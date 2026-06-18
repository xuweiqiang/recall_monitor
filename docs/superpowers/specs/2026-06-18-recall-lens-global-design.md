# Recall Lens Global 设计规格

## 目标

Recall Lens Global 是一个面向中文普通用户的全球产品召回监控页面。它定时抓取中国、美国、加拿大、欧盟和全球聚合召回信息，将政府公告按普通人的生活场景重新整理，让用户快速知道“哪些召回可能和我有关”。

项目第一版必须保持轻量：使用 GitHub Actions 定时抓取数据，使用 GitHub Pages 展示静态页面，不部署后端服务，不要求用户登录。

## 目标用户

- 普通家庭用户
- 家长和老人照护者
- 车主、租房者、养宠用户
- 关注食品、药品、电器、电池、儿童用品安全的人

## 核心场景

1. 用户打开页面，先看到“今日重点”召回。
2. 用户按生活分类查看召回，例如儿童与母婴、食品与药品、电器与电池、汽车交通。
3. 用户配置本地关注关键词，例如“婴儿食品”“充电宝”“血压计”“花生”“特斯拉”。
4. 页面用中文摘要说明风险、地区、建议动作，并保留官方原文标题和来源链接。
5. 某个数据源抓取失败时，页面仍显示其他来源的数据，并标注该来源的失败状态。

## v1 覆盖范围

### 地区和来源

- 中国：国家市场监督管理总局、缺陷产品召回相关官方网页。
- 美国：FDA、CPSC、NHTSA、USDA FSIS。
- 加拿大：Recalls and Safety Alerts。
- 欧盟：Safety Gate。
- 全球补充：OECD GlobalRecalls。

### 生活分类

- 食品饮料
- 药品保健
- 医疗护理
- 儿童婴幼儿
- 家电电器
- 电池充电
- 家具家装
- 汽车交通
- 宠物用品
- 运动户外
- 个护美妆
- 工具五金

### 风险分类

- 火灾
- 窒息
- 过敏
- 污染
- 触电
- 受伤
- 中毒
- 药品错误
- 车辆安全
- 未分类

## v1 不做

- 不做账号系统。
- 不做邮件、短信、微信推送。
- 不做后端数据库。
- 不强行承诺覆盖全球所有国家的所有召回。
- 不使用复杂 AI 翻译作为核心依赖。
- 不做复杂跨国家自动去重，只做轻量疑似重复提示。
- 不提供医疗、法律或购买建议，只提供官方召回信息摘要和来源链接。

## 信息模型

每条召回记录统一转换为内部结构：

```json
{
  "id": "source-specific-id-or-hash",
  "source": "FDA",
  "source_url": "https://example.gov/recall/123",
  "region": "US",
  "published_at": "2026-06-18",
  "updated_at": "2026-06-18",
  "title_original": "Original official title",
  "title_zh": "中文标题",
  "summary_zh": "简短中文摘要",
  "brand": "Brand",
  "product": "Product name",
  "model": "Model or batch",
  "categories": ["食品饮料"],
  "risks": ["过敏"],
  "action": "停止食用并联系销售方",
  "severity": "high",
  "dedupe_key": "normalized-brand-product-model-risk",
  "raw": {}
}
```

`raw` 保留原始字段，便于后续修正解析逻辑。页面默认不展示 `raw`。

## 架构

```text
GitHub Actions
  |
  |-- fetch scripts
  |     |-- fetch_cn.py
  |     |-- fetch_us_fda.py
  |     |-- fetch_us_cpsc.py
  |     |-- fetch_us_nhtsa.py
  |     |-- fetch_us_usda.py
  |     |-- fetch_ca.py
  |     |-- fetch_eu.py
  |     `-- fetch_oecd.py
  |
  |-- normalize/classify
  |
  `-- public/data/recalls.json
       public/data/status.json

GitHub Pages
  |
  `-- static web app
        |-- category tabs
        |-- search/filter
        |-- localStorage watch keywords
        `-- source status panel
```

## 数据流

1. GitHub Actions 按计划运行抓取任务。
2. 每个来源独立抓取，失败不会中断其他来源。
3. 抓取结果转换为统一召回模型。
4. 分类器根据关键词、来源字段和风险词生成生活分类与风险分类。
5. 生成 `recalls.json` 和 `status.json`。
6. GitHub Pages 加载静态 JSON，在浏览器内完成搜索、筛选和“我的关注”匹配。

## 分类策略

v1 使用规则分类，不依赖大模型。

- 标题、产品名、描述中命中 `baby`、`toy`、`crib`、`儿童` 等词，归入儿童婴幼儿。
- 命中 `battery`、`charger`、`power bank`、`锂电` 等词，归入电池充电。
- 命中 `allergen`、`peanut`、`milk`、`undeclared`、`过敏原` 等词，风险归为过敏。
- 命中 `fire`、`burn`、`overheat`、`起火` 等词，风险归为火灾。

规则表独立保存，便于后续调整。

## 去重策略

v1 不做强去重。系统生成 `dedupe_key`，当多条记录的品牌、产品、型号、风险高度接近时，在页面提示“可能相关召回”。

这样可以避免误合并不同国家、不同批次、不同处置方式的召回。

## 错误处理

- 单个来源请求失败：记录到 `status.json`，继续处理其他来源。
- 单条记录解析失败：跳过该条，记录错误计数和来源。
- 字段缺失：允许为空，页面隐藏空字段。
- 网络超时：每个来源设置超时和重试次数。
- 数据源结构变化：抓取脚本失败时在状态面板提示，而不是生成错误页面。

## 页面设计

首页优先展示普通人能立即理解的入口：

- 今日重点
- 我的关注
- 中国相关
- 儿童与母婴
- 食品与药品
- 电器与电池
- 汽车交通
- 全部召回

每条卡片显示：

- 中文标题
- 地区和来源
- 发布时间
- 风险标签
- 产品、品牌、型号或批次
- 建议动作
- 官方链接

## 验证方式

### 抓取验证

- 每个来源至少保留一个单元测试样例。
- 解析器必须能处理字段缺失。
- 抓取失败不应阻止其他来源输出。

### 页面验证

- 本地构建或静态预览能正常加载。
- `recalls.json` 缺失或为空时页面显示空状态。
- 搜索和分类筛选在浏览器内可用。
- localStorage 关注关键词不上传。

### 部署验证

- GitHub Actions 能生成 `public/data/recalls.json`。
- GitHub Pages 能访问首页和数据文件。
- 定时任务失败时能从 Actions 日志定位到具体来源。

## 风险和约束

- 中国官方网页可能没有稳定公开 API，需要保守抓取并容忍字段缺失。
- 不同国家发布时间和召回口径不同，不能简单比较严重程度。
- 自动中文摘要可能有误，页面必须保留原文标题和官方链接。
- 本项目只做信息整理，不替代官方公告。

## 后续扩展

- 增加英国、日本、韩国、澳大利亚、新加坡等国家源。
- 增加 RSS/Atom 输出。
- 增加浏览器通知，但仍不引入后端账号。
- 增加 AI 摘要作为可选增强，但不作为基础数据链路依赖。
