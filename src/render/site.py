from __future__ import annotations

from html import escape
from typing import Any


SITE_URL = "https://trionnemesis.github.io/StockmarketAgent/"
REPOSITORY_URL = "https://github.com/trionnemesis/StockmarketAgent"
MARKET_NAMES = {"TW": "台灣", "JP": "日本", "US": "美國"}
ASSET_NAMES = {"stock": "個股", "etf": "ETF"}
THEME_NAMES = {
    "ai": "AI",
    "semiconductor": "半導體",
    "defense": "國防",
    "aerospace": "航太",
    "cybersecurity": "資安",
    "consumer_staples": "民生必需",
    "defensive": "防禦",
    "healthcare": "醫療",
    "telecom": "電信",
    "utilities": "公用事業",
    "broad_market": "廣泛市場",
    "quality": "品質",
    "value": "價值",
    "dividend": "股息",
    "low_volatility": "低波動",
}


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _head(
    *,
    title: str,
    description: str,
    prefix: str,
    canonical_path: str,
    root_social_card: bool,
) -> str:
    canonical = SITE_URL + canonical_path
    image = (
        f'<meta property="og:image" content="{SITE_URL}assets/og.png">'
        f'<meta property="og:image:alt" content="StockmarketAgent 三市場股票研究情報">'
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:image" content="{SITE_URL}assets/og.png">'
        if root_social_card
        else '<meta name="twitter:card" content="summary">'
    )
    return f"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{_e(description)}">
  <meta name="theme-color" content="#09182e">
  <meta property="og:type" content="website">
  <meta property="og:locale" content="zh_TW">
  <meta property="og:site_name" content="StockmarketAgent">
  <meta property="og:title" content="{_e(title)}">
  <meta property="og:description" content="{_e(description)}">
  <meta property="og:url" content="{_e(canonical)}">
  <meta name="twitter:title" content="{_e(title)}">
  <meta name="twitter:description" content="{_e(description)}">
  {image}
  <link rel="canonical" href="{_e(canonical)}">
  <link rel="stylesheet" href="{prefix}assets/css/site.css">
  <title>{_e(title)}</title>
</head>"""


def _nav(prefix: str, current: str) -> str:
    links = [
        ("home", f"{prefix}index.html", "總覽"),
        ("tw", f"{prefix}markets/tw.html", "台灣"),
        ("jp", f"{prefix}markets/jp.html", "日本"),
        ("us", f"{prefix}markets/us.html", "美國"),
        ("methodology", f"{prefix}methodology.html", "方法"),
        ("review", f"{prefix}universe-review.html", "審查"),
        ("sources", f"{prefix}source-feasibility.html", "來源"),
        ("status", f"{prefix}status.html", "狀態"),
        ("history", f"{prefix}history.html", "歷史"),
    ]
    rendered = []
    for key, href, label in links:
        active = ' aria-current="page"' if key == current else ""
        rendered.append(f'<a href="{href}"{active}>{label}</a>')
    items = "".join(rendered)
    return f"""<nav class="site-nav" aria-label="主要導覽">
  <div class="shell nav-inner">
    <a class="brand" href="{prefix}index.html" aria-label="StockmarketAgent 首頁">
      <span aria-hidden="true">SA</span><strong>StockmarketAgent</strong>
    </a>
    <div class="nav-links">{items}</div>
  </div>
</nav>"""


def _footer(prefix: str) -> str:
    return f"""<footer class="site-footer">
  <div class="shell footer-grid">
    <div><strong>StockmarketAgent</strong><p>Evidence before direction.</p></div>
    <p>Fixture research preview · <a href="{prefix}methodology.html">非個人化投資建議</a> · <a href="{REPOSITORY_URL}">GitHub repository</a></p>
  </div>
