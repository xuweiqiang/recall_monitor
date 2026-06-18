# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import requests

from recall_monitor.fetchers.base import FetchResult, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; recall-monitor/0.1; +https://github.com/xuweiqiang/recall_monitor)"
}


class CpscFetcher(object):
    name = "CPSC"

    def __init__(self, limit=50):
        self.limit = limit
        self.headers = dict(DEFAULT_HEADERS)

    def fetch(self):
        url = (
            "https://www.saferproducts.gov/RestWebServices/Recall?format=json&take=%s"
            % self.limit
        )
        payload = http_get_json(url)
        records = [map_cpsc_item(item) for item in _items(payload)[: self.limit]]
        return _fetch_result(self.name, records)


def http_get_json(url, timeout=20.0):
    response = requests.get(url, timeout=timeout, headers=DEFAULT_HEADERS)
    response.raise_for_status()
    return response.json()


def map_cpsc_item(item):
    recall_id = _text(item.get("RecallID"))
    recall_date = _date(item.get("RecallDate"))
    title = _text(item.get("Title"))
    description = _text(item.get("Description"))
    products = item.get("Products") or []
    manufacturers = item.get("Manufacturers") or []
    product = _first_field(products, ("Name", "Description", "ProductName"))
    model = _first_field(products, ("Model", "ModelNumber"))
    brand = _first_field(manufacturers, ("Name", "CompanyName"))
    source_url = _text(item.get("URL"))

    return RecallRecord(
        id=stable_id("CPSC", recall_id, title),
        source="CPSC",
        source_url=source_url,
        region="US",
        published_at=recall_date,
        updated_at=recall_date,
        title_original=title,
        title_zh=title,
        summary_zh=description,
        brand=brand,
        product=product,
        model=model or recall_id,
        dedupe_key=stable_id("CPSC", brand, product, model or recall_id),
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
        return payload.get("results") or payload.get("Recalls") or payload.get("recalls") or []
    return []


def _first_field(items, names):
    for item in items:
        if isinstance(item, dict):
            for name in names:
                value = _text(item.get(name))
                if value:
                    return value
        else:
            value = _text(item)
            if value:
                return value
    return ""


def _date(value):
    text = _text(value)
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    return text


def _text(value):
    if value is None:
        return ""
    try:
        return unicode(value).strip()
    except NameError:
        return str(value).strip()
