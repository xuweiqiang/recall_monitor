# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall_monitor.fetchers.oecd import (
    OECD_GLOBAL_RECALLS_URL,
    OecdFetcher,
    map_oecd_item,
    parse_oecd_html,
)


def test_map_oecd_item_maps_local_sample_fields():
    item = {
        "id": "OECD-123",
        "title": "Blender recalled for laceration risk",
        "url": "https://globalrecalls.oecd.org/recall/123",
        "date": "2026-04-20",
        "country": "Australia",
        "category": "Household appliances",
        "risk": "Laceration",
        "product": "Blender",
        "brand": "BlendCo",
        "model": "BC-2",
    }

    record = map_oecd_item(item)

    assert record.id == "OECD-123"
    assert record.source == "OECD GlobalRecalls"
    assert record.source_url == item["url"]
    assert record.region == "GLOBAL"
    assert record.published_at == "2026-04-20"
    assert record.updated_at == "2026-04-20"
    assert record.title_original == item["title"]
    assert record.brand == "BlendCo"
    assert record.product == "Blender"
    assert record.model == "BC-2"
    assert record.categories == ["Household appliances"]
    assert record.risks == ["Laceration"]
    assert record.raw == item


def test_parse_oecd_html_extracts_recall_links():
    html = """
    <html><body>
      <a href="/recall/123">Blender recall</a>
      <a href="/contact">Contact</a>
    </body></html>
    """

    records = parse_oecd_html(html, base_url="https://globalrecalls.oecd.org", limit=5)

    assert len(records) == 1
    assert records[0].source_url == "https://globalrecalls.oecd.org/recall/123"
    assert records[0].region == "GLOBAL"


def test_parse_oecd_html_drops_unsafe_link_schemes():
    html = '<a href="data:text/html,<script>alert(1)</script>">Unsafe recall</a>'

    records = parse_oecd_html(html, base_url="https://globalrecalls.oecd.org", limit=5)

    assert records == []


def test_oecd_fetcher_default_url_is_configurable():
    fetcher = OecdFetcher(limit=6, url="https://example.org")

    assert fetcher.url == "https://example.org"
    assert fetcher.limit == 6
    assert OECD_GLOBAL_RECALLS_URL == "https://globalrecalls.oecd.org/"


def test_oecd_fetcher_fetch_uses_injected_html_getter():
    fetcher = OecdFetcher(
        limit=2,
        html_getter=lambda url: '<a href="/recall/123">Blender recall</a>',
    )

    result = fetcher.fetch()

    assert result.source == "OECD GlobalRecalls"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].source_url == "https://globalrecalls.oecd.org/recall/123"
