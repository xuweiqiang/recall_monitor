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

import base64
import requests

from recall_monitor.fetchers.base import FetchResult, sanitize_url, stable_id, utc_now_iso
from recall_monitor.model import RecallRecord, SourceStatus


CHINA_SAMR_URL = "https://qxzh.samr.gov.cn/qxzh/qxxxcx/web.jsp"
CHINA_CAR_NEWS_URL = "https://qxzh.samr.gov.cn/qxzh/frame/car/siteNews"
CHINA_CONSUMER_NEWS_URL = "https://qxzh.samr.gov.cn/qxzh/frame/car/consumeNews"
CHINA_REFERER = "https://qxzh.samr.gov.cn/qxzh/qxxxcx/web.jsp"


class ChinaFetcher(object):
    name = "China SAMR"

    def __init__(self, limit=50, url=CHINA_SAMR_URL, html_getter=None, json_getter=None):
        self.limit = limit
        self.url = url
        self._html_getter = html_getter or _http_get_text
        self._json_getter = json_getter or _http_post_json

    def fetch(self):
        if self.url == CHINA_SAMR_URL:
            records = self._fetch_json_records()
        else:
            html = self._html_getter(self.url)
            records = parse_china_html(html, self.url, self.limit)
        result = FetchResult(source=self.name, records=records)
        result.status = SourceStatus(self.name, True, utc_now_iso(), len(records))
        return result

    def _fetch_json_records(self):
        page_size = max(1, min(self.limit, 50))
        records = []
        sources = [
            (CHINA_CAR_NEWS_URL, "汽车"),
            (CHINA_CONSUMER_NEWS_URL, "消费品"),
        ]
        for url, category in sources:
            payload = self._json_getter(
                url,
                {
                    "pageNo": encode_china_param("1"),
                    "pageSize": encode_china_param(str(page_size)),
                    "keyword": encode_china_param(""),
                    "source": encode_china_param("GOVWEB"),
                },
            )
            if not payload.get("successful", True):
                raise RuntimeError(payload.get("error") or "China SAMR returned unsuccessful response")
            for item in payload.get("rows", []):
                copied = dict(item)
                copied["category"] = category
                records.append(map_china_item(copied))
                if len(records) >= self.limit:
                    return records
        return records


def parse_china_html(html, base_url, limit=50):
    records = []
    seen = set()
    for href, title in _extract_links(html):
        if not title or not href or not _looks_like_recall(title, href):
            continue
        url = urljoin(base_url, href)
        if url in seen:
            continue
        seen.add(url)
        records.append(map_china_item({"title": title, "url": url}))
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


def map_china_item(item):
    title = _text(item.get("title")) or _text(item.get("doctitle"))
    url = _text(item.get("url")) or _text(item.get("docpuburl"))
    date = _text(item.get("date")) or _text(item.get("docreltime"))
    product = _text(item.get("product"))
    company = _text(item.get("company"))
    risk = _text(item.get("risk"))
    action = _text(item.get("action"))
    category = _text(item.get("category"))
    summary = _join_nonempty([product, company, risk, action])

    return RecallRecord(
        id=_text(item.get("id")) or stable_id("China SAMR", title, url),
        source="China SAMR",
        source_url=sanitize_url(url),
        region="CN",
        published_at=date,
        updated_at=date,
        title_original=title,
        title_zh=title,
        summary_zh=summary or title,
        brand=company,
        product=product,
        model="",
        categories=[category] if category else [],
        risks=[risk] if risk else [],
        action=action,
        severity="unknown",
        dedupe_key=stable_id("China SAMR", company, product, title),
        raw=dict(item),
    )


def _http_get_text(url, timeout=20.0):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    if not response.encoding:
        response.encoding = response.apparent_encoding
    return response.text


def _http_post_json(url, data, timeout=20.0):
    response = requests.post(
        url,
        data=data,
        timeout=timeout,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; recall-monitor/0.1; +https://github.com/xuweiqiang/recall_monitor)",
            "Referer": CHINA_REFERER,
        },
    )
    response.raise_for_status()
    return response.json()


def encode_china_param(value):
    return base64.urlsafe_b64encode(_text(value).encode("utf-8")).decode("ascii")


def _looks_like_recall(title, href):
    haystack = (title + " " + href).lower()
    return "召回" in haystack or "recall" in haystack


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
