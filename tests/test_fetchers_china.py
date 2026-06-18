# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall_monitor.fetchers.china import (
    CHINA_SAMR_URL,
    ChinaFetcher,
    encode_china_param,
    map_china_item,
    parse_china_html,
)


def test_map_china_item_maps_local_sample_fields():
    item = {
        "title": "某公司召回儿童自行车",
        "url": "https://www.samr.gov.cn/recall/notice.html",
        "date": "2026-05-30",
        "product": "儿童自行车",
        "company": "示例公司",
        "risk": "制动失效，存在受伤风险",
        "action": "消费者应立即停止使用并联系公司维修。",
        "category": "儿童用品",
    }

    record = map_china_item(item)

    assert record.id
    assert record.source == "China SAMR"
    assert record.source_url == item["url"]
    assert record.region == "CN"
    assert record.published_at == "2026-05-30"
    assert record.updated_at == "2026-05-30"
    assert record.title_original == item["title"]
    assert record.brand == "示例公司"
    assert record.product == "儿童自行车"
    assert record.categories == ["儿童用品"]
    assert record.risks == ["制动失效，存在受伤风险"]
    assert record.action == item["action"]
    assert record.raw == item


def test_map_china_item_maps_official_news_fields():
    item = {
        "docpuburl": "https://www.samrdprc.org.cn/xfpzh/xfpgnzh/202606/t20260616_115652.html",
        "docreltime": "2026-06-12",
        "doctitle": "【广东】普宁市军埠石头王电器厂召回海雅牌延长线插座",
        "category": "消费品",
    }

    record = map_china_item(item)

    assert record.source == "China SAMR"
    assert record.source_url == item["docpuburl"]
    assert record.published_at == "2026-06-12"
    assert record.title_original == item["doctitle"]
    assert record.categories == ["消费品"]


def test_encode_china_param_matches_site_base16_for_ascii_values():
    assert encode_china_param("1") == "MQ=="
    assert encode_china_param("10") == "MTA="
    assert encode_china_param("GOVWEB") == "R09WV0VC"


def test_parse_china_html_extracts_notice_links_with_absolute_urls():
    html = """
    <html><body>
      <a href="/recall/notice-1.html">某公司召回儿童自行车</a>
      <a href="/about.html">机构简介</a>
    </body></html>
    """

    records = parse_china_html(html, base_url="https://www.samr.gov.cn", limit=5)

    assert len(records) == 1
    assert records[0].title_original == "某公司召回儿童自行车"
    assert records[0].source_url == "https://www.samr.gov.cn/recall/notice-1.html"


def test_china_fetcher_default_url_is_configurable():
    fetcher = ChinaFetcher(limit=3, url="https://example.cn/list.html")

    assert fetcher.url == "https://example.cn/list.html"
    assert fetcher.limit == 3
    assert CHINA_SAMR_URL == "https://qxzh.samr.gov.cn/qxzh/qxxxcx/web.jsp"


def test_china_fetcher_fetch_uses_injected_html_getter():
    fetcher = ChinaFetcher(
        limit=2,
        url="https://www.samr.gov.cn",
        html_getter=lambda url: '<a href="/recall/notice-1.html">某公司召回儿童自行车</a>',
    )

    result = fetcher.fetch()

    assert result.source == "China SAMR"
    assert result.status.ok is True
    assert result.status.count == 1
    assert result.records[0].source_url == "https://www.samr.gov.cn/recall/notice-1.html"


def test_china_fetcher_fetch_uses_official_json_getter():
    def fake_json_getter(url, data):
        assert data["pageNo"] == "MQ=="
        assert data["pageSize"] == "Mg=="
        assert "keyword" in data
        return {
            "successful": True,
            "rows": [
                {
                    "docpuburl": "https://www.samrdprc.org.cn/xfpzh/xfpgnzh/202606/t20260616_115652.html",
                    "docreltime": "2026-06-12",
                    "doctitle": "【广东】普宁市军埠石头王电器厂召回海雅牌延长线插座",
                }
            ],
        }

    fetcher = ChinaFetcher(limit=2, json_getter=fake_json_getter)

    result = fetcher.fetch()

    assert result.status.ok is True
    assert result.status.count == 2
    assert {record.categories[0] for record in result.records} == {"汽车", "消费品"}
