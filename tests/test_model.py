import json
from pathlib import Path
import sys
from dataclasses import is_dataclass

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.model import RecallRecord, SourceStatus, dumps_json


def test_recall_record_public_dict_omits_raw_by_default():
    record = RecallRecord(
        id="abc123",
        source="SAMPLE",
        source_url="https://example.com/recalls/abc123",
        region="US",
        published_at="2026-06-18",
        updated_at="2026-06-18",
        title_original="Infant rattle recalled for choking risk",
        title_zh="婴儿摇铃因窒息风险被召回",
        summary_zh="小零件可能脱落。",
        brand="Sample Kids",
        product="Infant rattle",
        model="IR-1",
        categories=["儿童婴幼儿"],
        risks=["窒息"],
        action="Stop using the product and contact the seller.",
        severity="high",
        dedupe_key="sample-kids-infant-rattle-ir-1-choking",
        raw={"internal": "source-only"},
    )

    payload = record.to_public_dict()

    assert is_dataclass(record)
    assert payload["id"] == "abc123"
    assert payload["source"] == "SAMPLE"
    assert payload["region"] == "US"
    assert payload["published_at"] == "2026-06-18"
    assert payload["updated_at"] == "2026-06-18"
    assert payload["title_original"] == "Infant rattle recalled for choking risk"
    assert payload["title_zh"] == "婴儿摇铃因窒息风险被召回"
    assert payload["summary_zh"] == "小零件可能脱落。"
    assert payload["brand"] == "Sample Kids"
    assert payload["product"] == "Infant rattle"
    assert payload["model"] == "IR-1"
    assert payload["categories"] == ["儿童婴幼儿"]
    assert payload["risks"] == ["窒息"]
    assert payload["action"] == "Stop using the product and contact the seller."
    assert payload["severity"] == "high"
    assert payload["dedupe_key"] == "sample-kids-infant-rattle-ir-1-choking"
    assert "raw" not in payload


def test_recall_record_public_dict_can_include_raw():
    record = RecallRecord(
        id="abc123",
        source="SAMPLE",
        source_url="https://example.com/recalls/abc123",
        region="US",
        published_at="2026-06-18",
        updated_at="2026-06-18",
        title_original="Infant rattle recalled",
        title_zh="婴儿摇铃召回",
        summary_zh="小零件可能脱落。",
        brand="Sample Kids",
        product="Infant rattle",
        model="IR-1",
        categories=["儿童婴幼儿"],
        risks=["窒息"],
        action="Stop using the product.",
        severity="high",
        dedupe_key="sample-kids-infant-rattle-ir-1-choking",
        raw={"internal": "source-only"},
    )

    assert record.to_public_dict(include_raw=True)["raw"] == {"internal": "source-only"}


def test_dumps_json_is_stable_utf8_pretty_json():
    payload = {"name": "婴儿玩具", "items": [2, 1]}

    dumped = dumps_json(payload)

    assert dumped.endswith("\n")
    assert "婴儿玩具" in dumped
    assert json.loads(dumped) == payload


def test_source_status_public_dict():
    status = SourceStatus(
        source="SAMPLE",
        ok=True,
        fetched_at="2026-06-18T00:00:00Z",
        count=2,
    )

    assert is_dataclass(status)
    assert status.to_dict() == {
        "source": "SAMPLE",
        "ok": True,
        "fetched_at": "2026-06-18T00:00:00Z",
        "count": 2,
        "error": None,
    }
    assert status.to_public_dict() == status.to_dict()
