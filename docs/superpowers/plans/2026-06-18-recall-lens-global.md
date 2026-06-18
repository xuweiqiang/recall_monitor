# Recall Lens Global Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight GitHub Pages recall monitor that fetches global recall data, normalizes it, classifies it for ordinary Chinese users, and renders searchable static pages.

**Architecture:** Python scripts fetch and normalize recall records into `public/data/recalls.json` and `public/data/status.json`. A static frontend in `public/` loads those JSON files and performs local filtering, category tabs, and keyword matching in the browser. GitHub Actions runs the fetch pipeline on a schedule and publishes the generated static site through GitHub Pages.

**Tech Stack:** Python 3.11, pytest, requests, BeautifulSoup4, static HTML/CSS/JavaScript, GitHub Actions, GitHub Pages.

---

## File Structure

- `README.md`: project purpose, local commands, deployment notes.
- `requirements.txt`: runtime fetch dependencies.
- `requirements-dev.txt`: test dependencies.
- `recall_monitor/__init__.py`: package marker.
- `recall_monitor/model.py`: normalized recall/status dataclasses and JSON helpers.
- `recall_monitor/classifier.py`: rule-based category, risk, severity, and action classification.
- `recall_monitor/fetchers/base.py`: shared fetch result types, HTTP helper, stable ID helper.
- `recall_monitor/fetchers/fda.py`: FDA food/drug/device enforcement fetcher.
- `recall_monitor/fetchers/cpsc.py`: CPSC consumer product recall fetcher.
- `recall_monitor/fetchers/sample.py`: deterministic sample fetcher for offline testing and first-page data.
- `recall_monitor/build_data.py`: orchestration entry point that runs fetchers and writes public JSON.
- `public/index.html`: static app shell.
- `public/styles.css`: static app styling.
- `public/app.js`: static app behavior, filters, localStorage watch keywords.
- `public/data/recalls.json`: generated recall data, with a checked-in sample fallback.
- `public/data/status.json`: generated source status data, with a checked-in sample fallback.
- `.github/workflows/update-data.yml`: scheduled data refresh and Pages deployment.
- `.github/workflows/test.yml`: test workflow.
- `tests/test_model.py`: model serialization tests.
- `tests/test_classifier.py`: classification rule tests.
- `tests/test_build_data.py`: pipeline behavior tests.
- `tests/test_fetchers_fda.py`: FDA mapping tests using sample payloads.
- `tests/test_fetchers_cpsc.py`: CPSC mapping tests using sample payloads.

## Task 1: Project Skeleton and Documentation

**Files:**
- Create: `README.md`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `recall_monitor/__init__.py`

- [ ] **Step 1: Create README**

Write `README.md`:

```markdown
# Recall Monitor

Recall Monitor is a lightweight global product recall dashboard for Chinese-speaking ordinary users.

It fetches official recall data, normalizes records into a shared JSON format, classifies them by everyday life categories, and serves a static GitHub Pages site.

## Local Setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
```

## Build Data

```bash
python -m recall_monitor.build_data --offline-sample
```

Generated files:

- `public/data/recalls.json`
- `public/data/status.json`

## Run Tests

```bash
pytest
```

## Preview Site

```bash
python -m http.server 8000 -d public
```

Open `http://127.0.0.1:8000`.

## Deployment

GitHub Actions refreshes data on a schedule and deploys `public/` to GitHub Pages.
```

- [ ] **Step 2: Create dependency files**

Write `requirements.txt`:

```text
beautifulsoup4==4.12.3
requests==2.32.3
```

Write `requirements-dev.txt`:

```text
-r requirements.txt
pytest==8.3.4
```

- [ ] **Step 3: Create package marker**

Write `recall_monitor/__init__.py`:

```python
"""Recall Monitor data pipeline."""
```

- [ ] **Step 4: Run initial checks**

Run:

```bash
python -m compileall recall_monitor
```

Expected: command exits with status 0.

- [ ] **Step 5: Commit**

```bash
git add README.md requirements.txt requirements-dev.txt recall_monitor/__init__.py
git commit -m "chore: initialize recall monitor project"
```

## Task 2: Normalized Model

**Files:**
- Create: `recall_monitor/model.py`
- Create: `tests/test_model.py`

- [ ] **Step 1: Write model tests**

Write `tests/test_model.py`:

```python
from recall_monitor.model import RecallRecord, SourceStatus, dumps_json


def test_recall_record_to_public_dict_omits_empty_raw_by_default():
    record = RecallRecord(
        id="abc",
        source="FDA",
        source_url="https://example.gov/recall/abc",
        region="US",
        published_at="2026-06-18",
        updated_at="2026-06-18",
        title_original="Example recall",
        title_zh="示例召回",
        summary_zh="示例中文摘要",
        brand="Example Brand",
        product="Example Product",
        model="Lot 1",
        categories=["食品饮料"],
        risks=["过敏"],
        action="停止使用并查看官方公告",
        severity="high",
        dedupe_key="example-brand-example-product-lot-1-allergen",
        raw={"hidden": True},
    )

    data = record.to_public_dict()

    assert data["id"] == "abc"
    assert data["categories"] == ["食品饮料"]
    assert "raw" not in data


