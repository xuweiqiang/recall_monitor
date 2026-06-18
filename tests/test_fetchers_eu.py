# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall_monitor.fetchers.eu import (
    EU_SAFETY_GATE_URL,
    EuSafetyGateFetcher,
    map_eu_item,
    parse_eu_html,
)


def test_map_eu_item_maps_local_sample_fields():
    item = {
        "alert_number": "A12/00123/26",
        "title": "Toy slime with chemical risk",
        "url": "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertDetail/100",
        "date": "2026-06-01",
        "category": "Toys",
        "risk": "Chemical",
        "brand": "SlimeCo",
        "product": "Toy slime",
        "model": "SL-1",
        "country": "France",
    }

    record = map_eu_item(item)

    assert record.id == "A12/00123/26"
    assert record.source == "EU Safety Gate"
    assert record.source_url == item["url"]
    assert record.region == "EU"
    assert record.published_at == "2026-06-01"
    assert record.updated_at == "2026-06-01"
    assert record.title_original == item["title"]
    assert record.brand == "SlimeCo"
    assert record.product == "Toy slime"
    assert record.model == "SL-1"
    assert record.categories == ["Toys"]
    assert record.risks == ["Chemical"]
    assert record.raw == item


def test_parse_eu_html_extracts_safety_gate_links():
    html = """
    <html><body>
      <a href="/safety-gate-alerts/screen/webReport/alertDetail/100">Alert A12/00123/26 Toy slime</a>
      <a href="/other">Other page</a>
    </body></html>
    """

    records = parse_eu_html(html, base_url="https://ec.europa.eu", limit=5)

    assert len(records) == 1
    assert records[0].source == "EU Safety Gate"
    assert records[0].source_url == "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertDetail/100"


def test_eu_fetcher_default_url_is_configurable():
    fetcher = EuSafetyGateFetcher(limit=4, url="https://example.eu/safety")

    assert fetcher.url == "https://example.eu/safety"
    assert fetcher.limit == 4
    assert EU_SAFETY_GATE_URL.startswith("https://")


def test_eu_fetcher_fetch_uses_injected_html_getter():
    fetcher = EuSafetyGateFetcher(
        limit=2,
        url="https://ec.europa.eu",
        html_getter=lambda url: '<a href="/safety-gate-alerts/screen/webReport/alertDetail/100">Alert Toy</a>',
    )

    result = fetcher.fetch()

    assert result.source == "EU Safety Gate"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].source_url == "https://ec.europa.eu/safety-gate-alerts/screen/webReport/alertDetail/100"