</footer>"""


def _layout(
    *,
    title: str,
    description: str,
    body: str,
    prefix: str = "",
    current: str = "home",
    canonical_path: str = "",
    root_social_card: bool = False,
) -> str:
    return (
        _head(
            title=title,
            description=description,
            prefix=prefix,
            canonical_path=canonical_path,
            root_social_card=root_social_card,
        )
        + "<body>"
        + _nav(prefix, current)
        + body
        + _footer(prefix)
        + f'<script src="{prefix}assets/js/app.js" defer></script>'
        + "</body></html>"
    )


def _theme_badges(themes: list[str]) -> str:
    return "".join(
        f'<span class="tag">{_e(THEME_NAMES.get(theme, theme))}</span>'
        for theme in themes
    )


def _stance_badge(stance: str) -> str:
    icons = {"BUY": "↑", "HOLD": "—", "SELL": "↓", "NO_SIGNAL": "○"}
    css_name = stance.lower().replace("_", "-")
    return (
        f'<span class="stance stance-{css_name}">'
        f'<span aria-hidden="true">{icons[stance]}</span> {stance}</span>'
    )


def _instrument_rows(instruments: list[dict[str, Any]], prefix: str) -> str:
    rows = []
    for item in instruments:
        horizon = item["horizons"][2]
        themes = " ".join(item["themes"])
        search_text = f"{item['symbol']} {item['name_zh']} {item['name_en']}".lower()
        rows.append(
            f"""<tr data-instrument
              data-country="{_e(item['country'])}"
              data-asset="{_e(item['asset_type'])}"
              data-stance="{_e(horizon['stance'])}"
              data-themes="{_e(themes)}"
              data-search="{_e(search_text)}">
  <td><a class="instrument-link" href="{prefix}instruments/{_e(item['slug'])}.html"><strong>{_e(item['symbol'])}</strong><span>{_e(item['name_zh'])}</span></a></td>
  <td>{_e(MARKET_NAMES[item['country']])}</td>
  <td>{_e(ASSET_NAMES[item['asset_type']])}</td>
  <td><div class="tag-row">{_theme_badges(item['themes'][:3])}</div></td>
  <td>{_stance_badge(horizon['stance'])}</td>
  <td class="num">{horizon['confidence']}</td>
</tr>"""
        )
    return "".join(rows)


def render_home(
    signal: dict[str, Any], review: dict[str, Any], sources: dict[str, Any]
) -> str:
    run = signal["run"]
    summary = signal["summary"]
    review_counts = {
        "verified": len(review["instruments"]),
        "tracking_indices": sum(
            1 for item in review["instruments"] if "tracking_index" in item
        ),
        "sources": len(sources["sources"]),
        "overlaps": len(review["overlap_groups"]),
        "limited_history": sum(
            1
            for item in review["instruments"]
            if item["history"]["live_age_status"] == "limited"
        ),
        "owner_decisions": len(review["owner_decisions"]),
    }
    review_cards = "".join(
        f"""<article class="metric-card">
  <span>{_e(label)}</span><strong>{review_counts[key]}</strong><small>{_e(note)}</small>
</article>"""
        for key, label, note in (
            ("verified", "已審查標的", "全部維持 proposed"),
            ("tracking_indices", "ETF tracking index", "與投資組合基準分離"),
            ("sources", "來源紀錄", "含授權與 Pages policy"),
            ("overlaps", "重疊群組", "等待集中度門檻"),
            ("limited_history", "短 live history", "00919、00965"),
            ("owner_decisions", "Owner decisions", "正式啟用前必須決定"),
        )
    )
    stance_cards = "".join(
        f"""<article class="metric-card">
  <span>{stance}</span><strong>{summary['stances'][stance]}</strong>
  <small>{'Risk Gate' if stance == 'NO_SIGNAL' else '已停用'}</small>
</article>"""
        for stance in ("BUY", "HOLD", "SELL", "NO_SIGNAL")
    )
    market_cards = "".join(
        f"""<a class="market-card" href="markets/{market['country'].lower()}.html">
  <span class="market-code">{market['country']}</span>
  <div><h3>{_e(market['name_zh'])}市場</h3><p>{_e(market['notice'])}</p></div>
  <strong>{market['instrument_count']} <small>proposed</small></strong>
</a>"""
        for market in signal["markets"]
    )
    events = "".join(
        f"""<article class="event-card">
  <div><span class="priority">P{event['priority']}</span><span class="tag">{_e(event['event_type'])}</span></div>
  <h3>{_e(event['title'])}</h3><p>{_e(event['summary'])}</p>
