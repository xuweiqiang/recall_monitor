# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from recall_monitor.fetchers.base import FetchResult, stable_id
from recall_monitor.model import RecallRecord


class SampleFetcher:
    name = "sample"

    def fetch(self):
        records = [
            RecallRecord(
                id=stable_id(self.name, "infant-toy-choking"),
                source="SAMPLE",
                source_url="https://example.com/sample/infant-toy-choking",
                region="GLOBAL",
                published_at="2026-06-18",
                updated_at="2026-06-18",
                title_original="Infant toy recalled for choking risk",
                title_zh="婴儿玩具因小零件脱落风险召回",
                summary_zh="婴儿摇铃的小零件可能脱落，存在窒息风险。",
                brand="Sample Kids",
                product="婴儿摇铃",
                model="IR-1",
                dedupe_key=stable_id("Sample Kids", "婴儿摇铃", "IR-1", "窒息"),
                raw={"sample": True},
            ),
            RecallRecord(
                id=stable_id(self.name, "power-bank-fire"),
                source="SAMPLE",
                source_url="https://example.com/sample/power-bank-fire",
                region="GLOBAL",
                published_at="2026-06-17",
                updated_at="2026-06-17",
                title_original="Power bank recalled for fire risk",
                title_zh="移动电源因过热起火风险召回",
                summary_zh="部分移动电源锂电池在充电时可能过热，存在起火风险。",
                brand="Sample Power",
                product="移动电源",
                model="PB-100",
                dedupe_key=stable_id("Sample Power", "移动电源", "PB-100", "火灾"),
                raw={"sample": True},
            ),
        ]
        return FetchResult(source="SAMPLE", records=records)
