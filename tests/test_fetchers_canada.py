# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall_monitor.fetchers.canada import (
    CANADA_OPEN_DATA_URL,
    CanadaFetcher,
    map_canada_item,
    parse_canada_payload,
)


def test_map_canada_item_maps_official_json_fields():
    item = {
        "NID": "ra-123",
        "Title": "Portable heater recalled due to fire hazard",
        "URL": "https://recalls-rappels.canada.ca/en/alert-recall/portable-heater",
        "Organization": "Health Canada",
        "Product": "Portable heater",
        "Issue": "The product can overheat and create a fire hazard.",
        "What you should do": "Stop using the product and contact the company.",
        "Category": "Consumer products",
        "Recall class": "Class 2",
        "Last updated": "2026-06-10",
    }

    record = map_canada_item(item)

    assert record.id == "ra-123"
    assert record.source == "Canada Recalls"
    assert record.source_url == item["URL"]
    assert record.region == "CA"
    assert record.published_at == "2026-06-10"
    assert record.updated_at == "2026-06-10"
    assert record.title_original == item["Title"]
    assert record.brand == "Health Canada"
    assert record.product == "Portable heater"
    assert record.categories == ["Consumer products"]
    assert record.risks == ["The product can overheat and create a fire hazard."]
    assert record.action == item["What you should do"]
    assert record.severity == "Class 2"
    assert record.raw == item


def test_parse_canada_payload_respects_limit():
    payload = [
        {"NID": "1", "Title": "First", "URL": "https://example.com/1"},
        {"NID": "2", "Title": "Second", "URL": "https://example.com/2"},
    ]

    records = parse_canada_payload(payload, limit=1)

    assert [record.id for record in records] == ["1"]


def test_canada_fetcher_uses_official_open_data_url():
    fetcher = CanadaFetcher(limit=7)

    assert fetcher.url == CANADA_OPEN_DATA_URL
    assert fetcher.limit == 7


def test_canada_fetcher_fetch_uses_injected_json_getter():
    fetcher = CanadaFetcher(
        limit=2,
        json_getter=lambda url: [
            {"NID": "1", "Title": "First", "URL": "https://example.com/1"}
        ],
    )

    result = fetcher.fetch()

    assert result.source == "Canada Recalls"
    assert result.status.source == "Canada Recalls"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].id == "1"
