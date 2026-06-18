const DATA_URL = "./data/recalls.json";
const STATUS_URL = "./data/status.json";
const WATCH_KEY = "recall-monitor-watch-keywords";

const categories = [
  { id: "today", label: "今日重点" },
  { id: "watch", label: "我的关注" },
  { id: "china", label: "中国相关" },
  { id: "children", label: "儿童与母婴" },
  { id: "food", label: "食品与药品" },
  { id: "electronics", label: "电器与电池" },
  { id: "auto", label: "汽车交通" },
  { id: "all", label: "全部召回" },
];

const state = {
  records: [],
  status: null,
  activeCategory: "today",
  search: "",
  watchKeywords: [],
};

const el = {
  updatedAt: document.querySelector("#updatedAt"),
  searchInput: document.querySelector("#searchInput"),
  categoryTabs: document.querySelector("#categoryTabs"),
  watchKeywords: document.querySelector("#watchKeywords"),
  saveWatch: document.querySelector("#saveWatch"),
  saveHint: document.querySelector("#saveHint"),
  sourceStatus: document.querySelector("#sourceStatus"),
  resultSummary: document.querySelector("#resultSummary"),
  recallList: document.querySelector("#recallList"),
  cardTemplate: document.querySelector("#recallCardTemplate"),
};

function asArray(value) {
  return Array.isArray(value) ? value : [];
}

function normalizeText(value) {
  if (value === null || value === undefined) {
    return "";
  }
  return String(value).trim();
}

function formatList(value) {
  const items = asArray(value).map(normalizeText).filter(Boolean);
  return items.length ? items.join("、") : "未标注";
}

function formatDate(value) {
  const text = normalizeText(value);
  if (!text) {
    return "未知";
  }
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) {
    return text;
  }
  return new Intl.DateTimeFormat("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: text.includes("T") ? "2-digit" : undefined,
    minute: text.includes("T") ? "2-digit" : undefined,
    timeZoneName: text.includes("T") ? "short" : undefined,
  }).format(date);
}

function textBlob(record) {
  return [
    record.title_zh,
    record.title_original,
    record.region,
    record.source,
    record.summary_zh,
    record.brand,
    record.product,
    record.model,
    record.action,
    ...asArray(record.risks),
    ...asArray(record.categories),
  ]
    .map(normalizeText)
    .join(" ")
    .toLowerCase();
}

function parseKeywords(text) {
  return text
    .split(/\n|,|，|;/)
    .map((item) => item.trim().toLowerCase())
    .filter(Boolean);
}