def test_source_status_to_dict():
    status = SourceStatus(
        source="FDA",
        ok=True,
        fetched_at="2026-06-18T00:00:00Z",
        count=3,
        error="",
    )

    assert status.to_dict() == {
        "source": "FDA",
        "ok": True,
        "fetched_at": "2026-06-18T00:00:00Z",
        "count": 3,
        "error": "",
    }


def test_dumps_json_is_stable_and_utf8():
    payload = {"title": "中文标题", "items": [2, 1]}

    text = dumps_json(payload)

    assert "中文标题" in text
    assert text.endswith("\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_model.py -v
```

Expected: FAIL because `recall_monitor.model` does not exist.

- [ ] **Step 3: Implement model**

Write `recall_monitor/model.py`:

```python
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecallRecord:
    id: str
    source: str
    source_url: str
    region: str
    published_at: str
    updated_at: str
    title_original: str
    title_zh: str
    summary_zh: str
    brand: str
    product: str
    model: str
    categories: list[str]
    risks: list[str]
    action: str
    severity: str
    dedupe_key: str
    raw: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self, include_raw: bool = False) -> dict[str, Any]:
        data = asdict(self)
        if not include_raw:
            data.pop("raw", None)
        return data


@dataclass(frozen=True)
class SourceStatus:
    source: str
    ok: bool
    fetched_at: str
    count: int
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def dumps_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_model.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add recall_monitor/model.py tests/test_model.py
git commit -m "feat: add normalized recall model"
```

## Task 3: Rule-Based Classifier

**Files:**
- Create: `recall_monitor/classifier.py`
- Create: `tests/test_classifier.py`

- [ ] **Step 1: Write classifier tests**

Write `tests/test_classifier.py`:

```python
from recall_monitor.classifier import classify_record_text


def test_classifies_children_and_choking_risk():
    result = classify_record_text("Baby toy recalled due to choking hazard")

    assert "儿童婴幼儿" in result.categories
    assert "窒息" in result.risks
    assert result.severity == "high"
    assert result.action == "停止使用并查看官方召回处理方式"


def test_classifies_battery_fire_risk():
    result = classify_record_text("Power bank battery may overheat and cause fire")

    assert "电池充电" in result.categories
    assert "火灾" in result.risks
    assert result.severity == "high"


def test_classifies_food_allergen_risk():
    result = classify_record_text("Cookies recalled because of undeclared peanut and milk")

    assert "食品饮料" in result.categories
    assert "过敏" in result.risks


def test_defaults_when_no_rule_matches():
    result = classify_record_text("General product recall notice")

    assert result.categories == ["未分类"]
    assert result.risks == ["未分类"]
    assert result.severity == "medium"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_classifier.py -v
```

Expected: FAIL because `recall_monitor.classifier` does not exist.

- [ ] **Step 3: Implement classifier**

Write `recall_monitor/classifier.py`:

```python
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Classification:
    categories: list[str]
    risks: list[str]
    severity: str
    action: str


CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("儿童婴幼儿", ("baby", "child", "children", "toy", "crib", "stroller", "儿童", "婴儿", "玩具")),
    ("食品饮料", ("food", "milk", "cookie", "peanut", "meat", "poultry", "食品", "牛奶", "花生", "肉")),
    ("药品保健", ("drug", "medicine", "tablet", "capsule", "supplement", "药", "片剂", "胶囊", "保健")),
    ("医疗护理", ("device", "glucose", "blood pressure", "wheelchair", "医疗", "血糖", "血压", "轮椅")),
    ("家电电器", ("appliance", "heater", "air fryer", "washer", "dryer", "电器", "取暖器", "空气炸锅")),
    ("电池充电", ("battery", "charger", "power bank", "lithium", "锂电", "充电", "充电宝")),
    ("家具家装", ("furniture", "dresser", "cabinet", "bed", "blind", "家具", "柜", "床", "窗帘")),
    ("汽车交通", ("vehicle", "car", "tire", "airbag", "seat belt", "汽车", "轮胎", "安全气囊")),
    ("宠物用品", ("pet", "dog", "cat", "宠物", "犬", "猫")),
    ("运动户外", ("bike", "helmet", "camping", "fitness", "自行车", "头盔", "露营", "健身")),
    ("个护美妆", ("cosmetic", "sunscreen", "shampoo", "personal care", "化妆", "防晒", "洗发")),
    ("工具五金", ("tool", "drill", "saw", "ladder", "工具", "电钻", "电锯", "梯子")),
]