</article>"""
        for event in signal["events"]
    )
    themes = sorted({theme for item in signal["instruments"] for theme in item["themes"]})
    theme_options = "".join(
        f'<option value="{_e(theme)}">{_e(THEME_NAMES.get(theme, theme))}</option>'
        for theme in themes
    )
    body = f"""
<header class="hero">
  <div class="shell hero-grid">
    <div>
      <p class="eyebrow">TRI-MARKET RESEARCH INTELLIGENCE</p>
      <h1>三個市場，一套可追溯的研究語言。</h1>
      <p class="hero-copy">把台灣、日本、美國的候選標的放進同一個資料品質、證據與 Risk Gate 框架。這是固定 fixture 的公開工程預覽，不是即時行情。</p>
      <div class="hero-actions">
        <a class="button button-primary" href="#universe">檢視候選標的</a>
        <a class="button button-ghost" href="methodology.html">了解方法與限制</a>
      </div>
    </div>
    <aside class="mode-card" aria-label="目前執行模式">
      <div><span class="status-dot" aria-hidden="true"></span><p>PUBLIC PREVIEW</p></div>
      <strong>RESEARCH ONLY</strong>
      <small>Fixture data · Owner approval required</small>
    </aside>
  </div>
</header>
<main class="shell main-content">
  <section class="status-strip" aria-label="資料狀態">
    <div><span>最新成功執行</span><strong>{_e(run['generated_at'])}</strong></div>
    <div><span>資料型態</span><strong>Fixed fixture</strong></div>
    <div><span>正式核准標的</span><strong>{summary['approved_enabled_count']} / 30</strong></div>
    <div><span>方向性訊號</span><strong>已關閉</strong></div>
  </section>
  <section class="section-card" id="evidence-review">
    <div class="section-heading">
      <div><p class="kicker">EVIDENCE REVIEW · {_e(review['evidence_as_of'])}</p><h2>部署版本可閱讀的查證資料</h2></div>
      <span class="pill pill-neutral">owner decision required</span>
    </div>
    <p class="lead">30 檔候選的身分、歷史、流動性、tracking index、重疊與模型適用性已公開；這些是審查資料，不是即時行情或投資訊號。</p>
    <div class="metric-grid">{review_cards}</div>
    <div class="hero-actions">
      <a class="button button-primary" href="universe-review.html">閱讀 30 檔證據審查</a>
      <a class="button button-ghost" href="source-feasibility.html">查看來源可行性</a>
    </div>
    <div class="notice" role="note"><strong>安全邊界仍啟用</strong><span>所有標的維持 proposed / disabled；live adapters 與 BUY／SELL 均未啟用。</span></div>
  </section>
  <section class="section-card">
    <div class="section-heading">
      <div><p class="kicker">SIGNAL GATE</p><h2>研究態度分布</h2></div>
      <span class="pill pill-neutral">模型尚未校準</span>
    </div>
    <div class="metric-grid">{stance_cards}</div>
    <div class="notice" role="note"><strong>為什麼全部是 NO_SIGNAL？</strong><span>Universe 尚未核准、live sources 尚未啟用、模型尚未完成回測。Risk Gate 因此禁止方向性結論。</span></div>
  </section>
  <section class="section-card">
    <div class="section-heading">
      <div><p class="kicker">MARKET STATUS</p><h2>跨市場狀態</h2></div>
      <a class="text-link" href="status.html">完整資料狀態 →</a>
    </div>
    <div class="market-grid">{market_cards}</div>
  </section>
  <section class="section-card">
    <div class="section-heading">
      <div><p class="kicker">PRIORITY QUEUE</p><h2>先處理證據缺口</h2></div>
      <span class="pill pill-risk">{summary['critical_events']} high materiality</span>
    </div>
    <div class="event-grid">{events}</div>
  </section>
  <section class="section-card" id="universe">
    <div class="section-heading">
      <div><p class="kicker">PROPOSED UNIVERSE</p><h2>30 個候選標的</h2></div>
      <span class="pill pill-neutral">全部 proposed · disabled</span>
    </div>
    <form class="filters" data-filter-form>
      <label><span>搜尋</span><input type="search" name="search" placeholder="代號或名稱" autocomplete="off"></label>
      <label><span>市場</span><select name="country"><option value="">全部市場</option><option value="TW">台灣</option><option value="JP">日本</option><option value="US">美國</option></select></label>
      <label><span>資產</span><select name="asset"><option value="">全部類型</option><option value="stock">個股</option><option value="etf">ETF</option></select></label>
      <label><span>主題</span><select name="theme"><option value="">全部主題</option>{theme_options}</select></label>
      <button type="reset" class="button button-muted">清除</button>
    </form>
    <p class="result-count" aria-live="polite"><strong data-result-count>30</strong> 個候選符合條件</p>
    <noscript><div class="notice"><strong>JavaScript 已停用。</strong><span>完整 30 筆表格仍可閱讀；篩選功能需要 JavaScript。</span></div></noscript>
    <div class="table-wrap">
      <table>
        <thead><tr><th>標的</th><th>市場</th><th>類型</th><th>主題</th><th>3M 態度</th><th class="num">信心</th></tr></thead>
        <tbody data-instrument-body>{_instrument_rows(signal['instruments'], '')}</tbody>
      </table>
    </div>
  </section>
  <section class="disclaimer" aria-label="重要聲明">
    <p class="kicker">RESEARCH BOUNDARY</p>
    <h2>證據先於方向。</h2>
    <p>本網站不提供個人化投資建議、下單或保證報酬。公開 fixture 只用來證明 JSON → Markdown → HTML 的一致性與發布流程。</p>
  </section>
