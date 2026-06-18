# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser
try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

import requests

from recall_monitor.fetchers.base import FetchResult, sanitize_url, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


EU_SAFETY_GATE_URL = (
    "https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/"
    "healthref-europe-rapex-en/records?limit={limit}&order_by=alert_date%20desc"
)
EU_SAFETY_GATE_WEB_URL = "https://ec.europa.eu/safety-gate-alerts/screen/webReport"


class EuSafetyGateFetcher(object):
    name = "EU Safety Gate"

    def __init__(self, limit=50, url=EU_SAFETY_GATE_URL, html_getter=None, json_getter=None):
        self.limit = limit
        self.url = url
        self._html_getter = html_getter or _http_get_text
        self._json_getter = json_getter or _http_get_json

    def fetch(self):
        if "{limit}" in self.url:
            payload = self._json_getter(self.url.format(limit=self.limit))
            records = [map_eu_item(item) for item in _items(payload)[: self.limit]]
        else:
            html = self._html_getter(self.url)
            records = parse_eu_html(html, self.url, self.limit)
        if not records:
            raise RuntimeError("EU Safety Gate returned no records")
        result = FetchResult(source=self.name, records=records)
        result.status = SourceStatus(self.name, True, utc_now_iso(), len(records))
        return result


def parse_eu_html(html, base_url, limit=50):
    records = []
    seen = set()
    for href, title in _extract_links(html):
        if not title or not href or not _looks_like_alert(title, href):
            continue
        url = sanitize_url(urljoin(base_url, href))
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        records.append(map_eu_item({"title": title, "url": url}))
        if len(records) >= limit:
            break
    return records


def _extract_links(html):
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        parser = _LinkParser()
        parser.feed(html or "")
        return parser.links

    soup = BeautifulSoup(html or "", "html.parser")
    return [
        ((link.get("href") or "").strip(), link.get_text(" ", strip=True))
        for link in soup.find_all("a")
    ]


def map_eu_item(item):
    title = _text(item.get("title")) or _join_nonempty(
        [_text(item.get("product_type")), _text(item.get("product_name"))]
    )
    url = _text(item.get("url")) or _text(item.get("rapex_url"))
    date = _text(item.get("date")) or _text(item.get("alert_date"))
    category = _text(item.get("category")) or _text(item.get("product_category"))
    risk = _first_text(item.get("risk")) or _first_text(item.get("alert_type"))
    brand = _text(item.get("brand")) or _text(item.get("product_brand"))
    product = _text(item.get("product")) or _text(item.get("product_name"))
    model = _text(item.get("model")) or _text(item.get("product_model_type")) or _text(item.get("product_batch_number"))
    country = _text(item.get("country")) or _text(item.get("alert_country"))
    alert_number = _text(item.get("alert_number"))
    description = _text(item.get("alert_description"))
    action = _first_text(item.get("measures_country"))

    return RecallRecord(
        id=alert_number or stable_id("EU Safety Gate", title, url),
        source="EU Safety Gate",
        source_url=url,
        region="EU",
        published_at=date,
        updated_at=date,
        title_original=title,
        title_zh=title,
        summary_zh=_join_nonempty([country, product, risk, description]) or title,
        brand=brand,
        product=product,
        model=model,
        categories=[category] if category else [],
        risks=[risk] if risk else [],
        action=action,
        severity="unknown",
        dedupe_key=stable_id("EU Safety Gate", brand, product, model, title),
        raw=dict(item),
    )


def _http_get_text(url, timeout=20.0):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def _http_get_json(url, timeout=20.0):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _items(payload):
    if isinstance(payload, dict):
        return payload.get("results") or []
    return []


def _looks_like_alert(title, href):
    haystack = (title + " " + href).lower()
    return "alert" in haystack or "safety-gate" in haystack or "webreport" in haystack


def _join_nonempty(parts):
    return " ".join(part for part in parts if part)


def _text(value):
    if value is None:
        return ""
    try:
        return unicode(value).strip()
    except NameError:
        return str(value).strip()


def _first_text(value):
    if isinstance(value, list):
        for item in value:
            text = _text(item)
            if text:
                return text
        return ""
    return _text(value)


class _LinkParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.links = []
        self._href = None
        self._text_parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self._href = dict(attrs).get("href", "")
            self._text_parts = []

    def handle_data(self, data):
        if self._href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href is not None:
            self.links.append((self._href.strip(), " ".join(self._text_parts).strip()))
            self._href = None
            self._text_parts = []
