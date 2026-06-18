# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall_monitor.build_data import build_data, default_fetchers
from recall_monitor.fetchers.base import FetchResult
from recall_monitor.fetchers.sample import SampleFetcher
from recall_monitor.model import RecallRecord


class BrokenFetcher:
    name = "broken"

    def fetch(self):
        raise RuntimeError("network unavailable")


class OneRecordFetcher:
    name = "one"

    def fetch(self):
        return FetchResult(
            source=self.name,
            records=[
                RecallRecord(
                    id="one-1",
                    source="ONE",
                    source_url="https://example.com/one-1",
                    region="US",
                    published_at="2026-06-18",
                    updated_at="2026-06-18",
                    title_original="Food recall",
                    title_zh="食品召回",
                    summary_zh="食品可能污染",
                    brand="Sample Food",
                    product="Snack",
                    model="Lot 1",
                    categories=[],
                    risks=[],
                    action="",
                    severity="unknown",
                    dedupe_key="",
                )
            ],
        )


class UnsafeUrlFetcher:
    name = "unsafe"

    def fetch(self):
        return FetchResult(
            source=self.name,
            records=[
                RecallRecord(
                    id="unsafe-1",
                    source="UNSAFE",
                    source_url="javascript:alert(1)",
                    region="GLOBAL",
                    published_at="2026-06-18",
                    updated_at="2026-06-18",
                    title_original="Unsafe URL recall",
                    title_zh="不安全链接召回",
                    summary_zh="用于验证链接过滤",
                    brand="",
                    product="",
                    model="",
                    categories=[],
                    risks=[],
                    action="",
                    severity="unknown",
                    dedupe_key="",
                )
            ],
        )


def test_build_data_writes_recalls_and_status(tmp_path):
    result = build_data([SampleFetcher()], tmp_path)

    recalls_path = tmp_path / "recalls.json"
    status_path = tmp_path / "status.json"
    recalls = json.loads(recalls_path.read_text(encoding="utf-8"))
    status = json.loads(status_path.read_text(encoding="utf-8"))

    assert result["recalls_path"] == recalls_path
    assert result["status_path"] == status_path
    assert "generated_at" in recalls
    assert "generated_at" in status
    assert "recalls" not in recalls
    assert len(recalls["records"]) == 2
    assert recalls["records"][0]["source"] == "SAMPLE"
    assert "published_at" in recalls["records"][0]
    assert "title_zh" in recalls["records"][0]
    assert "summary_zh" in recalls["records"][0]
    assert "dedupe_key" in recalls["records"][0]
    assert "raw" not in recalls["records"][0]
    assert status["sources"][0]["source"] == "SAMPLE"
    assert status["sources"][0]["ok"] is True
    assert status["sources"][0]["count"] == 2


def test_build_data_classifies_records_without_classifier_fields(tmp_path):
    build_data([OneRecordFetcher()], tmp_path)

    recalls = json.loads((tmp_path / "recalls.json").read_text(encoding="utf-8"))

    record = recalls["records"][0]
    assert record["categories"] == ["食品饮料"]
    assert record["risks"] == ["污染"]
    assert record["action"] == "查看召回公告并按官方指引处理。"
    assert record["dedupe_key"]


def test_build_data_strips_unsafe_source_urls(tmp_path):
    build_data([UnsafeUrlFetcher()], tmp_path)

    recalls = json.loads((tmp_path / "recalls.json").read_text(encoding="utf-8"))

    assert recalls["records"][0]["source_url"] == ""


def test_build_data_isolates_fetcher_exceptions(tmp_path):
    build_data([BrokenFetcher(), SampleFetcher()], tmp_path)

    recalls = json.loads((tmp_path / "recalls.json").read_text(encoding="utf-8"))
    status = json.loads((tmp_path / "status.json").read_text(encoding="utf-8"))

    assert len(recalls["records"]) == 2
    assert [source["source"] for source in status["sources"]] == ["broken", "SAMPLE"]
    assert status["sources"][0]["ok"] is False
    assert "network unavailable" in status["sources"][0]["error"]
    assert status["sources"][1]["ok"] is True


def test_default_fetchers_include_us_and_global_sources_and_offline_sample_only():
    online_names = [fetcher.name for fetcher in default_fetchers(offline_sample=False)]
    offline_names = [fetcher.name for fetcher in default_fetchers(offline_sample=True)]

    assert online_names == [
        "FDA Food",
        "FDA Drug",
        "FDA Device",
        "CPSC",
        "NHTSA",
        "USDA FSIS",
        "Canada Recalls",
        "China SAMR",
        "EU Safety Gate",
        "OECD GlobalRecalls",
        "sample",
    ]
    assert offline_names == ["sample"]