</main>"""
    return _layout(
        title="StockmarketAgent｜三市場股票研究情報",
        description="台灣、日本、美國三市場的可追溯研究情報與 Risk Gate 儀表板。首版為 research-only fixture。",
        body=body,
        current="home",
        canonical_path="",
        root_social_card=True,
    )


def render_market(signal: dict[str, Any], country: str) -> str:
    market = next(item for item in signal["markets"] if item["country"] == country)
    instruments = [item for item in signal["instruments"] if item["country"] == country]
    name = MARKET_NAMES[country]
    body = f"""
<header class="subhero">
  <div class="shell">
    <p class="eyebrow">{country} MARKET · RESEARCH ONLY</p>
    <h1>{name}市場候選清單</h1>
    <p>{_e(market['notice'])}</p>
    <div class="subhero-meta"><span>狀態：{_e(market['status'])}</span><span>標的：{len(instruments)}</span><span>正式核准：0</span></div>
  </div>
</header>
<main class="shell main-content">
  <section class="section-card">
    <div class="section-heading"><div><p class="kicker">MARKET UNIVERSE</p><h2>5 個股 + 5 ETF</h2></div>{_stance_badge('NO_SIGNAL')}</div>
    <div class="notice" role="note"><strong>目前沒有市場日期。</strong><span>這是 fixture 頁面；live adapter 啟用前不會顯示行情或推導新鮮度。</span></div>
    <div class="table-wrap">
      <table>
        <thead><tr><th>標的</th><th>市場</th><th>類型</th><th>主題</th><th>3M 態度</th><th class="num">信心</th></tr></thead>
        <tbody>{_instrument_rows(instruments, '../')}</tbody>
      </table>
    </div>
  </section>
</main>"""
    return _layout(
        title=f"{name}市場｜StockmarketAgent",
        description=f"{name}市場 5 個股與 5 ETF 候選清單；全部為 proposed、research-only。",
        body=body,
        prefix="../",
        current=country.lower(),
        canonical_path=f"markets/{country.lower()}.html",
    )


def render_instrument(signal: dict[str, Any], item: dict[str, Any], review_item: dict[str, Any]) -> str:
    horizon_cards = "".join(
        f"""<article class="horizon-card">
  <span>{entry['horizon']}</span>{_stance_badge(entry['stance'])}
  <div><strong>—</strong><small>score</small></div>
  <p>confidence {entry['confidence']} · {entry['calibration_status']}</p>
</article>"""
        for entry in item["horizons"]
    )
    component_cards = "".join(
        f"""<article class="component-card">
  <span>{_e(label)}</span><strong>未評估</strong><small>{_e(item['components'][key]['status'])}</small>