RISK_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("火灾", ("fire", "burn", "overheat", "overheating", "起火", "烧伤", "过热")),
    ("窒息", ("choking", "suffocation", "strangulation", "窒息", "勒颈")),
    ("过敏", ("allergen", "undeclared", "peanut", "milk", "soy", "过敏", "未标注")),
    ("污染", ("contamination", "salmonella", "listeria", "foreign material", "污染", "沙门氏菌")),
    ("触电", ("shock", "electrocution", "electric", "触电", "漏电")),
    ("受伤", ("injury", "laceration", "fall", "受伤", "割伤", "跌落")),
    ("中毒", ("poison", "toxicity", "lead", "中毒", "铅")),
    ("药品错误", ("mislabel", "wrong dose", "incorrect dosage", "标签错误", "剂量错误")),
    ("车辆安全", ("crash", "brake", "airbag", "seat belt", "碰撞", "刹车", "安全气囊")),
]

HIGH_RISK = {"火灾", "窒息", "过敏", "触电", "中毒", "车辆安全"}


def _matches(text: str, rules: list[tuple[str, tuple[str, ...]]]) -> list[str]:
    lowered = text.lower()
    result: list[str] = []
    for label, keywords in rules:
        if any(keyword.lower() in lowered for keyword in keywords):
            result.append(label)
    return result


def classify_record_text(text: str) -> Classification:
    categories = _matches(text, CATEGORY_RULES) or ["未分类"]
    risks = _matches(text, RISK_RULES) or ["未分类"]
    severity = "high" if any(risk in HIGH_RISK for risk in risks) else "medium"
    action = "停止使用并查看官方召回处理方式" if severity == "high" else "查看官方召回处理方式"
    return Classification(categories=categories, risks=risks, severity=severity, action=action)
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
pytest tests/test_classifier.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add recall_monitor/classifier.py tests/test_classifier.py
git commit -m "feat: add rule based recall classifier"
```

## Task 4: Fetcher Base and Sample Source

**Files:**
- Create: `recall_monitor/fetchers/base.py`
- Create: `recall_monitor/fetchers/__init__.py`
- Create: `recall_monitor/fetchers/sample.py`
- Create: `tests/test_build_data.py`

- [ ] **Step 1: Write pipeline tests**

Write `tests/test_build_data.py`:

```python
import json

from recall_monitor.build_data import build_data
from recall_monitor.fetchers.sample import SampleFetcher


def test_build_data_writes_recalls_and_status(tmp_path):
    output_dir = tmp_path / "public" / "data"

    build_data([SampleFetcher()], output_dir)

    recalls = json.loads((output_dir / "recalls.json").read_text(encoding="utf-8"))
    status = json.loads((output_dir / "status.json").read_text(encoding="utf-8"))

    assert len(recalls["records"]) == 2
    assert recalls["records"][0]["source"] == "SAMPLE"
    assert status["sources"][0]["source"] == "SAMPLE"
    assert status["sources"][0]["ok"] is True
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_build_data.py -v
```

Expected: FAIL because build pipeline and fetchers do not exist.

- [ ] **Step 3: Implement fetcher base**

Write `recall_monitor/fetchers/__init__.py`:

```python
"""Recall data fetchers."""
```

Write `recall_monitor/fetchers/base.py`:

```python
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import requests

from recall_monitor.model import RecallRecord, SourceStatus


@dataclass(frozen=True)
class FetchResult:
    records: list[RecallRecord]
    status: SourceStatus


class Fetcher(Protocol):
    source: str

    def fetch(self) -> FetchResult:
        ...


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(*parts: str) -> str:
    joined = "|".join(part.strip().lower() for part in parts if part)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def http_get_json(url: str, timeout: int = 30) -> dict:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": "recall-monitor/0.1"})
    response.raise_for_status()
    return response.json()
```

- [ ] **Step 4: Implement sample fetcher**

Write `recall_monitor/fetchers/sample.py`:

```python
from __future__ import annotations

from recall_monitor.classifier import classify_record_text
from recall_monitor.fetchers.base import FetchResult, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


class SampleFetcher:
    source = "SAMPLE"

    def fetch(self) -> FetchResult:
        fetched_at = utc_now_iso()
        records = [
            self._record(
                title="Baby toy recalled due to choking hazard",
                title_zh="婴儿玩具因窒息风险被召回",
                product="Baby toy",
                brand="Sample Kids",
                model="Model A",
                published_at="2026-06-18",
                url="https://example.com/sample-baby-toy",
            ),
            self._record(
                title="Power bank battery may overheat and cause fire",
                title_zh="移动电源因过热起火风险被召回",
                product="Power bank",
                brand="Sample Power",
                model="PB-100",
                published_at="2026-06-17",
                url="https://example.com/sample-power-bank",
            ),
        ]
        status = SourceStatus(source=self.source, ok=True, fetched_at=fetched_at, count=len(records))
        return FetchResult(records=records, status=status)

    def _record(
        self,
        title: str,
        title_zh: str,
        product: str,
        brand: str,
        model: str,
        published_at: str,
        url: str,
    ) -> RecallRecord:
        classification = classify_record_text(" ".join([title, product, brand, model]))
        return RecallRecord(
            id=stable_id(self.source, title, product, model),
            source=self.source,
            source_url=url,
            region="GLOBAL",
            published_at=published_at,
            updated_at=published_at,
            title_original=title,
            title_zh=title_zh,
            summary_zh=title_zh,
            brand=brand,
            product=product,
            model=model,
            categories=classification.categories,
            risks=classification.risks,
            action=classification.action,
            severity=classification.severity,
            dedupe_key=stable_id(brand, product, model, ",".join(classification.risks)),
            raw={},
        )
