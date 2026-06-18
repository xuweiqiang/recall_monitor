from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from recall_monitor.classifier import classify_record_text


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("婴儿摇铃含小零件，可能造成窒息", "儿童婴幼儿"),
        ("花生酱食品可能被沙门氏菌污染", "食品饮料"),
        ("降压药标签剂量错误", "药品保健"),
        ("一次性注射器医疗器械无菌包装破损", "医疗护理"),
        ("电热水壶家电存在触电风险", "家电电器"),
        ("移动电源锂电池充电时可能起火", "电池充电"),
        ("折叠床家具可能夹伤儿童", "家具家装"),
        ("汽车制动系统故障影响车辆安全", "汽车交通"),
        ("宠物狗粮可能被霉菌污染", "宠物用品"),
        ("自行车头盔运动用品扣具断裂", "运动户外"),
        ("面霜化妆品含未申报过敏原", "个护美妆"),
        ("电钻工具开关故障可能导致受伤", "工具五金"),
    ],
)
def test_classify_categories(text, category):
    result = classify_record_text(text)

    assert category in result["categories"]


@pytest.mark.parametrize(
    ("text", "risk"),
    [
        ("移动电源过热可能引发火灾", "火灾"),
        ("婴儿玩具小零件脱落造成窒息", "窒息"),
        ("面霜含有未标示花生成分可能过敏", "过敏"),
        ("食品疑似细菌污染", "污染"),
        ("电热毯绝缘失效可能触电", "触电"),
        ("梯子断裂导致跌落受伤", "受伤"),
        ("清洁剂误食可能中毒", "中毒"),
        ("药品说明书剂量错误", "药品错误"),
        ("汽车安全气囊故障影响车辆安全", "车辆安全"),
    ],
)
def test_classify_risks(text, risk):
    result = classify_record_text(text)

    assert risk in result["risks"]


def test_classify_unknown_text_uses_uncategorized_defaults():
    result = classify_record_text("召回公告")

    assert result["categories"] == ["未分类"]
    assert result["risks"] == ["未分类"]
    assert result["severity"] == "unknown"
    assert result["action"] == "查看召回公告并按官方指引处理。"


def test_classify_high_severity_for_fire_or_choking():
    fire = classify_record_text("移动电源起火风险")
    choking = classify_record_text("婴儿玩具窒息风险")

    assert fire["severity"] == "high"
    assert choking["severity"] == "high"
