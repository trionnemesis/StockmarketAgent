(function () {
  "use strict";

  var STANCE_LABELS = {
    BUY: "模擬情境偏多",
    HOLD: "模擬情境中性",
    SELL: "模擬情境偏空",
    NO_SIGNAL: "目前沒有可用的即時買賣訊號"
  };

  var HORIZON_LABELS = {
    "1W": "約 1 週",
    "1M": "約 1 個月",
    "3M": "約 3 個月",
    "12M": "約 1 年"
  };

  var COMPONENT_LABELS = {
    macro: "總體環境",
    fundamental: "公司基本面",
    valuation: "估值合理性",
    technical: "價格趨勢",
    cycle: "產業循環",
    events: "事件影響"
  };

  var RISK_LABELS = {
    RESEARCH_FIXTURE: "目前分析使用模擬研究資料，不代表真實市場訊號",
    MODEL_UNCALIBRATED: "模型尚未完成歷史回測與校準",
    SOURCE_CONTRADICTION: "不同研究訊號互相矛盾，暫時不提供方向結論",
    UNIVERSE_OWNER_APPROVAL_REQUIRED: "候選標的尚未完成正式核准",
    PRODUCTION_SIGNALS_DISABLED: "正式買賣訊號目前停用"
  };

  var TEXT_REPLACEMENTS = [
    ["TRI-MARKET RESEARCH INTELLIGENCE", "跨市場研究摘要"],
    ["PUBLIC PREVIEW", "公開研究預覽"],
    ["RESEARCH ONLY", "研究預覽"],
    ["EVIDENCE REVIEW", "資料查證"],
    ["SIGNAL GATE · 3M", "約 3 個月的模擬研究看法"],
    ["MARKET STATUS", "市場狀態"],
    ["PRIORITY QUEUE", "待補強項目"],
    ["PROPOSED UNIVERSE", "候選標的"],
    ["OFFICIAL COVERAGE MATRIX", "官方資料總覽"],
    ["OFFICIAL OBSERVED FACTS", "官方市場資料"],
    ["OBSERVATION DETAIL", "官方資料摘要"],
    ["PROVENANCE", "資料來源與追溯"],
    ["DATA-QUALITY EVIDENCE", "資料可靠度"],
    ["MULTI-HORIZON", "不同時間尺度"],
    ["MODEL COMPONENTS", "分析構面"],
    ["EXPLAINABILITY", "判斷依據"],
    ["RISK GATE", "風險與限制"],
    ["APPLICABILITY", "目前可用程度"],
    ["EVIDENCE", "資料依據"],
    ["METHODOLOGY", "研究方法"],
    ["PIPELINE", "分析流程"],
    ["STANCE", "研究看法"],
    ["RESEARCH BOUNDARY", "使用限制"],
    ["SYSTEM STATUS", "系統狀態"],
    ["research_fixture", "模擬研究資料"],
    ["uncalibrated", "尚未完成回測校準"],
    ["owner approval required", "尚待正式核准"],
    ["proposed / disabled", "候選中 / 尚未正式啟用"],
    ["proposed · disabled", "候選中 · 尚未正式啟用"],
    ["proposed", "候選中"],
    ["disabled", "尚未啟用"],
    ["Risk Gate", "安全檢查"],
    ["research score", "模擬研究分數"],
    ["confidence", "研究信心分數"],
    ["official_observation", "官方市場資料"],
    ["source official_observation", "資料來源：官方市場資料"],
    ["official as of", "資料日期"],
    ["sessions behind", "個交易日落後"],
    ["OGL attribution", "官方開放資料授權"],
    ["not used in signal", "尚未納入模型判斷"],
    ["signal-isolated", "未納入模型"],
    ["context only · not directional", "僅供資料品質判讀 · 不代表買賣方向"],
    ["high materiality", "高優先事項"],
    ["synthetic scenario", "模擬研究情境"],
    ["synthetic fixture", "模擬研究資料"],
    ["live market", "目前市場"],
    ["production signal", "正式買賣訊號"]
  ];

  function stanceLabel(stance) {
    return STANCE_LABELS[stance] || "研究狀態未定";
  }

  function scoreLabel(score) {
    var value = Number(score);
    if (!Number.isFinite(value)) {
      return "資料不足";
    }
    if (value > 0) {
      return "偏正面";
    }
    if (value < 0) {
      return "偏負面";
    }
    return "中性";
  }

  function freshnessLabel(value) {
    return {
      fresh: "資料正常",
      stale: "資料已落後",
      missing: "缺少最新資料"
    }[value] || "資料狀態待確認";
  }

  function replaceVisibleText(root) {
    var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) {
      nodes.push(walker.currentNode);
    }
    nodes.forEach(function (node) {
      var parent = node.parentElement;
      if (!parent || parent.closest("code, pre, script, style, [data-technical-raw]")) {
        return;
      }
      var text = node.nodeValue;
      TEXT_REPLACEMENTS.forEach(function (entry) {
        text = text.split(entry[0]).join(entry[1]);
      });
      node.nodeValue = text;
    });
  }

  function humanizeStances() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-stance]"), function (node) {
      if (node.classList.contains("stance")) {
        node.setAttribute("aria-label", stanceLabel(node.dataset.stance));
      }
    });
    Array.prototype.forEach.call(document.querySelectorAll(".stance[data-input-kind='synthetic_fixture']"), function (badge) {
      var holder = badge.closest("[data-stance]");
      var stance = holder ? holder.dataset.stance : null;
      if (!stance) {
        var text = badge.textContent || "";
        if (text.indexOf("BUY") !== -1) { stance = "BUY"; }
        else if (text.indexOf("HOLD") !== -1) { stance = "HOLD"; }
        else if (text.indexOf("SELL") !== -1) { stance = "SELL"; }
        else { stance = "NO_SIGNAL"; }
      }
      badge.textContent = stanceLabel(stance);
      badge.setAttribute("title", "底層狀態碼：" + stance + "；僅供模擬研究");
    });
  }

  function humanizeHorizonCards() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-horizon]"), function (card) {
      var horizon = card.dataset.horizon;
      var first = card.querySelector(":scope > span:first-child");
      if (first && HORIZON_LABELS[horizon]) {
        first.textContent = HORIZON_LABELS[horizon];
      }
      var score = card.querySelector("div strong");
      if (score) {
        score.textContent = scoreLabel(card.dataset.score);
        score.setAttribute("title", "原始模擬分數：" + card.dataset.score);
      }
      var scoreCaption = card.querySelector("div small");
      if (scoreCaption) {
        scoreCaption.textContent = "模擬研究傾向";
      }
      var detail = card.querySelector(":scope > p");
      if (detail) {
        detail.textContent = "尚未完成回測校準，不能當成即時投資建議";
      }
    });
  }

  function humanizeComponents() {
    Array.prototype.forEach.call(document.querySelectorAll("[data-component]"), function (card) {
      var key = card.dataset.component;
      var label = card.querySelector("span");
      var score = card.querySelector("strong");
      var detail = card.querySelector("small");
      if (label && COMPONENT_LABELS[key]) {
        label.textContent = COMPONENT_LABELS[key];
      }
      if (score) {
        score.textContent = scoreLabel(card.dataset.score);
        score.setAttribute("title", "原始模擬分數：" + card.dataset.score);
      }
      if (detail) {
        detail.textContent = "依目前模擬情境計算；原始技術值保留於頁面資料屬性";
      }
    });
  }

  function humanizeRiskFlags() {
    Array.prototype.forEach.call(document.querySelectorAll(".risk-list li"), function (item) {
      var raw = (item.textContent || "").trim();
      if (RISK_LABELS[raw]) {
        item.dataset.rawFlag = raw;
        item.textContent = RISK_LABELS[raw];
      }
    });
  }

  function collapseTechnicalSourceDetails() {
    Array.prototype.forEach.call(document.querySelectorAll(".section-card"), function (section) {
      var heading = section.querySelector(":scope > h2");
      if (!heading || heading.textContent.trim() !== "可追溯、可再建") {
        return;
      }
      var details = document.createElement("details");
      details.dataset.technicalDetails = "source";
      var summary = document.createElement("summary");
      summary.textContent = "查看資料來源與版本細節";
      details.appendChild(summary);
      while (heading.nextSibling) {
        details.appendChild(heading.nextSibling);
      }
      section.appendChild(details);
    });
  }

  function componentSummary() {
    var values = Array.prototype.map.call(document.querySelectorAll("[data-component]"), function (card) {
      return {
        key: card.dataset.component,
        score: Number(card.dataset.score)
      };
    }).filter(function (item) {
      return Number.isFinite(item.score);
    });
    values.sort(function (a, b) { return b.score - a.score; });
    var positive = values.filter(function (item) { return item.score > 0; }).slice(0, 2);
    var negative = values.slice().reverse().filter(function (item) { return item.score < 0; }).slice(0, 2);
    return {
      positive: positive.map(function (item) { return COMPONENT_LABELS[item.key] || item.key; }),
      negative: negative.map(function (item) { return COMPONENT_LABELS[item.key] || item.key; })
    };
  }

  function addHumanSummary() {
    var main = document.querySelector("main.main-content");
    var hero = document.querySelector(".instrument-hero");
    if (!main || !hero || main.querySelector("[data-human-summary]")) {
      return;
    }

    var threeMonth = document.querySelector("[data-horizon='3M']");
    var stance = threeMonth ? threeMonth.dataset.stance : "NO_SIGNAL";
    var official = document.querySelector("[data-official-as-of]");
    var freshness = document.querySelector("[data-observation-freshness]");
    var coverage = document.querySelector("[data-model-input-coverage]");
    var factors = componentSummary();

    var section = document.createElement("section");
    section.className = "section-card";
    section.dataset.humanSummary = "true";

    var factorText = "";
    if (factors.positive.length) {
      factorText += "模擬情境中較正面的因素：" + factors.positive.join("、") + "。";
    }
    if (factors.negative.length) {
      factorText += "較需要留意的因素：" + factors.negative.join("、") + "。";
    }
    if (!factorText) {
      factorText = "目前沒有足夠的模擬構面可整理成主要因素。";
    }

    var officialDate = official ? official.dataset.officialAsOf : "目前沒有官方觀測資料";
    var freshnessText = freshness ? freshnessLabel(freshness.dataset.observationFreshness) : "尚未接入官方觀測資料";
    var modelCoverage = coverage && coverage.dataset.modelInputCoverage !== "0" ? "已有部分官方資料納入" : "尚未納入模型";

    section.innerHTML =
      '<div class="section-heading"><div><p class="kicker">先看結論</p><h2>白話分析摘要</h2></div><span class="pill pill-neutral">給一般閱讀者</span></div>' +
      '<div class="notice notice-warning" role="note"><strong>目前沒有可用的即時買賣訊號</strong><span>頁面上的方向只來自模擬研究情境；官方市場資料目前尚未進入模型，因此不能把這個結果當成今天的買進或賣出建議。</span></div>' +
      '<div class="metric-grid">' +
        '<article class="metric-card"><span>約 3 個月的模擬看法</span><strong>' + stanceLabel(stance) + '</strong><small>僅供研究流程驗證</small></article>' +
        '<article class="metric-card"><span>官方資料日期</span><strong>' + officialDate + '</strong><small>不是即時報價</small></article>' +
        '<article class="metric-card"><span>資料狀態</span><strong>' + freshnessText + '</strong><small>依專案資料新鮮度規則判定</small></article>' +
        '<article class="metric-card"><span>官方資料是否已納入模型</span><strong>' + modelCoverage + '</strong><small>目前正式模型仍未啟用</small></article>' +
      '</div>' +
      '<p class="lead">' + factorText + ' 這些因素仍來自模擬研究資料，重點是幫助理解分析方向，而不是提供投資指令。</p>' +
      '<details data-technical-raw><summary>查看維護者用的原始技術值</summary>' +
        '<p>約 3 個月底層狀態：<code>' + stance + '</code>；原始分數：<code>' + (threeMonth ? threeMonth.dataset.score : "n/a") + '</code>；研究信心：<code>' + (threeMonth ? threeMonth.dataset.confidence : "n/a") + '</code>。其他原始值仍保留在頁面 <code>data-*</code> 屬性與 JSON。</p>' +
      '</details>';

    main.insertBefore(section, main.firstChild);
  }

  function humanizeApplicability() {
    Array.prototype.forEach.call(document.querySelectorAll(".fact-list div"), function (row) {
      var dt = row.querySelector("dt");
      var dd = row.querySelector("dd");
      if (!dt || !dd) { return; }
      var key = dt.textContent.trim();
      var raw = dd.textContent.trim();
      dd.dataset.rawValue = raw;
      if (key === "狀態" && raw === "proposed") {
        dd.textContent = "候選中，尚未正式核准";
      } else if (key === "啟用" && raw === "false") {
        dd.textContent = "尚未正式啟用";
      } else if (key === "資料狀態" && raw === "research_fixture") {
        dd.textContent = "目前分析使用模擬研究資料";
      } else if (key === "基準" && raw.indexOf(":BROAD_MARKET") !== -1) {
        dd.textContent = "大盤比較基準（技術代碼保留於頁面資料）";
      }
    });
  }

  function humanizePage() {
    addHumanSummary();
    humanizeHorizonCards();
    humanizeComponents();
    humanizeRiskFlags();
    humanizeApplicability();
    collapseTechnicalSourceDetails();
    humanizeStances();
    replaceVisibleText(document.body);
  }

  function setupFilters() {
    var form = document.querySelector("[data-filter-form]");
    if (!form) {
      return;
    }

    var rows = Array.prototype.slice.call(document.querySelectorAll("[data-instrument]"));
    var count = document.querySelector("[data-result-count]");

    function value(name) {
      var field = form.elements.namedItem(name);
      return field ? String(field.value || "").trim().toLowerCase() : "";
    }

    function applyFilters() {
      var search = value("search");
      var country = value("country");
      var asset = value("asset");
      var theme = value("theme");
      var visible = 0;

      rows.forEach(function (row) {
        var matches =
          (!search || row.dataset.search.indexOf(search) !== -1) &&
          (!country || row.dataset.country.toLowerCase() === country) &&
          (!asset || row.dataset.asset.toLowerCase() === asset) &&
          (!theme || row.dataset.themes.split(" ").indexOf(theme) !== -1);
        row.hidden = !matches;
        if (matches) {
          visible += 1;
        }
      });

      if (count) {
        count.textContent = String(visible);
      }
    }

    form.addEventListener("input", applyFilters);
    form.addEventListener("change", applyFilters);
    form.addEventListener("reset", function () {
      window.setTimeout(applyFilters, 0);
    });
  }

  humanizePage();
  setupFilters();
}());