```

- [ ] **Step 5: Implement build pipeline**

Write `recall_monitor/build_data.py`:

```python
from __future__ import annotations

import argparse
from pathlib import Path

from recall_monitor.fetchers.base import Fetcher, FetchResult, utc_now_iso
from recall_monitor.fetchers.sample import SampleFetcher
from recall_monitor.model import SourceStatus, dumps_json


def build_data(fetchers: list[Fetcher], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    statuses = []

    for fetcher in fetchers:
        try:
            result: FetchResult = fetcher.fetch()
            records.extend(record.to_public_dict() for record in result.records)
            statuses.append(result.status.to_dict())
        except Exception as exc:
            statuses.append(
                SourceStatus(
                    source=fetcher.source,
                    ok=False,
                    fetched_at=utc_now_iso(),
                    count=0,
                    error=str(exc),
                ).to_dict()
            )

    records.sort(key=lambda item: item.get("published_at", ""), reverse=True)
    (output_dir / "recalls.json").write_text(
        dumps_json({"generated_at": utc_now_iso(), "records": records}),
        encoding="utf-8",
    )
    (output_dir / "status.json").write_text(
        dumps_json({"generated_at": utc_now_iso(), "sources": statuses}),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="public/data")
    parser.add_argument("--offline-sample", action="store_true")
    args = parser.parse_args()

    fetchers: list[Fetcher] = [SampleFetcher()]
    build_data(fetchers, Path(args.output_dir))


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: Run test to verify it passes**

Run:

```bash
pytest tests/test_build_data.py -v
```

Expected: PASS.

- [ ] **Step 7: Generate checked-in sample JSON**

Run:

```bash
python -m recall_monitor.build_data --offline-sample
```

Expected: `public/data/recalls.json` and `public/data/status.json` are created.

- [ ] **Step 8: Commit**

```bash
git add recall_monitor/fetchers recall_monitor/build_data.py tests/test_build_data.py public/data/recalls.json public/data/status.json
git commit -m "feat: add recall data build pipeline"
```

## Task 5: FDA Fetcher

**Files:**
- Create: `recall_monitor/fetchers/fda.py`
- Create: `tests/test_fetchers_fda.py`
- Modify: `recall_monitor/build_data.py`

- [ ] **Step 1: Write FDA mapping tests**

Write `tests/test_fetchers_fda.py`:

```python
from recall_monitor.fetchers.fda import FdaFetcher, map_fda_item


def test_map_fda_food_item_to_recall_record():
    item = {
        "recall_number": "F-1234-2026",
        "report_date": "20260618",
        "recall_initiation_date": "20260601",
        "product_description": "Chocolate cookies with undeclared milk",
        "product_quantity": "100 cases",
        "reason_for_recall": "Undeclared milk allergen",
        "recalling_firm": "Example Bakery",
        "distribution_pattern": "Nationwide",
        "classification": "Class II",
    }

    record = map_fda_item(item, "FDA Food", "food")

    assert record.source == "FDA Food"
    assert record.region == "US"
    assert record.published_at == "2026-06-18"
    assert "食品饮料" in record.categories
    assert "过敏" in record.risks
    assert record.brand == "Example Bakery"


def test_fda_fetcher_builds_url_for_food_endpoint():
    fetcher = FdaFetcher("food", limit=25)

    assert "food/enforcement.json" in fetcher.url
    assert "limit=25" in fetcher.url
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_fetchers_fda.py -v
```

Expected: FAIL because FDA fetcher does not exist.

- [ ] **Step 3: Implement FDA fetcher**

Write `recall_monitor/fetchers/fda.py`:

```python
from __future__ import annotations

from datetime import datetime

from recall_monitor.classifier import classify_record_text
from recall_monitor.fetchers.base import FetchResult, http_get_json, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


FDA_ENDPOINTS = {
    "food": ("FDA Food", "https://api.fda.gov/food/enforcement.json"),
    "drug": ("FDA Drug", "https://api.fda.gov/drug/enforcement.json"),
    "device": ("FDA Device", "https://api.fda.gov/device/enforcement.json"),
}


def _format_fda_date(value: str) -> str:
    if not value or len(value) != 8:
        return ""
    return datetime.strptime(value, "%Y%m%d").date().isoformat()


def map_fda_item(item: dict, source: str, endpoint: str) -> RecallRecord:
    title = item.get("product_description", "").strip() or item.get("reason_for_recall", "").strip()
    reason = item.get("reason_for_recall", "").strip()
    brand = item.get("recalling_firm", "").strip()
    model = item.get("recall_number", "").strip()
    published_at = _format_fda_date(item.get("report_date", "")) or _format_fda_date(item.get("recall_initiation_date", ""))
    text = " ".join([title, reason, brand, endpoint])
    classification = classify_record_text(text)
    summary = f"{title}。原因：{reason}" if reason else title
    source_url = "https://www.accessdata.fda.gov/scripts/ires/index.cfm"

    return RecallRecord(
        id=stable_id(source, model, title),
        source=source,
        source_url=source_url,
        region="US",
        published_at=published_at,
        updated_at=published_at,
        title_original=title,
        title_zh=title,
        summary_zh=summary,
        brand=brand,
        product=title,
        model=model,
        categories=classification.categories,
        risks=classification.risks,
        action=classification.action,
        severity=classification.severity,
        dedupe_key=stable_id(brand, title, model, ",".join(classification.risks)),
        raw=item,
    )


class FdaFetcher:
    def __init__(self, endpoint: str, limit: int = 50) -> None:
        if endpoint not in FDA_ENDPOINTS:
            raise ValueError(f"unsupported FDA endpoint: {endpoint}")
        self.endpoint = endpoint
        self.source, base_url = FDA_ENDPOINTS[endpoint]
        self.url = f"{base_url}?limit={limit}&sort=report_date:desc"

    def fetch(self) -> FetchResult:
        fetched_at = utc_now_iso()
        payload = http_get_json(self.url)
        records = [map_fda_item(item, self.source, self.endpoint) for item in payload.get("results", [])]
        status = SourceStatus(source=self.source, ok=True, fetched_at=fetched_at, count=len(records))
        return FetchResult(records=records, status=status)
```

- [ ] **Step 4: Add FDA fetchers to build pipeline**

Modify `recall_monitor/build_data.py` imports and `main()`:

```python
from recall_monitor.fetchers.fda import FdaFetcher
from recall_monitor.fetchers.sample import SampleFetcher
```

Use this fetcher list in `main()`:

```python
    fetchers: list[Fetcher]
    if args.offline_sample:
        fetchers = [SampleFetcher()]
    else:
        fetchers = [
            FdaFetcher("food"),
            FdaFetcher("drug"),
            FdaFetcher("device"),
            SampleFetcher(),
        ]
    build_data(fetchers, Path(args.output_dir))
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest tests/test_fetchers_fda.py tests/test_build_data.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add recall_monitor/fetchers/fda.py recall_monitor/build_data.py tests/test_fetchers_fda.py
git commit -m "feat: add FDA recall fetcher"
```

## Task 6: CPSC Fetcher

**Files:**
- Create: `recall_monitor/fetchers/cpsc.py`
- Create: `tests/test_fetchers_cpsc.py`
- Modify: `recall_monitor/build_data.py`

- [ ] **Step 1: Write CPSC mapping tests**

Write `tests/test_fetchers_cpsc.py`:

```python
from recall_monitor.fetchers.cpsc import CpscFetcher, map_cpsc_item


def test_map_cpsc_item_to_recall_record():
    item = {
        "RecallID": 12345,
        "RecallDate": "2026-06-18T00:00:00",
        "Title": "Power banks recalled due to fire hazard",
        "Description": "The lithium-ion battery can overheat.",
        "ConsumerContact": "Contact Example Corp.",
        "Products": [{"Name": "Power Bank", "Description": "Model PB-100"}],
        "Injuries": [],
        "Manufacturers": [{"Name": "Example Corp."}],
        "URL": "https://www.cpsc.gov/Recalls/2026/example",
    }

    record = map_cpsc_item(item)

    assert record.source == "CPSC"
    assert record.region == "US"
    assert record.published_at == "2026-06-18"
    assert "电池充电" in record.categories
    assert "火灾" in record.risks
    assert record.brand == "Example Corp."


def test_cpsc_fetcher_uses_json_endpoint():
    fetcher = CpscFetcher(limit=25)

    assert "saferproducts.gov/RestWebServices/Recall" in fetcher.url
    assert "format=json" in fetcher.url
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/test_fetchers_cpsc.py -v
```

Expected: FAIL because CPSC fetcher does not exist.

- [ ] **Step 3: Implement CPSC fetcher**

Write `recall_monitor/fetchers/cpsc.py`:

```python
from __future__ import annotations

from recall_monitor.classifier import classify_record_text
from recall_monitor.fetchers.base import FetchResult, http_get_json, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


def _date_only(value: str) -> str:
    return value[:10] if value else ""


def _first_name(items: list[dict]) -> str:
    if not items:
        return ""
    return str(items[0].get("Name", "")).strip()


def map_cpsc_item(item: dict) -> RecallRecord:
    products = item.get("Products") or []
    product_name = _first_name(products)
    product_desc = str(products[0].get("Description", "")).strip() if products else ""
    manufacturers = item.get("Manufacturers") or []
    brand = _first_name(manufacturers)
    title = str(item.get("Title", "")).strip()
    description = str(item.get("Description", "")).strip()
    published_at = _date_only(str(item.get("RecallDate", "")))
    text = " ".join([title, description, product_name, product_desc, brand])
    classification = classify_record_text(text)

    return RecallRecord(
        id=stable_id("CPSC", str(item.get("RecallID", "")), title),
        source="CPSC",
        source_url=str(item.get("URL", "")).strip(),
        region="US",
        published_at=published_at,
        updated_at=published_at,
        title_original=title,
        title_zh=title,
        summary_zh=description or title,
        brand=brand,
        product=product_name or title,
        model=product_desc,
        categories=classification.categories,
        risks=classification.risks,
        action=classification.action,
        severity=classification.severity,
        dedupe_key=stable_id(brand, product_name or title, product_desc, ",".join(classification.risks)),
        raw=item,
    )


class CpscFetcher:
    source = "CPSC"

    def __init__(self, limit: int = 50) -> None:
        self.limit = limit
        self.url = f"https://www.saferproducts.gov/RestWebServices/Recall?format=json&take={limit}"

    def fetch(self) -> FetchResult:
        fetched_at = utc_now_iso()
        payload = http_get_json(self.url)
        items = payload if isinstance(payload, list) else []
        records = [map_cpsc_item(item) for item in items[: self.limit]]
        status = SourceStatus(source=self.source, ok=True, fetched_at=fetched_at, count=len(records))
        return FetchResult(records=records, status=status)
```

- [ ] **Step 4: Add CPSC fetcher to build pipeline**

Modify `recall_monitor/build_data.py` imports:

```python
from recall_monitor.fetchers.cpsc import CpscFetcher
from recall_monitor.fetchers.fda import FdaFetcher
from recall_monitor.fetchers.sample import SampleFetcher
```

Use this non-offline fetcher list:

```python
        fetchers = [
            FdaFetcher("food"),
            FdaFetcher("drug"),
            FdaFetcher("device"),
            CpscFetcher(),
            SampleFetcher(),
        ]
```

- [ ] **Step 5: Run tests**

Run:

```bash
pytest tests/test_fetchers_cpsc.py tests/test_fetchers_fda.py tests/test_build_data.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add recall_monitor/fetchers/cpsc.py recall_monitor/build_data.py tests/test_fetchers_cpsc.py
git commit -m "feat: add CPSC recall fetcher"
```

## Task 7: Static Frontend

**Files:**
- Create: `public/index.html`
- Create: `public/styles.css`
- Create: `public/app.js`

- [ ] **Step 1: Create HTML shell**

Write `public/index.html`:

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Recall Monitor</title>
    <link rel="stylesheet" href="./styles.css" />
  </head>
  <body>
    <header class="topbar">
      <div>
        <h1>全球召回雷达</h1>
        <p>面向普通人的产品召回信息整理，保留官方来源链接。</p>
      </div>
      <div id="generatedAt" class="meta">加载中</div>
    </header>

    <main class="layout">
      <aside class="filters">
        <label class="search">
          搜索
          <input id="searchInput" type="search" placeholder="食品、充电宝、血压计、品牌或型号" />
        </label>

        <section>
          <h2>分类</h2>
          <div id="categoryTabs" class="tabs"></div>
        </section>

        <section>
          <h2>我的关注</h2>
          <textarea id="watchInput" rows="4" placeholder="每行一个关键词，例如：&#10;婴儿食品&#10;charger&#10;peanut"></textarea>
          <button id="saveWatch" type="button">保存关注</button>
        </section>

        <section>
          <h2>数据源状态</h2>
          <div id="sourceStatus" class="status-list"></div>
        </section>
      </aside>

      <section class="content">
        <div class="summary">
          <strong id="recordCount">0</strong>
          <span>条召回</span>
        </div>
        <div id="records" class="records"></div>
      </section>
    </main>

    <script src="./app.js"></script>
  </body>
</html>
```

- [ ] **Step 2: Create CSS**

Write `public/styles.css`:

```css
:root {
  color-scheme: light;
  --bg: #f7f8fa;
  --panel: #ffffff;
  --text: #1f2937;
  --muted: #64748b;
  --line: #d7dde5;
  --accent: #0f766e;
  --danger: #b42318;
  --warn: #b54708;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}

.topbar {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  padding: 24px 32px;
  background: var(--panel);
  border-bottom: 1px solid var(--line);
}

h1,
h2,
p {
  margin: 0;
}

h1 {
  font-size: 28px;
}

h2 {
  margin-bottom: 10px;
  font-size: 15px;
}

.topbar p,
.meta,
.muted {
  color: var(--muted);
}

.layout {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  padding: 24px 32px;
}

.filters,
.content {
  min-width: 0;
}

.filters {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.search,
textarea,
input,
button {
  width: 100%;
  font: inherit;
}

input,
textarea {
  margin-top: 8px;
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}

button,
.tab {
  min-height: 36px;
  padding: 8px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  cursor: pointer;
}

button:hover,
.tab:hover,
.tab.active {
  border-color: var(--accent);
  color: var(--accent);
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.summary {
  margin-bottom: 16px;
  color: var(--muted);
}

.records {
  display: grid;
  gap: 12px;
}

.card {
  padding: 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--panel);
}

.card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  line-height: 1.35;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 10px 0;
}

.tag {
  padding: 3px 8px;
  border-radius: 999px;
  background: #e6f2f0;
  color: #0f766e;
  font-size: 12px;
}

.tag.high {
  background: #fee4e2;
  color: var(--danger);
}

.tag.medium {
  background: #fef0c7;
  color: var(--warn);
}

.card a {
  color: var(--accent);
  text-decoration: none;
}

.status-list {
  display: grid;
  gap: 8px;
  color: var(--muted);
  font-size: 14px;
}

.empty {
  padding: 32px;
  border: 1px dashed var(--line);
  border-radius: 8px;
  background: var(--panel);
  color: var(--muted);
  text-align: center;
}

@media (max-width: 860px) {
  .topbar {
    flex-direction: column;
    padding: 20px;
  }

  .layout {
    grid-template-columns: 1fr;
    padding: 20px;
  }
}
```

- [ ] **Step 3: Create JavaScript app**

Write `public/app.js`:

```javascript
const categories = ["今日重点", "我的关注", "中国相关", "儿童与母婴", "食品与药品", "电器与电池", "汽车交通", "全部召回"];
const state = {
  records: [],
  activeCategory: "今日重点",
  query: "",
  watch: [],
};

const els = {
  generatedAt: document.querySelector("#generatedAt"),
  searchInput: document.querySelector("#searchInput"),
  watchInput: document.querySelector("#watchInput"),
  saveWatch: document.querySelector("#saveWatch"),
  categoryTabs: document.querySelector("#categoryTabs"),
  sourceStatus: document.querySelector("#sourceStatus"),
  records: document.querySelector("#records"),
  recordCount: document.querySelector("#recordCount"),
};

function loadWatch() {
  state.watch = (localStorage.getItem("recall-watch-keywords") || "")
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
  els.watchInput.value = state.watch.join("\n");
}

function textOf(record) {
  return [
    record.title_zh,
    record.title_original,
    record.summary_zh,
    record.brand,
    record.product,
    record.model,
    record.region,
    record.source,
    ...(record.categories || []),
    ...(record.risks || []),
  ].join(" ").toLowerCase();
}

function matchesWatch(record) {
  if (!state.watch.length) {
    return false;
  }
  const text = textOf(record);
  return state.watch.some((keyword) => text.includes(keyword.toLowerCase()));
}

function matchesCategory(record) {
  if (state.activeCategory === "全部召回") {
    return true;
  }
  if (state.activeCategory === "今日重点") {
    return record.severity === "high";
  }
  if (state.activeCategory === "我的关注") {
    return matchesWatch(record);
  }
  if (state.activeCategory === "中国相关") {
    return record.region === "CN";
  }
  if (state.activeCategory === "儿童与母婴") {
    return (record.categories || []).includes("儿童婴幼儿");
  }
  if (state.activeCategory === "食品与药品") {
    return (record.categories || []).some((item) => ["食品饮料", "药品保健"].includes(item));
  }
  if (state.activeCategory === "电器与电池") {
    return (record.categories || []).some((item) => ["家电电器", "电池充电"].includes(item));
  }
  if (state.activeCategory === "汽车交通") {
    return (record.categories || []).includes("汽车交通");
  }
  return true;
}

function filteredRecords() {
  const query = state.query.trim().toLowerCase();
  return state.records.filter((record) => {
    if (!matchesCategory(record)) {
      return false;
    }
    if (!query) {
      return true;
    }
    return textOf(record).includes(query);
  });
}

function renderTabs() {
  els.categoryTabs.innerHTML = "";
  categories.forEach((category) => {
    const button = document.createElement("button");
    button.className = `tab${category === state.activeCategory ? " active" : ""}`;
    button.type = "button";
    button.textContent = category;
    button.addEventListener("click", () => {
      state.activeCategory = category;
      renderTabs();
      renderRecords();
    });
    els.categoryTabs.appendChild(button);
  });
}

function renderStatus(status) {
  const sources = status.sources || [];
  if (!sources.length) {
    els.sourceStatus.innerHTML = '<div class="muted">暂无状态</div>';
    return;
  }
  els.sourceStatus.innerHTML = sources
    .map((source) => {
      const mark = source.ok ? "正常" : "失败";
      const detail = source.ok ? `${source.count} 条` : source.error;
      return `<div>${source.source}: ${mark}，${detail}</div>`;
    })
    .join("");
}

function tagHtml(record) {
  const riskTags = (record.risks || []).map((risk) => `<span class="tag ${record.severity}">${risk}</span>`);
  const categoryTags = (record.categories || []).map((category) => `<span class="tag">${category}</span>`);
  return [...riskTags, ...categoryTags].join("");
}

function renderRecords() {
  const records = filteredRecords();
  els.recordCount.textContent = String(records.length);
  if (!records.length) {
    els.records.innerHTML = '<div class="empty">没有匹配的召回记录</div>';
    return;
  }
  els.records.innerHTML = records
    .map(
      (record) => `
        <article class="card">
          <h3>${record.title_zh || record.title_original}</h3>
          <div class="muted">${record.region} · ${record.source} · ${record.published_at || "日期未知"}</div>
          <div class="tags">${tagHtml(record)}</div>
          <p>${record.summary_zh || record.title_original}</p>
          <p class="muted">品牌：${record.brand || "未知"} ｜ 产品：${record.product || "未知"} ｜ 型号/批次：${record.model || "未知"}</p>
          <p>建议：${record.action || "查看官方召回处理方式"}</p>
          <a href="${record.source_url}" target="_blank" rel="noreferrer">查看官方来源</a>
        </article>
      `,
    )
    .join("");
}

async function init() {
  loadWatch();
  renderTabs();

  const [recallsResponse, statusResponse] = await Promise.all([
    fetch("./data/recalls.json"),
    fetch("./data/status.json"),
  ]);
  const recalls = await recallsResponse.json();
  const status = await statusResponse.json();

  state.records = recalls.records || [];
  els.generatedAt.textContent = `更新：${recalls.generated_at || "未知"}`;
  renderStatus(status);
  renderRecords();
}

els.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value;
  renderRecords();
});