</article>"""
        for key, label in (
            ("macro", "總體"),
            ("fundamental", "基本面"),
            ("valuation", "估值"),
            ("technical", "技術"),
            ("cycle", "循環"),
            ("events", "事件"),
        )
    )
    risks = "".join(
        f"<li>{_e(flag)}</li>" for flag in item["horizons"][2]["risk_flags"]
    )
    body = f"""
<header class="subhero instrument-hero">
  <div class="shell">
    <a class="back-link" href="../markets/{item['country'].lower()}.html">← 返回{MARKET_NAMES[item['country']]}市場</a>
    <div class="instrument-title">
      <div><p class="eyebrow">{_e(item['country'])} · {_e(item['asset_type'].upper())} · {_e(item['market'])}</p><h1>{_e(item['symbol'])} <span>{_e(item['name_zh'])}</span></h1><p>{_e(item['name_en'])}</p></div>
      {_stance_badge('NO_SIGNAL')}
    </div>
    <div class="tag-row">{_theme_badges(item['themes'])}</div>
  </div>
</header>
<main class="shell main-content">
  <section class="section-card">
    <div class="section-heading"><div><p class="kicker">MULTI-HORIZON</p><h2>期間研究態度</h2></div><span class="pill pill-neutral">資料未就緒</span></div>
    <div class="horizon-grid">{horizon_cards}</div>
  </section>
  <section class="section-card">
    <div class="section-heading"><div><p class="kicker">MODEL COMPONENTS</p><h2>六個研究元件</h2></div><span class="pill pill-neutral">不以空值假裝 0 分</span></div>
    <div class="component-grid">{component_cards}</div>
  </section>
  <section class="split-grid">
    <article class="section-card">
      <p class="kicker">RISK GATE</p><h2>阻擋條件</h2>
      <ul class="risk-list">{risks}</ul>
    </article>
    <article class="section-card">
      <p class="kicker">APPLICABILITY</p><h2>模型適用性</h2>
      <p class="lead">{_e(item['model_applicability']['reason'])}</p>
      <dl class="fact-list"><div><dt>狀態</dt><dd>{_e(item['status'])}</dd></div><div><dt>啟用</dt><dd>{str(item['enabled']).lower()}</dd></div><div><dt>幣別</dt><dd>{_e(item['currency'])}</dd></div><div><dt>基準</dt><dd>{_e(item['benchmark_id'])}</dd></div></dl>
    </article>
  </section>
  <section class="section-card">
    <p class="kicker">EVIDENCE</p><h2>證據與來源</h2>
    <p><strong>選取理由：</strong>{_e(review_item['selection_rationale'])}</p>
    <p><strong>身分：</strong>{_e(review_item['verification_status'])} · <a href="{_e(review_item['official_url'])}">官方頁面</a></p>
    <p><strong>歷史：</strong>live age {_e(review_item['history']['live_age_status'])}；可用 PIT 歷史 {_e(review_item['history']['usable_history_status'])}。{_e(review_item['history']['usable_history_note'])}</p>
    <p><strong>流動性：</strong>{_e(review_item['liquidity']['status'])}。{_e(review_item['liquidity']['note'])}</p>
    <ul class="risk-list">{''.join(f'<li>{_e(name)}: {_e(value["status"])} — {_e(value["reason"])}</li>' for name, value in review_item['models'].items())}</ul>
    <p>{' · '.join(f'<a href="{_e(ref["url"])}">{_e(ref["source_id"])}</a>' for ref in review_item['evidence'])}</p>
  </section>
</main>"""
    return _layout(
        title=f"{item['symbol']} {item['name_zh']}｜StockmarketAgent",
        description=f"{item['symbol']} {item['name_zh']} 的 research-only 研究頁；目前為 proposed fixture，方向性訊號關閉。",
        body=body,
        prefix="../",
        canonical_path=f"instruments/{item['slug']}.html",
    )


def render_methodology(signal: dict[str, Any]) -> str:
    body = """
