from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.fetchers.cpsc import CpscFetcher, map_cpsc_item


def test_map_cpsc_item_uses_recall_products_and_manufacturers():
    item = {
        "RecallID": 26123,
        "RecallDate": "2026-06-12T00:00:00",
        "Title": "Children's helmets recalled due to head injury hazard",
        "Description": "The helmets can fail to protect users.",
        "Products": [{"Name": "Youth Bike Helmet", "Model": "YH-100"}],
        "Manufacturers": [{"Name": "Helmet Maker Inc."}],
        "URL": "https://www.cpsc.gov/Recalls/2026/sample",
    }

    record = map_cpsc_item(item)

    assert record.id
    assert record.source == "CPSC"
    assert record.source_url == "https://www.cpsc.gov/Recalls/2026/sample"
    assert record.region == "US"
    assert record.published_at == "2026-06-12"
    assert record.updated_at == "2026-06-12"
    assert record.title_original == "Children's helmets recalled due to head injury hazard"
    assert "The helmets can fail" in record.summary_zh
    assert record.brand == "Helmet Maker Inc."
    assert record.product == "Youth Bike Helmet"
    assert record.model == "YH-100"
    assert record.raw == item


def test_cpsc_fetcher_builds_url_and_maps_results(monkeypatch):
    captured = []

    def fake_get_json(url):
        captured.append(url)
        return [
            {
                "RecallID": "R1",
                "RecallDate": "2026-06-12",
                "Title": "Power bank recalled",
                "Description": "Fire hazard",
                "Products": [{"Name": "Power Bank"}],
                "Manufacturers": [{"Name": "Battery Co"}],
                "URL": "https://www.cpsc.gov/recalls/r1",
            }
        ]

    monkeypatch.setattr("recall_monitor.fetchers.cpsc.http_get_json", fake_get_json)

    result = CpscFetcher(limit=3).fetch()

    assert captured == [
        "https://www.saferproducts.gov/RestWebServices/Recall?format=json&take=3"
    ]
    assert result.source == "CPSC"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].brand == "Battery Co"
