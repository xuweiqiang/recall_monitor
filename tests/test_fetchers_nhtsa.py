from io import BytesIO
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.fetchers.nhtsa import NhtsaFetcher, map_nhtsa_item, parse_nhtsa_flat_rows


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


def test_nhtsa_fetcher_reads_general_flat_file(monkeypatch):
    captured = []
    rows = (
        "81716\t10E054000\tJL AUDIO\tHD750/1\t9999\t\tEQUIPMENT\tJL AUDIO, INC.\t\t\tE\t5900\t"
        "20101203\tMFR\tJL AUDIO, INC.\t20101122\t20101130\t\t\t"
        "Amplifier can overheat.\tThis can produce smoke and possibly fire.\tRepair.\tNotes\tRCL1\t\t\t\tN\tY\n"
    )
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("FLAT_RCL_POST_2010.txt", rows)

    def fake_get_binary(url):
        captured.append(url)
        return buffer.getvalue()

    monkeypatch.setattr("recall_monitor.fetchers.nhtsa._http_get_binary", fake_get_binary)

    result = NhtsaFetcher(limit=5).fetch()

    assert captured == ["https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip"]
    assert result.source == "NHTSA"
    assert result.status.ok is True
    assert result.status.count == 1
    assert len(result.records) == 1
    assert result.records[0].model == "10E054000"


def test_parse_nhtsa_flat_rows_maps_general_recall_dataset():
    rows = (
        "81716\t10E054000\tJL AUDIO\tHD750/1\t9999\t\tEQUIPMENT\tJL AUDIO, INC.\t\t\tE\t5900\t"
        "20101203\tMFR\tJL AUDIO, INC.\t20101122\t20101130\t\t\t"
        "Amplifier can overheat.\tThis can produce smoke and possibly fire.\tRepair free of charge.\tNotes\tRCL1\t\t\t\tN\tY\n"
    )

    records = parse_nhtsa_flat_rows(rows, limit=5)

    assert len(records) == 1
    assert records[0].source == "NHTSA"
    assert records[0].region == "US"
    assert records[0].published_at == "2010-11-22"
    assert records[0].brand == "JL AUDIO, INC."
    assert records[0].product == "JL AUDIO HD750/1 EQUIPMENT"
    assert records[0].model == "10E054000"
    assert "Amplifier can overheat." in records[0].summary_zh
    assert records[0].source_url == "https://www.nhtsa.gov/recalls"


def test_nhtsa_fetcher_raises_when_flat_file_fails(monkeypatch):
    def fake_get_json(url):
        raise RuntimeError("nhtsa unavailable")

    monkeypatch.setattr("recall_monitor.fetchers.nhtsa._http_get_binary", fake_get_json)

    try:
        NhtsaFetcher(limit=5).fetch()
    except RuntimeError as exc:
        assert "NHTSA flat file request failed" in str(exc)
    else:
        raise AssertionError("expected NHTSA failure")