<header class="subhero"><div class="shell"><p class="eyebrow">METHODOLOGY</p><h1>先證明資料，再討論方向。</h1><p>Renderer 只讀取已驗證 JSON；它不在 HTML 或瀏覽器內重算研究分數。</p></div></header>
<main class="shell main-content">
  <section class="section-card">
    <p class="kicker">PIPELINE</p><h2>可重現的七道關卡</h2>
    <ol class="process">
      <li><span>01</span><div><strong>Source policy</strong><p>官方、授權或明確允許的來源優先。</p></div></li>
      <li><span>02</span><div><strong>Normalization</strong><p>日期、幣別、單位與公司行動分層處理。</p></div></li>
      <li><span>03</span><div><strong>Point-in-time features</strong><p>只使用當時已公開的資料，避免前視偏誤。</p></div></li>
      <li><span>04</span><div><strong>Deterministic model</strong><p>權重與門檻版本化；LLM 不決定數值或態度。</p></div></li>
      <li><span>05</span><div><strong>Risk Gate</strong><p>缺資料、過期、矛盾或未校準時強制 NO_SIGNAL。</p></div></li>
      <li><span>06</span><div><strong>Strict JSON</strong><p>拒絕未定義欄位、NaN、Infinity 與不合法日期。</p></div></li>
      <li><span>07</span><div><strong>Derived outputs</strong><p>同一份 JSON 產生 Markdown 與靜態 HTML。</p></div></li>
    </ol>
  </section>
  <section class="split-grid">
    <article class="section-card"><p class="kicker">STANCE</p><h2>四種研究態度</h2><dl class="definition-list"><div><dt>BUY</dt><dd>經校準後的買入傾向。</dd></div><div><dt>HOLD</dt><dd>方向不足或風險報酬中性。</dd></div><div><dt>SELL</dt><dd>經校準後的減碼傾向。</dd></div><div><dt>NO_SIGNAL</dt><dd>資料或模型條件不允許方向性結論。</dd></div></dl></article>
    <article class="section-card"><p class="kicker">PUBLIC MVP</p><h2>目前刻意不做</h2><ul class="risk-list"><li>即時行情與新聞抓取</li><li>正式 Universe 核准</li><li>回測、校準與 p_outperform</li><li>個人化建議或自動下單</li><li>自動調權與模型自我修改</li></ul></article>
  </section>
  <section class="disclaimer"><p class="kicker">IMPORTANT</p><h2>非個人化投資建議。</h2><p>分數與態度是版本化研究模型的輸出，不等於獲利機率，也不能取代個人的財務、稅務或風險評估。</p></section>
</main>"""
    return _layout(
        title="研究方法與限制｜StockmarketAgent",
        description="StockmarketAgent 的資料、模型、Risk Gate、NO_SIGNAL 與公開限制。",
        body=body,
        current="methodology",
        canonical_path="methodology.html",
        root_social_card=True,
    )


def render_status(signal: dict[str, Any]) -> str:
    market_rows = "".join(
        f"<tr><td>{_e(item['name_zh'])}</td><td>{_e(item['status'])}</td><td>{_e(item['last_market_session'] or '未提供')}</td><td>{_e(item['notice'])}</td></tr>"
        for item in signal["markets"]
    )
    event_rows = "".join(
        f"<tr><td>{event['priority']}</td><td>{_e(event['event_type'])}</td><td>{_e(event['title'])}</td><td>{_e(event['summary'])}</td></tr>"
        for event in signal["events"]
    )
    body = f"""
<header class="subhero"><div class="shell"><p class="eyebrow">SYSTEM STATUS</p><h1>每一個缺口都應該可見。</h1><p>目前成功產生 fixture 版本；這不代表 live sources、模型或市場資料已就緒。</p></div></header>
<main class="shell main-content">
  <section class="status-strip status-strip-flat"><div><span>Run</span><strong>{_e(signal['run']['run_id'])}</strong></div><div><span>Mode</span><strong>{_e(signal['run']['mode'])}</strong></div><div><span>Data</span><strong>{_e(signal['run']['data_kind'])}</strong></div><div><span>Critical</span><strong>{signal['summary']['critical_events']}</strong></div></section>
  <section class="section-card"><p class="kicker">MARKETS</p><h2>市場資料狀態</h2><div class="table-wrap"><table><thead><tr><th>市場</th><th>狀態</th><th>交易日</th><th>說明</th></tr></thead><tbody>{market_rows}</tbody></table></div></section>
  <section class="section-card"><p class="kicker">EVENTS</p><h2>高優先缺口</h2><div class="table-wrap"><table><thead><tr><th>Priority</th><th>類型</th><th>事件</th><th>說明</th></tr></thead><tbody>{event_rows}</tbody></table></div></section>
  <section class="section-card"><p class="kicker">SOURCE MANIFEST</p><h2>來源清單</h2><div class="code-block"><code>{_e(signal['source_manifest'][0]['path'])}</code><span>sha256:{_e(signal['source_manifest'][0]['content_hash'])}</span></div></section>
