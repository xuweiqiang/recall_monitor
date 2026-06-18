# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from recall_monitor.fetchers.base import FetchResult, http_get_json, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


REPRESENTATIVE_MODELS = [
    ("Honda", "Accord", "2020"),
    ("Toyota", "Camry", "2020"),
    ("Ford", "F-150", "2020"),
]


class NhtsaFetcher(object):
    name = "NHTSA"

    def __init__(self, limit=50, vehicles=None):
        self.limit = limit
        self.vehicles = vehicles or list(REPRESENTATIVE_MODELS)

    def fetch(self):
        records = []
        seen = set()
        for make, model, year in self.vehicles:
            try:
                payload = http_get_json(_vehicle_url(make, model, year))
            except Exception:
                continue
            for item in payload.get("results", []):
                campaign = _text(item.get("NHTSACampaignNumber"))
                key = campaign or stable_id(item)
                if key in seen:
                    continue
                seen.add(key)
                records.append(map_nhtsa_item(item))
                if len(records) >= self.limit:
                    return _fetch_result(self.name, records)
        return _fetch_result(self.name, records)


def map_nhtsa_item(item):
    campaign = _text(item.get("NHTSACampaignNumber"))
    report_date = _date(item.get("ReportReceivedDate"))
    manufacturer = _text(item.get("Manufacturer"))
    component = _text(item.get("Component"))
    summary = _text(item.get("Summary"))
    remedy = _text(item.get("Remedy"))
    notes = _text(item.get("Notes"))
    title = " ".join(part for part in [manufacturer, component, "recall", campaign] if part)
    summary_text = " ".join(part for part in [summary, remedy, notes] if part)

    return RecallRecord(
        id=stable_id("NHTSA", campaign, manufacturer, component),
        source="NHTSA",
        source_url="https://www.nhtsa.gov/recalls",
        region="US",
        published_at=report_date,
        updated_at=report_date,
        title_original=title,
        title_zh=title,
        summary_zh=summary_text,
        brand=manufacturer,
        product=component,
        model=campaign,
        dedupe_key=stable_id("NHTSA", manufacturer, component, campaign),
        raw=item,
    )


def _vehicle_url(make, model, year):
    return (
        "https://api.nhtsa.gov/recalls/recallsByVehicle?make=%s&model=%s&modelYear=%s"
        % (make, model, year)
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
    if len(text) >= 10 and text[4:5] == "-" and text[7:8] == "-":
        return text[:10]
    parts = text.split("/")
    if len(parts) == 3:
        day, month, year = parts
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
