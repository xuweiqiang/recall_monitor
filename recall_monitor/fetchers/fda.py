# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from recall_monitor.fetchers.base import FetchResult, http_get_json, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


FDA_SOURCES = {
    "food": "FDA Food",
    "drug": "FDA Drug",
    "device": "FDA Device",
}


class FdaFetcher(object):
    def __init__(self, endpoint, limit=50):
        if endpoint not in FDA_SOURCES:
            raise ValueError("unsupported FDA endpoint: %s" % endpoint)
        self.endpoint = endpoint
        self.limit = limit
        self.name = FDA_SOURCES[endpoint]

    def fetch(self):
        url = (
            "https://api.fda.gov/%s/enforcement.json?limit=%s&sort=report_date:desc"
            % (self.endpoint, self.limit)
        )
        payload = http_get_json(url)
        records = [map_fda_item(item, self.endpoint) for item in payload.get("results", [])]
        return _fetch_result(self.name, records)


def map_fda_item(item, endpoint):
    source = FDA_SOURCES[endpoint]
    product = _text(item.get("product_description"))
    reason = _text(item.get("reason_for_recall"))
    firm = _text(item.get("recalling_firm"))
    recall_number = _text(item.get("recall_number"))
    report_date = _date(item.get("report_date"))
    initiation_date = _date(item.get("recall_initiation_date")) or report_date
    title = product or ("%s recall %s" % (source, recall_number)).strip()

    return RecallRecord(
        id=stable_id(source, recall_number, product, report_date),
        source=source,
        source_url="https://open.fda.gov/apis/enforcement/",
        region="US",
        published_at=report_date,
        updated_at=initiation_date,
        title_original=title,
        title_zh=title,
        summary_zh=reason,
        brand=firm,
        product=product,
        model=recall_number,
        dedupe_key=stable_id(source, firm, product, recall_number),
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


def _date(value):
    text = _text(value)
    if not text:
        return ""
    if len(text) == 8 and text.isdigit():
        return "%s-%s-%s" % (text[0:4], text[4:6], text[6:8])
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