function localDateKey(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function isToday(record) {
  const published = normalizeText(record.published_at || record.updated_at);
  if (!published) {
    return false;
  }
  const today = localDateKey(new Date());
  return published.slice(0, 10) === today;
}

function includesAny(record, keywords) {
  if (!keywords.length) {
    return false;
  }
  const blob = textBlob(record);
  return keywords.some((keyword) => blob.includes(keyword));
}

function matchesCategory(record) {
  const blob = textBlob(record);
  const categoryText = formatList(record.categories).toLowerCase();
  const riskText = formatList(record.risks).toLowerCase();

  switch (state.activeCategory) {
    case "today":
      return isToday(record) || normalizeText(record.severity).toLowerCase() === "high";
    case "watch":
      return includesAny(record, state.watchKeywords);
    case "china":
      return /中国|china|cn|香港|澳门|台湾/.test(blob);
    case "children":
      return /儿童|婴|母婴|baby|child|children|toy/.test(`${categoryText} ${blob}`);
    case "food":
      return /食品|食物|药|医疗|food|drug|medicine|medical/.test(`${categoryText} ${blob}`);
    case "electronics":
      return /电器|电池|充电|锂|battery|charger|power|fire|过热/.test(`${categoryText} ${riskText} ${blob}`);
    case "auto":
      return /汽车|车辆|交通|auto|vehicle|car|motor|brake/.test(`${categoryText} ${blob}`);
    case "all":
    default:
      return true;
  }
}

function matchesSearch(record) {
  const query = state.search.trim().toLowerCase();
  if (!query) {
    return true;
  }
  return textBlob(record).includes(query);
}

function getFilteredRecords() {
  return state.records
    .filter(matchesCategory)
    .filter(matchesSearch)
    .sort((a, b) => normalizeText(b.published_at).localeCompare(normalizeText(a.published_at)));
}

function createMeta(label, value) {
  const wrapper = document.createElement("div");
  const dt = document.createElement("dt");
  const dd = document.createElement("dd");
  dt.textContent = label;
  dd.textContent = value || "未知";
  wrapper.append(dt, dd);
  return wrapper;
}

function createDetail(label, value) {
  const wrapper = document.createElement("div");
  const labelEl = document.createElement("span");
  const valueEl = document.createElement("strong");
  wrapper.className = "detail";
  labelEl.textContent = label;
  valueEl.textContent = value || "未标注";
  wrapper.append(labelEl, valueEl);
  return wrapper;
}

function renderCategories() {
  el.categoryTabs.replaceChildren(
    ...categories.map((category) => {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = category.label;
      button.setAttribute("aria-pressed", String(category.id === state.activeCategory));
      button.addEventListener("click", () => {
        state.activeCategory = category.id;
        render();
      });
      return button;
    }),
  );
}

function renderStatus() {
  const sources = asArray(state.status && state.status.sources);
  if (!sources.length) {
    el.sourceStatus.textContent = "暂无数据源状态。";
    return;
  }

  el.sourceStatus.replaceChildren(
    ...sources.map((source) => {
      const item = document.createElement("div");
      const title = document.createElement("strong");
      const detail = document.createElement("span");
      const health = document.createElement("span");

      item.className = "source-item";
      title.textContent = normalizeText(source.source) || "UNKNOWN";
      health.className = source.ok ? "source-ok" : "source-bad";
      health.textContent = source.ok ? `正常，${source.count ?? 0} 条` : `异常：${source.error || "未知错误"}`;
      detail.textContent = `抓取时间：${formatDate(source.fetched_at)}`;
      item.append(title, health, detail);
      return item;
    }),
  );
}

function renderCards(records) {
  if (!records.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.textContent = "没有匹配的召回记录。可以调整搜索词、分类或我的关注关键词。";
    el.recallList.replaceChildren(empty);
    return;
  }

  el.recallList.replaceChildren(
    ...records.map((record) => {
      const card = el.cardTemplate.content.firstElementChild.cloneNode(true);
      const title = normalizeText(record.title_zh) || normalizeText(record.title_original) || "未命名召回";
      const originalTitle = normalizeText(record.title_original);
      const sourceUrl = normalizeText(record.source_url);

      card.querySelector("h3").textContent = title;
      card.querySelector(".original-title").textContent = originalTitle && originalTitle !== title ? originalTitle : "";
      card.querySelector(".severity").textContent = normalizeText(record.severity) || "未评级";
      card.querySelector(".summary").textContent = normalizeText(record.summary_zh) || "暂无中文摘要。";
      card.querySelector(".action").textContent = `建议措施：${normalizeText(record.action) || "请查看官方来源。"} `;

      card.querySelector(".meta-grid").replaceChildren(
        createMeta("地区", normalizeText(record.region)),
        createMeta("来源", normalizeText(record.source)),
        createMeta("发布日期", formatDate(record.published_at)),
        createMeta("风险/分类", `${formatList(record.risks)} / ${formatList(record.categories)}`),
      );

      card.querySelector(".detail-grid").replaceChildren(
        createDetail("品牌", normalizeText(record.brand)),
        createDetail("产品", normalizeText(record.product)),
        createDetail("型号", normalizeText(record.model)),
      );

      const link = card.querySelector(".source-link");
      if (sourceUrl) {
        link.href = sourceUrl;
        link.textContent = sourceUrl;
      } else {
        link.removeAttribute("href");
        link.textContent = "暂无来源链接";
      }

      return card;
    }),
  );
}

function render() {
  const records = getFilteredRecords();
  const active = categories.find((category) => category.id === state.activeCategory);
  renderCategories();
  renderStatus();
  renderCards(records);
  el.resultSummary.textContent = `${active ? active.label : "全部"}：显示 ${records.length} 条，共 ${state.records.length} 条召回记录。`;
}

async function loadJson(url) {
  const response = await fetch(url, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${url} HTTP ${response.status}`);
  }
  return response.json();
}

async function init() {
  const savedKeywords = localStorage.getItem(WATCH_KEY) || "";
  el.watchKeywords.value = savedKeywords;
  state.watchKeywords = parseKeywords(savedKeywords);

  renderCategories();

  el.searchInput.addEventListener("input", (event) => {
    state.search = event.target.value;
    render();
  });

  el.saveWatch.addEventListener("click", () => {
    localStorage.setItem(WATCH_KEY, el.watchKeywords.value);
    state.watchKeywords = parseKeywords(el.watchKeywords.value);
    el.saveHint.textContent = "已保存到本地";
    window.setTimeout(() => {
      el.saveHint.textContent = "";
    }, 1800);
    render();
  });

  try {
    const [recalls, status] = await Promise.all([loadJson(DATA_URL), loadJson(STATUS_URL)]);
    state.records = asArray(recalls.records || recalls.items || recalls.data);
    state.status = status;
    el.updatedAt.textContent = formatDate(recalls.generated_at || status.generated_at);
    render();
  } catch (error) {
    el.updatedAt.textContent = "加载失败";
    el.resultSummary.textContent = "数据加载失败";
    const errorBox = document.createElement("div");
    errorBox.className = "error-state";
    errorBox.textContent = `无法读取静态数据：${error.message}`;
    el.recallList.replaceChildren(errorBox);
    el.sourceStatus.textContent = "数据源状态加载失败。";
  }
}

init();
