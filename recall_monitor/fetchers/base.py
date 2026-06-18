# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime
import hashlib

from recall_monitor.model import RecallRecord

try:
    from dataclasses import dataclass
except ImportError:

    def dataclass(cls):
        return cls

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


@dataclass
class FetchResult:
    __annotations__ = {
        "source": str,
        "records": list,
    }

    def __init__(self, source, records):
        self.source = source
        self.records = records


class Fetcher(object):
    name = ""

    def fetch(self):
        raise NotImplementedError


def utc_now_iso():
    try:
        from datetime import UTC

        return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except ImportError:
        return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def stable_id(*parts):
    payload = "\n".join(_to_text(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def http_get_json(url, timeout=20.0):
    import requests

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def sanitize_url(url):
    text = _to_text(url).strip()
    if not text:
        return ""
    scheme = urlparse(text).scheme.lower()
    if scheme not in ("http", "https"):
        return ""
    return text


def _to_text(value):
    try:
        return unicode(value)
    except NameError:
        return str(value)
