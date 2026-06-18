# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from recall_monitor.fetchers.base import FetchResult, http_get_json, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


CANADA_OPEN_DATA_URL = (
    "https://recalls-rappels.canada.ca/sites/default/files/"
    "opendata-donneesouvertes/HCRSAMOpenData.json"
)


class CanadaFetcher(object):
    name = "Canada Recalls"

    def __init__(self, limit=50, url=CANADA_OPEN_DATA_URL, json_getter=None):
        self.limit = limit
        self.url = url
        self._json_getter = json_getter or http_get_json

    def fetch(self):
        payload = self._json_getter(self.url)
        records = parse_canada_payload(payload, self.limit)
        result = FetchResult(source=self.name, records=records)
        result.status = SourceStatus(self.name, True, utc_now_iso(), len(records))
        return result


def parse_canada_payload(payload, limit=50):
    rows = payload
    if isinstance(payload, dict):
        rows = payload.get("results") or payload.get("records") or payload.get("data") or []
    return [map_canada_item(item) for item in list(rows)[:limit]]


def map_canada_item(item):
    recall_id = _text(item.get("NID")) or stable_id("Canada Recalls", item.get("Title"), item.get("URL"))
    title = _text(item.get("Title"))
    url = _text(item.get("URL"))
    updated = _text(item.get("Last updated") or item.get("Date"))
    product = _text(item.get("Product"))
    organization = _text(item.get("Organization"))
    issue = _text(item.get("Issue"))
    action = _text(item.get("What you should do"))
    category = _text(item.get("Category"))
    recall_class = _text(item.get("Recall class"))
    summary = _join_nonempty([issue, action])

    return RecallRecord(
        id=recall_id,
        source="Canada Recalls",
        source_url=url,
        region="CA",
        published_at=updated,
        updated_at=updated,
        title_original=title,
        title_zh=title,
        summary_zh=summary,
        brand=organization,
        product=product,
        model="",
        categories=[category] if category else [],
        risks=[issue] if issue else [],
        action=action,
        severity=recall_class or "unknown",
        dedupe_key=stable_id("Canada Recalls", organization, product, title),
        raw=dict(item),
    )


def _join_nonempty(parts):
    return " ".join(part for part in parts if part)


def _text(value):
    if value is None:
        return ""
    try:
        return unicode(value).strip()
    except NameError:
        return str(value).strip()
