# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import BytesIO
import zipfile

import requests

from recall_monitor.fetchers.base import FetchResult, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


NHTSA_FLAT_RECALLS_URL = "https://static.nhtsa.gov/odi/ffdd/rcl/FLAT_RCL_POST_2010.zip"


class NhtsaFetcher(object):
    name = "NHTSA"

    def __init__(self, limit=50, url=NHTSA_FLAT_RECALLS_URL):
        self.limit = limit
        self.url = url

    def fetch(self):
        try:
            zip_bytes = _http_get_binary(self.url)
            rows = _read_first_text_file(zip_bytes)
        except Exception as exc:
            raise RuntimeError("NHTSA flat file request failed: %s" % exc)

        records = parse_nhtsa_flat_rows(rows, self.limit)
        result = FetchResult(source=self.name, records=records)
        result.status = SourceStatus(self.name, True, utc_now_iso(), len(records))
        return result


def parse_nhtsa_flat_rows(rows, limit=50):
    records = []
    seen = set()
    for line in (rows or "").splitlines():
        if not line.strip():
            continue
        item = _flat_row_to_item(line)
        campaign = _text(item.get("NHTSACampaignNumber"))
        if campaign in seen:
            continue
        seen.add(campaign)
        records.append(map_nhtsa_item(item))
        if len(records) >= limit:
            break
    return records


def map_nhtsa_item(item):
    campaign = _text(item.get("NHTSACampaignNumber"))
    report_date = _date(item.get("ReportReceivedDate"))
    manufacturer = _text(item.get("Manufacturer"))
    make = _text(item.get("Make"))
    model_text = _text(item.get("VehicleModel"))
    year = _text(item.get("ModelYear"))
    if year == "9999":
        year = ""
    component = _text(item.get("Component"))
    summary = _text(item.get("Summary"))
    consequence = _text(item.get("Consequence"))
    remedy = _text(item.get("Remedy"))
    notes = _text(item.get("Notes"))
    product = " ".join(part for part in [make, model_text, year, component] if part)
    title = " ".join(part for part in [manufacturer, product, "recall", campaign] if part)
    summary_text = " ".join(part for part in [summary, consequence, remedy, notes] if part)

    return RecallRecord(
        id=stable_id("NHTSA", campaign, manufacturer, product),
        source="NHTSA",
        source_url="https://www.nhtsa.gov/recalls",
        region="US",
        published_at=report_date,
        updated_at=report_date,
        title_original=title,
        title_zh=title,
        summary_zh=summary_text,
        brand=manufacturer,
        product=product,
        model=campaign,
        dedupe_key=stable_id("NHTSA", manufacturer, product, campaign),
        raw=item,
    )


def _flat_row_to_item(line):
    fields = line.rstrip("\n").split("\t")
    fields += [""] * max(0, 29 - len(fields))
    return {
        "RecordID": fields[0],
        "NHTSACampaignNumber": fields[1],
        "Make": fields[2],
        "VehicleModel": fields[3],
        "ModelYear": fields[4],
        "ManufacturerCampaignNumber": fields[5],
        "Component": fields[6],
        "Manufacturer": fields[7],
        "RecallType": fields[10],
        "PotentialUnitsAffected": fields[11],
        "ReportReceivedDate": fields[15],
        "Summary": fields[19],
        "Consequence": fields[20],
        "Remedy": fields[21],
        "Notes": fields[22],
        "NhtsaComponentID": fields[23],
        "DoNotDrive": fields[27],
        "ParkOutside": fields[28],
    }


def _read_first_text_file(zip_bytes):
    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        for name in archive.namelist():
            if name.lower().endswith(".txt"):
                with archive.open(name) as handle:
                    return handle.read().decode("utf-8", "replace")
    raise RuntimeError("NHTSA zip did not contain a text file")


def _http_get_binary(url, timeout=30.0):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def _date(value):
    text = _text(value)
    if not text:
        return ""
    if len(text) == 8 and text.isdigit():
        return "%s-%s-%s" % (text[0:4], text[4:6], text[6:8])
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
