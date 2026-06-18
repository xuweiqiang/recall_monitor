# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

try:
    from dataclasses import dataclass
except ImportError:

    def dataclass(cls):
        return cls


def dumps_json(payload):
    return json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


@dataclass
class RecallRecord:
    __annotations__ = {
        "id": str,
        "source": str,
        "source_url": str,
        "region": str,
        "published_at": str,
        "updated_at": str,
        "title_original": str,
        "title_zh": str,
        "summary_zh": str,
        "brand": str,
        "product": str,
        "model": str,
        "categories": list,
        "risks": list,
        "action": str,
        "severity": str,
        "dedupe_key": str,
        "raw": dict,
    }

    def __init__(
        self,
        id,
        source,
        source_url,
        region,
        published_at,
        updated_at,
        title_original,
        title_zh,
        summary_zh,
        brand,
        product,
        model,
        categories=None,
        risks=None,
        action="",
        severity="unknown",
        dedupe_key="",
        raw=None,
    ):
        self.id = id
        self.source = source
        self.source_url = source_url
        self.region = region
        self.published_at = published_at
        self.updated_at = updated_at
        self.title_original = title_original
        self.title_zh = title_zh
        self.summary_zh = summary_zh
        self.brand = brand
        self.product = product
        self.model = model
        self.categories = categories or []
        self.risks = risks or []
        self.action = action
        self.severity = severity
        self.dedupe_key = dedupe_key
        self.raw = raw or {}

    def to_public_dict(self, include_raw=False):
        payload = {
            "id": self.id,
            "source": self.source,
            "source_url": self.source_url,
            "region": self.region,
            "published_at": self.published_at,
            "updated_at": self.updated_at,
            "title_original": self.title_original,
            "title_zh": self.title_zh,
            "summary_zh": self.summary_zh,
            "brand": self.brand,
            "product": self.product,
            "model": self.model,
            "categories": self.categories,
            "risks": self.risks,
            "action": self.action,
            "severity": self.severity,
            "dedupe_key": self.dedupe_key,
            "raw": self.raw,
        }
        if not include_raw:
            payload.pop("raw", None)
        return payload


@dataclass
class SourceStatus:
    __annotations__ = {
        "source": str,
        "ok": bool,
        "fetched_at": str,
        "count": int,
        "error": object,
    }

    def __init__(self, source, ok, fetched_at, count=0, error=None):
        self.source = source
        self.ok = ok
        self.fetched_at = fetched_at
        self.count = count
        self.error = error

    def to_dict(self):
        return {
            "source": self.source,
            "ok": self.ok,
            "fetched_at": self.fetched_at,
            "count": self.count,
            "error": self.error,
        }

    def to_public_dict(self):
        return self.to_dict()
