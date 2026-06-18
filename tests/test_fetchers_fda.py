from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.fetchers.fda import FdaFetcher, map_fda_item


def test_map_fda_food_item_uses_enforcement_fields():
    item = {
        "product_description": "Peanut butter cups, 12 oz",
        "reason_for_recall": "Undeclared peanuts",
        "recalling_firm": "Sample Foods LLC",
        "recall_number": "F-1234-2026",
        "report_date": "20260610",
        "recall_initiation_date": "20260601",
    }

    record = map_fda_item(item, "food")

    assert record.id
    assert record.source == "FDA Food"
    assert record.region == "US"
    assert record.published_at == "2026-06-10"
    assert record.updated_at == "2026-06-01"
    assert record.title_original == "Peanut butter cups, 12 oz"
    assert record.brand == "Sample Foods LLC"
    assert record.product == "Peanut butter cups, 12 oz"
    assert record.model == "F-1234-2026"
    assert "Undeclared peanuts" in record.summary_zh
    assert record.raw == item


def test_fda_fetcher_builds_openfda_url_and_maps_results(monkeypatch):
    captured = []

    def fake_get_json(url):
        captured.append(url)
        return {
            "results": [
                {
                    "product_description": "Infusion pump",
                    "reason_for_recall": "Software failure",
                    "recalling_firm": "Device Co",
                    "recall_number": "Z-0001-2026",
                    "report_date": "2026-06-11",
                }
            ]
        }

    monkeypatch.setattr("recall_monitor.fetchers.fda.http_get_json", fake_get_json)

    result = FdaFetcher("device", limit=7).fetch()

    assert captured == [
        "https://api.fda.gov/device/enforcement.json?limit=7&sort=report_date:desc"
    ]
    assert result.source == "FDA Device"
    assert result.status.source == "FDA Device"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].source == "FDA Device"
