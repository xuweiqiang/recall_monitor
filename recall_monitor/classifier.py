# -*- coding: utf-8 -*-
from __future__ import unicode_literals


CATEGORY_RULES = [
    ("儿童婴幼儿", ("婴儿", "儿童", "幼儿", "玩具", "摇铃", "童车")),
    ("食品饮料", ("食品", "饮料", "花生酱", "狗粮", "沙门氏菌", "污染")),
    ("药品保健", ("药品", "保健", "药", "剂量", "说明书")),
    ("医疗护理", ("医疗", "护理", "注射器", "器械", "无菌")),
    ("家电电器", ("家电", "电器", "电热", "电热水壶", "电热毯")),
    ("电池充电", ("电池", "充电", "移动电源", "锂电池")),
    ("家具家装", ("家具", "家装", "折叠床", "床", "柜")),
    ("汽车交通", ("汽车", "交通", "车辆", "制动", "安全气囊")),
    ("宠物用品", ("宠物", "狗粮", "猫粮")),
    ("运动户外", ("运动", "户外", "自行车", "头盔")),
    ("个护美妆", ("个护", "美妆", "面霜", "化妆品")),
    ("工具五金", ("工具", "五金", "电钻", "梯子")),
]

RISK_RULES = [
    ("火灾", ("火灾", "起火", "过热", "燃烧")),
    ("窒息", ("窒息", "小零件", "脱落")),
    ("过敏", ("过敏", "过敏原", "未标示花生", "未申报")),
    ("污染", ("污染", "细菌", "沙门氏菌", "霉菌")),
    ("触电", ("触电", "绝缘失效", "漏电")),
    ("受伤", ("受伤", "夹伤", "跌落", "断裂")),
    ("中毒", ("中毒", "误食", "有毒")),
    ("药品错误", ("药品错误", "剂量错误", "标签剂量错误", "说明书剂量错误")),
    ("车辆安全", ("车辆安全", "制动系统", "安全气囊", "制动")),
]

ACTION_BY_RISK = {
    "火灾": "立即停止使用，远离可燃物，并按官方召回指引处理。",
    "窒息": "立即停止给儿童使用，并按官方召回指引处理。",
    "触电": "立即断电并停止使用，按官方召回指引处理。",
    "车辆安全": "停止高风险使用场景，联系经销商或官方渠道处理。",
}


def classify_record_text(text):
    haystack = text.lower()
    categories = _match_rules(haystack, CATEGORY_RULES)
    risks = _match_rules(haystack, RISK_RULES)

    if not categories:
        categories = ["未分类"]
    if not risks:
        risks = ["未分类"]

    severity = _severity_for_risks(risks)
    action = _action_for_risks(risks)

    return {
        "categories": categories,
        "risks": risks,
        "severity": severity,
        "action": action,
    }


def _match_rules(haystack, rules):
    matches = []
    for label, keywords in rules:
        if any(keyword.lower() in haystack for keyword in keywords):
            matches.append(label)
    return matches


def _severity_for_risks(risks):
    if any(risk in risks for risk in ("火灾", "窒息", "触电", "车辆安全", "中毒")):
        return "high"
    if risks == ["未分类"]:
        return "unknown"
    return "medium"


def _action_for_risks(risks):
    for risk in risks:
        if risk in ACTION_BY_RISK:
            return ACTION_BY_RISK[risk]
    return "查看召回公告并按官方指引处理。"