</main>"""
    return _layout(
        title="資料與執行狀態｜StockmarketAgent",
        description="StockmarketAgent 的市場資料狀態、執行紀錄、錯誤與來源清單。",
        body=body,
        current="status",
        canonical_path="status.html",
        root_social_card=True,
    )


def render_history(signals: list[dict[str, Any]]) -> str:
    rows = "".join(
        f"""<tr>
  <td>{_e(signal['run']['as_of'])}</td>
  <td><code>{_e(signal['run']['run_id'])}</code></td>
  <td>{_e(signal['run']['mode'])}</td>
  <td>{_e(signal['run']['data_kind'])}</td>
  <td><a href="data/archive/{_e(signal['run']['as_of'])}.json">JSON</a> · <a href="{REPOSITORY_URL}/blob/main/reports/archive/{_e(signal['run']['as_of'])}.md">Markdown</a></td>
</tr>"""
        for signal in signals
    )
    body = f"""
<header class="subhero"><div class="shell"><p class="eyebrow">RUN HISTORY</p><h1>最新與歷史同時保留。</h1><p>每次成功產生都保存 JSON、Markdown 與 Agent Run record；不以空結果覆蓋 last-known-good。</p></div></header>
<main class="shell main-content">
  <section class="section-card"><p class="kicker">AVAILABLE SNAPSHOTS</p><h2>研究快照</h2><div class="table-wrap"><table><thead><tr><th>日期</th><th>Run ID</th><th>模式</th><th>資料</th><th>輸出</th></tr></thead><tbody>{rows}</tbody></table></div></section>
</main>"""
    return _layout(
        title="執行歷史｜StockmarketAgent",
        description="StockmarketAgent 的可重現研究快照與歷史執行紀錄。",
        body=body,
        current="history",
        canonical_path="history.html",
        root_social_card=True,
    )


def render_not_found() -> str:
    body = f"""