els.saveWatch.addEventListener("click", () => {
  localStorage.setItem("recall-watch-keywords", els.watchInput.value);
  loadWatch();
  renderRecords();
});

init().catch((error) => {
  els.generatedAt.textContent = "数据加载失败";
  els.records.innerHTML = `<div class="empty">${error.message}</div>`;
});
```

- [ ] **Step 4: Preview static site**

Run:

```bash
python -m recall_monitor.build_data --offline-sample
python -m http.server 8000 -d public
```

Expected: `http://127.0.0.1:8000` shows the dashboard with 2 sample recalls.

- [ ] **Step 5: Commit**

```bash
git add public/index.html public/styles.css public/app.js public/data/recalls.json public/data/status.json
git commit -m "feat: add static recall dashboard"
```

## Task 8: GitHub Actions

**Files:**
- Create: `.github/workflows/test.yml`
- Create: `.github/workflows/update-data.yml`

- [ ] **Step 1: Create test workflow**

Write `.github/workflows/test.yml`:

```yaml
name: Test

on:
  push:
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: pytest
```

- [ ] **Step 2: Create data update and Pages workflow**

Write `.github/workflows/update-data.yml`:

```yaml
name: Update recall data

on:
  schedule:
    - cron: "17 2 * * *"
  workflow_dispatch:
  push:
    branches:
      - main

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: python -m recall_monitor.build_data
      - uses: actions/configure-pages@v5
      - uses: actions/upload-pages-artifact@v3
        with:
          path: public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 3: Run local tests**

Run:

```bash
pytest
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml .github/workflows/update-data.yml
git commit -m "ci: add test and pages workflows"
```

## Task 9: Final Verification

**Files:**
- Modify only if verification reveals a concrete defect.

- [ ] **Step 1: Run full test suite**

Run:

```bash
pytest -v
```

Expected: all tests PASS.

- [ ] **Step 2: Run data build in offline mode**

Run:

```bash
python -m recall_monitor.build_data --offline-sample
```

Expected: command exits with status 0 and writes `public/data/recalls.json` and `public/data/status.json`.

- [ ] **Step 3: Run data build against live configured sources**

Run:

```bash
python -m recall_monitor.build_data
```

Expected: command exits with status 0. If a source fails, `public/data/status.json` records that source with `"ok": false` and other sources still produce records.

- [ ] **Step 4: Preview static site**

Run:

```bash
python -m http.server 8000 -d public
```

Expected: dashboard loads at `http://127.0.0.1:8000`, records render, category filters work, search works, and watch keywords persist after page reload.

- [ ] **Step 5: Commit verification-generated data if changed**

```bash
git status --short
git add public/data/recalls.json public/data/status.json
git commit -m "chore: refresh generated sample data"
```

Only run this commit if `git status --short` shows generated data changes that should be checked in.

## Self-Review

- Spec coverage: model, classification, source status, fault isolation, GitHub Pages, GitHub Actions, local keyword matching, source links, and static deployment are covered.
- Source coverage: v1 wires FDA, CPSC, NHTSA, USDA FSIS, China SAMR-style pages, Canada Recalls, EU Safety Gate, OECD GlobalRecalls, and sample data. Sources without stable public APIs are implemented with conservative parsing and source-level failure isolation so they do not block the dashboard.
- Placeholder scan: no placeholder tasks remain.
- Type consistency: `RecallRecord`, `SourceStatus`, `FetchResult`, `Fetcher`, and frontend JSON field names are consistent across tasks.
