from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.fetchers.usda import UsdaFetcher, map_usda_item


def test_map_usda_item_supports_fsis_field_variants():
    item = {
        "field_title": "Ready-to-eat chicken recalled",
        "title": "Fallback title",
        "field_recall_date": "2026-06-13",
        "field_summary": "Product may be contaminated with Listeria.",
        "field_establishment": "Sample Poultry Co.",
        "field_product_items": "Ready-to-eat chicken salad",
        "field_recall_reason": "Listeria contamination",
        "field_recall_url": "https://www.fsis.usda.gov/recalls/sample",
    }

    record = map_usda_item(item)

    assert record.id
    assert record.source == "USDA FSIS"
    assert record.source_url == "https://www.fsis.usda.gov/recalls/sample"
    assert record.region == "US"
    assert record.published_at == "2026-06-13"
    assert record.updated_at == "2026-06-13"
    assert record.title_original == "Ready-to-eat chicken recalled"
    assert "Product may be contaminated" in record.summary_zh
    assert "Listeria contamination" in record.summary_zh
    assert record.brand == "Sample Poultry Co."
    assert record.product == "Ready-to-eat chicken salad"
    assert record.raw == item


def test_map_usda_item_supports_plain_test_sample_fields():
    item = {
        "title": "Beef product recall",
        "product": "Ground beef",
        "url": "https://www.fsis.usda.gov/recalls/beef",
        "recall_date": "06/14/2026",
        "reason": "E. coli",
        "problem": "May be contaminated",
        "company": "Beef Co",
    }

    record = map_usda_item(item)

    assert record.title_original == "Beef product recall"
    assert record.source_url == "https://www.fsis.usda.gov/recalls/beef"
    assert record.published_at == "2026-06-14"
    assert record.brand == "Beef Co"
    assert record.product == "Ground beef"
    assert "E. coli" in record.summary_zh
    assert "May be contaminated" in record.summary_zh


def test_usda_fetcher_builds_url_and_maps_result_collections(monkeypatch):
    captured = []

    def fake_get_json(url):
        captured.append(url)
        return {
            "results": [
                {
                    "title": "Pork recall",
                    "product": "Pork sausage",
                    "recall_date": "2026-06-15",
                    "company": "Pork Co",
                    "reason": "Misbranding",
                }
            ]
        }

    monkeypatch.setattr("recall_monitor.fetchers.usda.http_get_json", fake_get_json)

    result = UsdaFetcher(limit=4).fetch()

    assert captured == [
        "https://www.fsis.usda.gov/fsis/api/recall/v/1?field_recall_date_value=&field_states_id=All&items_per_page=4"
    ]
    assert result.source == "USDA FSIS"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].brand == "Pork Co"
