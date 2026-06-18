from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.fetchers.nhtsa import NhtsaFetcher, map_nhtsa_item


def test_map_nhtsa_item_uses_vehicle_recall_fields():
    item = {
        "NHTSACampaignNumber": "26V123000",
        "ReportReceivedDate": "15/06/2026",
        "Manufacturer": "Sample Motors, LLC",
        "Component": "AIR BAGS",
        "Summary": "Air bags may deploy unexpectedly.",
        "Remedy": "Dealers will update the software.",
        "Notes": "Owners may contact customer service.",
    }

    record = map_nhtsa_item(item)

    assert record.id
    assert record.source == "NHTSA"
    assert record.region == "US"
    assert record.published_at == "2026-06-15"
    assert record.updated_at == "2026-06-15"
    assert record.title_original == "Sample Motors, LLC AIR BAGS recall 26V123000"
    assert "Air bags may deploy unexpectedly." in record.summary_zh
    assert "Dealers will update the software." in record.summary_zh
    assert "Owners may contact customer service." in record.summary_zh
    assert record.brand == "Sample Motors, LLC"
    assert record.product == "AIR BAGS"
    assert record.model == "26V123000"
    assert record.raw == item


def test_nhtsa_fetcher_queries_representative_models_and_deduplicates(monkeypatch):
    captured = []

    def fake_get_json(url):
        captured.append(url)
        if "make=honda&model=accord" in url.lower():
            return {
                "results": [
                    {
                        "NHTSACampaignNumber": "26V123000",
                        "ReportReceivedDate": "2026-06-15",
                        "Manufacturer": "Honda",
                        "Component": "SERVICE BRAKES",
                        "Summary": "Brake issue",
                        "Remedy": "Repair",
                        "Notes": "",
                    }
                ]
            }
        if "make=toyota&model=camry" in url.lower():
            return {
                "results": [
                    {
                        "NHTSACampaignNumber": "26V123000",
                        "ReportReceivedDate": "2026-06-15",
                        "Manufacturer": "Honda",
                        "Component": "SERVICE BRAKES",
                        "Summary": "Brake issue duplicate",
                        "Remedy": "Repair",
                        "Notes": "",
                    }
                ]
            }
        raise RuntimeError("single model failed")

    monkeypatch.setattr("recall_monitor.fetchers.nhtsa.http_get_json", fake_get_json)

    result = NhtsaFetcher(limit=5).fetch()

    assert captured == [
        "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Honda&model=Accord&modelYear=2020",
        "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Toyota&model=Camry&modelYear=2020",
        "https://api.nhtsa.gov/recalls/recallsByVehicle?make=Ford&model=F-150&modelYear=2020",
    ]
    assert result.source == "NHTSA"
    assert result.status.ok is True
    assert result.status.count == 1
    assert len(result.records) == 1
    assert result.records[0].model == "26V123000"