<main class="shell not-found"><p class="eyebrow">404</p><h1>找不到這個研究頁。</h1><p>標的可能尚未納入候選 Universe，或連結已更新。</p><a class="button button-primary" href="{SITE_URL}">返回總覽</a></main>"""
    return _layout(
        title="找不到頁面｜StockmarketAgent",
        description="找不到要求的 StockmarketAgent 頁面。",
        body=body,
        canonical_path="404.html",
    )


def render_universe_review(review: dict[str, Any]) -> str:
    rows = "".join(
        f"<tr><td><code>{_e(item['instrument_id'])}</code></td><td>{_e(item['verification_status'])}</td><td>{_e(item['history']['live_age_status'])}</td><td>{_e(item['history']['usable_history_status'])}</td><td>{_e(item['liquidity']['status'])}</td><td>{_e(item['replacement_assessment'])}</td></tr>"
        for item in review["instruments"]
    )
    detail_parts = []
    for item in review["instruments"]:
        model_text = "；".join(
            f"{_e(name)}={_e(value['status'])}（{_e(value['reason'])}）"
            for name, value in item["models"].items()
        )
        evidence_links = " · ".join(
            f'<a href="{_e(ref["url"])}">{_e(ref["source_id"])}</a>'
            for ref in item["evidence"]
        )
        detail_parts.append(
            f"<article class='section-card'><p class='kicker'>{_e(item['instrument_id'])}</p>"
            f"<h2>{_e(item['legal_name'])}</h2><p><strong>選取理由：</strong>{_e(item['selection_rationale'])}</p>"
            f"<p><strong>模型：</strong>{model_text}</p><p>{evidence_links}</p></article>"
        )
    details = "".join(detail_parts)
    overlap = "".join(f"<li><strong>{_e(item['overlap_id'])}</strong> ({_e(item['severity'])}) — {_e(item['basis'])} <a href='{_e(item['evidence'][0]['url'])}'>evidence</a></li>" for item in review["overlap_groups"])
    concentration = "".join(f"<li><strong>{_e(item['country'])} {_e(item['issuer'])}</strong> — {_e(item['share_of_market_etfs'])}. {_e(item['assessment'])} <a href='{_e(item['evidence'][0]['url'])}'>evidence</a></li>" for item in review["issuer_concentration"])
    decisions = "".join(f"<li><strong>{_e(item['decision_id'])}</strong> — {_e(item['question'])} Gap: {_e(item['evidence_gap'])}</li>" for item in review["owner_decisions"])
    body = f"""<header class="subhero"><div class="shell"><p class="eyebrow">B.1 EVIDENCE REVIEW</p><h1>30 檔候選逐筆查證</h1><p>Review {_e(review['review_version'])} · evidence as of {_e(review['evidence_as_of'])} · owner decision required</p></div></header><main class="shell main-content"><section class="section-card"><p>所有候選仍為 proposed / disabled；此頁不包含 live adapter、方向性訊號或受限來源數值。</p><div class="table-wrap"><table><thead><tr><th>ID</th><th>身分</th><th>Live age</th><th>可用 PIT history</th><th>流動性</th><th>替代評估</th></tr></thead><tbody>{rows}</tbody></table></div></section><section class="section-card"><h2>重疊證據</h2><ul class="risk-list">{overlap}</ul><h2>ETF 發行人集中</h2><ul class="risk-list">{concentration}</ul><h2>Owner decisions</h2><ul class="risk-list">{decisions}</ul></section>{details}</main>"""
    return _layout(title="Universe evidence review｜StockmarketAgent", description="30 檔候選的身分、歷史、流動性、重疊、發行人與模型適用性查證。", body=body, current="review", canonical_path="universe-review.html", root_social_card=True)


def render_source_feasibility(sources: dict[str, Any]) -> str:
    rows = "".join(f"<tr><td><a href='{_e(item['documentation_url'])}'>{_e(item['source_id'])}</a></td><td>{_e(', '.join(item['countries']))}</td><td>{_e(', '.join(item['data_classes']))}</td><td>{_e(item['authentication'])} / {_e(item['key_required'])}</td><td>{_e(item['point_in_time_status'])}</td><td><a href='{_e(item['license_url'])}'>{_e(item['license_status'])}</a> / {_e(item['pages_policy'])}</td><td>{_e(item['feasibility'])}</td></tr>" for item in sources["sources"])
    details = "".join(f"<article class='section-card'><p class='kicker'>{_e(item['source_id'])}</p><h2>{_e(item['publisher'])}</h2><p><strong>Limits:</strong> {_e(item['rate_limit'])}</p><p><strong>History:</strong> {_e(item['history_depth'])}</p><p><strong>Retention:</strong> {_e(item['retention'])}</p><p><strong>Redistribution:</strong> {_e(item['redistribution'])}</p><p><strong>Fallback:</strong> {_e(item['fallback'])}</p><p><strong>Gaps:</strong> {_e('; '.join(item['gaps']))}</p></article>" for item in sources["sources"])
    body = f"""<header class="subhero"><div class="shell"><p class="eyebrow">SOURCE FEASIBILITY</p><h1>來源、授權與發布邊界</h1><p>Reviewed {_e(sources['reviewed_at'])} · live adapters disabled</p></div></header><main class="shell main-content"><section class="section-card"><p>{_e(sources['publication_boundary'])}</p><div class="table-wrap"><table><thead><tr><th>來源</th><th>市場</th><th>資料類別</th><th>Auth / key</th><th>PIT</th><th>授權 / Pages</th><th>可行性</th></tr></thead><tbody>{rows}</tbody></table></div></section>{details}</main>"""
    return _layout(title="Source feasibility｜StockmarketAgent", description="三市場官方資料來源的驗證、授權、PIT、保留、再發布與 fallback 矩陣。", body=body, current="sources", canonical_path="source-feasibility.html", root_social_card=True)
