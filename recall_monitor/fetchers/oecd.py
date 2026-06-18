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


OECD_GLOBAL_RECALLS_URL = "https://globalrecalls.oecd.org/"


class OecdFetcher(object):
    name = "OECD GlobalRecalls"

    def __init__(self, limit=50, url=OECD_GLOBAL_RECALLS_URL, html_getter=None):
        self.limit = limit
        self.url = url
        self._html_getter = html_getter or _http_get_text

    def fetch(self):
        html = self._html_getter(self.url)
        records = parse_oecd_html(html, self.url, self.limit)
        if not records:
            raise RuntimeError("OECD GlobalRecalls returned no records")
        result = FetchResult(source=self.name, records=records)
        result.status = SourceStatus(self.name, True, utc_now_iso(), len(records))
        return result


def parse_oecd_html(html, base_url, limit=50):
    records = []
    seen = set()
    for href, title in _extract_links(html):
        if not title or not href or not _looks_like_recall(title, href):
            continue
        url = sanitize_url(urljoin(base_url, href))
        if not url:
            continue
        if url in seen:
            continue
        seen.add(url)
        records.append(map_oecd_item({"title": title, "url": url}))
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


def map_oecd_item(item):
    title = _text(item.get("title"))
    url = _text(item.get("url"))
    date = _text(item.get("date"))
    country = _text(item.get("country"))
    category = _text(item.get("category"))
    risk = _text(item.get("risk"))
    product = _text(item.get("product"))
    brand = _text(item.get("brand"))
    model = _text(item.get("model"))

    return RecallRecord(
        id=_text(item.get("id")) or stable_id("OECD GlobalRecalls", title, url),
        source="OECD GlobalRecalls",
        source_url=url,
        region="GLOBAL",
        published_at=date,
        updated_at=date,
        title_original=title,
        title_zh=title,
        summary_zh=_join_nonempty([country, product, risk]) or title,
        brand=brand,
        product=product,
        model=model,
        categories=[category] if category else [],
        risks=[risk] if risk else [],
        action="",
        severity="unknown",
        dedupe_key=stable_id("OECD GlobalRecalls", country, brand, product, model),
        raw=dict(item),
    )


def _http_get_text(url, timeout=20.0):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.text


def _looks_like_recall(title, href):
    haystack = (title + " " + href).lower()
    return "recall" in haystack


def _join_nonempty(parts):
    return " ".join(part for part in parts if part)


def _text(value):
    if value is None:
        return ""
    try:
        return unicode(value).strip()
    except NameError:
        return str(value).strip()


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
