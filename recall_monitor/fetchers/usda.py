# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from recall_monitor.fetchers.base import FetchResult, http_get_json, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


class UsdaFetcher(object):
    name = "USDA FSIS"

    def __init__(self, limit=50):
        self.limit = limit

    def fetch(self):
        url = (
            "https://www.fsis.usda.gov/fsis/api/recall/v/1?"
            "field_recall_date_value=&field_states_id=All&items_per_page=%s"
            % self.limit
        )
        payload = http_get_json(url)
        records = [map_usda_item(item) for item in _items(payload)]
        return _fetch_result(self.name, records)


def map_usda_item(item):
    title = _first(item, "field_title", "title")
    product = _first(item, "field_product_items", "product")
    source_url = _first(item, "field_recall_url", "url")
    recall_date = _date(_first(item, "field_recall_date", "recall_date"))
    reason = _first(item, "field_recall_reason", "reason")
    problem = _first(item, "field_summary", "problem")
    company = _first(item, "field_establishment", "company")
    summary = " ".join(part for part in [problem, reason] if part)

    return RecallRecord(
        id=stable_id("USDA FSIS", title, product, recall_date),
        source="USDA FSIS",
        source_url=source_url,
        region="US",
        published_at=recall_date,
        updated_at=recall_date,
        title_original=title,
        title_zh=title,
        summary_zh=summary,
        brand=company,
        product=product,
        model="",
        dedupe_key=stable_id("USDA FSIS", company, product, title),
        raw=item,
    )


def _fetch_result(source, records):
    result = FetchResult(source=source, records=records)
    result.status = SourceStatus(
        source=source,
        ok=True,
        fetched_at=utc_now_iso(),
        count=len(records),
    )
    return result


def _items(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        return payload.get("results") or payload.get("data") or payload.get("items") or []
    return []


def _first(item, *names):
    for name in names:
        value = _text(item.get(name))
        if value:
            return value
    return ""


def _date(value):
    text = _text(value)
    if not text:
        return ""
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    parts = text.split("/")
    if len(parts) == 3:
        month, day, year = parts
        if len(year) == 4:
            return "%s-%s-%s" % (year, month.zfill(2), day.zfill(2))
    return text


def _text(value):
    if value is None:
        return ""
    try:
        return unicode(value).strip()
    except NameError:
        return str(value).strip()
