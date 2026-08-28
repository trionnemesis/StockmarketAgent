from __future__ import annotations

from typing import Any


MARKET_NAMES = {"TW": "台灣", "JP": "日本", "US": "美國"}
STANCE_ORDER = ("BUY", "HOLD", "SELL", "NO_SIGNAL")
COMPONENT_NAMES = {
    "macro": "總體",
    "fundamental": "基本面",
    "valuation": "估值",
    "technical": "技術",
    "cycle": "循環",
    "events": "事件",
}


def _score(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def _horizon(item: dict[str, Any], name: str) -> dict[str, Any]:
    return next(entry for entry in item["horizons"] if entry["horizon"] == name)


def _horizon_summary(entry: dict[str, Any]) -> str:
    return (
        f"{entry['stance']} / score {_score(entry['score'])} / "
        f"confidence {entry['confidence']} / {entry['calibration_status']}"
    )


def render_report(signal: dict[str, Any]) -> str:
    run = signal["run"]
    summary = signal["summary"]
    lines = [
        "# StockmarketAgent 最新研究快照",
        "",
        f"- 執行時間：{run['generated_at']}",
        f"- 資料日期：{run['as_of']}",
        f"- 模式：{run['mode']}",
        f"- 資料類型：{run['data_kind']}",
        f"- 追蹤候選：{summary['tracked_count']}",
        f"- 正式核准並啟用：{summary['approved_enabled_count']}",
        "",
        "> **研究模擬資料：** 本報告顯示 synthetic scenario fixture 與未校準研究態度；不含即時或當前市場事實，也不是投資建議。",
        "",
        "## 市場狀態",
        "",
        "| 市場 | 狀態 | 最新完成交易日 | 說明 |",
        "|---|---|---|---|",
    ]
    for market in signal["markets"]:
        lines.append(
            f"| {MARKET_NAMES[market['country']]} | {market['status']} | "
            f"{market['last_market_session'] or '未提供（research fixture）'} | {market['notice']} |"
        )

    lines.extend(
        [
            "",
            "## 研究態度",
            "",
            "| 態度 | 數量 |",
            "|---|---:|",
        ]
    )
    for stance in STANCE_ORDER:
        lines.append(f"| {stance} | {summary['stances'][stance]} |")

    lines.extend(
        [
            "",
            "## 候選標的",
            "",
            "以下每格依序顯示 `態度 / score / confidence / calibration`。",
            "",
            "| 市場 | 類型 | 代號 | 名稱 | 1W | 1M | 3M | 12M |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in signal["instruments"]:
        horizons = [
            _horizon_summary(_horizon(item, name))
            for name in ("1W", "1M", "3M", "12M")
        ]
        lines.append(
            f"| {item['country']} | {item['asset_type']} | {item['symbol']} | "
            f"{item['name_zh']} | {' | '.join(horizons)} |"
        )

    lines.extend(
        [
            "",
            "## 六個研究元件",
            "",
            "| 代號 | 元件 | Score | Confidence | Status |",
            "|---|---|---:|---:|---|",
        ]
    )
    for item in signal["instruments"]:
        for key, label in COMPONENT_NAMES.items():
            component = item["components"][key]
            lines.append(
                f"| {item['symbol']} | {label} | {_score(component['score'])} | "
                f"{component['confidence']} | {component['status']} |"
            )

    lines.extend(
        [
            "",
            "## 支持、反向證據與失效條件",
            "",
            "| 代號 | 期間 | 支持證據 | 反向證據 | 失效條件 |",
            "|---|---|---|---|---|",
        ]
    )
    for item in signal["instruments"]:
        for horizon in item["horizons"]:
            lines.append(
                f"| {item['symbol']} | {horizon['horizon']} | "
                f"{'；'.join(horizon['supporting_evidence']) or '無'} | "
                f"{'；'.join(horizon['contrary_evidence']) or '無'} | "
                f"{'；'.join(horizon['invalidation_conditions']) or '無'} |"
            )

    lines.extend(
        [
            "",
            "## Risk Gate 與資料狀態",
            "",
            "| 代號 | Data status | Risk flags（四期間聯集） |",
            "|---|---|---|",
        ]
    )
    for item in signal["instruments"]:
        flags = list(
            dict.fromkeys(
                flag
                for horizon in item["horizons"]
                for flag in horizon["risk_flags"]
            )
        )
        lines.append(
            f"| {item['symbol']} | {item['data_status']['status']} | "
            f"{', '.join(flags) or '無'} |"
        )

    lines.extend(["", "## 高優先事件", ""])
    for event in signal["events"]:
        lines.append(f"- **{event['title']}**：{event['summary']}")

    lines.extend(
        [
            "",
            "## 限制",
            "",
            "- 此 research fixture 不包含 live 市場事實；頁面不得稱為即時或當前市場分析。",
            "- Universe 全部為 proposed、disabled，等待 Owner 核准。",
            "- BUY／HOLD／SELL／NO_SIGNAL 是合成情境的未校準研究態度，不是可交易訊號。",
            "- Risk Gate 在條件不足時輸出 NO_SIGNAL；其他態度也不代表獲利機率或投資建議。",
        ]
    )
    return "\n".join(lines)


def render_universe_review(review: dict[str, Any]) -> str:
    lines = [
        "# Universe evidence review",
        "",
        f"- Review version: `{review['review_version']}`",
        f"- Evidence as of: `{review['evidence_as_of']}`",
        f"- Status: `{review['review_status']}`",
        "- Boundary: all 30 instruments remain `proposed` and `disabled`.",
        "",
        "## Instrument findings",
        "",
        "| ID | Identity | Live age | Usable PIT history | Liquidity | Replacement |",
        "|---|---|---|---|---|---|",
    ]
    for item in review["instruments"]:
        lines.append(
            f"| {item['instrument_id']} | {item['verification_status']} | {item['history']['live_age_status']} | "
            f"{item['history']['usable_history_status']} | {item['liquidity']['status']} | {item['replacement_assessment']} |"
        )
        lines.extend(["", f"**Selection rationale:** {item['selection_rationale']}", ""])
        lines.append("Model routing: " + "; ".join(f"{name}={value['status']} ({value['reason']})" for name, value in item["models"].items()))
        lines.append("Evidence: " + ", ".join(f"[{ref['source_id']}]({ref['url']})" for ref in item["evidence"]))
        lines.append("")
    lines.extend(["## Overlap findings", ""])
    for group in review["overlap_groups"]:
        links = ", ".join(f"[{ref['source_id']}]({ref['url']})" for ref in group["evidence"])
        lines.append(f"- **{group['overlap_id']} ({group['severity']})**: {group['basis']} Members: {', '.join(group['members'])}. Evidence: {links}")
    lines.extend(["", "## ETF issuer concentration", ""])
    for item in review["issuer_concentration"]:
        links = ", ".join(f"[{ref['source_id']}]({ref['url']})" for ref in item["evidence"])
        lines.append(f"- **{item['country']} — {item['issuer']}**: {item['share_of_market_etfs']}. {item['assessment']} Evidence: {links}")
    lines.extend(["", "## Owner decisions required", ""])
    for item in review["owner_decisions"]:
        lines.append(f"- **{item['decision_id']}**: {item['question']} Gap: {item['evidence_gap']}")
    return "\n".join(lines)


def render_source_feasibility(sources: dict[str, Any]) -> str:
    lines = [
        "# Source feasibility matrix",
        "",
        f"- Reviewed at: `{sources['reviewed_at']}`",
        f"- Live adapters enabled: `{str(sources['live_adapters_enabled']).lower()}`",
        f"- Publication boundary: {sources['publication_boundary']}",
        "",
        "## Providers",
        "",
        "| Source | Countries | Classes | Auth/key | PIT | License / Pages | Feasibility |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in sources["sources"]:
        lines.append(
            f"| [{item['source_id']}]({item['documentation_url']}) | {', '.join(item['countries'])} | {', '.join(item['data_classes'])} | "
            f"{item['authentication']} / {item['key_required']} | {item['point_in_time_status']} | "
            f"[{item['license_status']}]({item['license_url']}) / {item['pages_policy']} | {item['feasibility']} |"
        )
        lines.append(f"  - Limits: {item['rate_limit']} History: {item['history_depth']}")
        lines.append(f"  - Retention: {item['retention']} Redistribution: {item['redistribution']}")
        lines.append(f"  - Fallback: {item['fallback']} Gaps: {'; '.join(item['gaps'])}")
    lines.extend(["", "## Country / asset policies", ""])
    for policy in sources["policies"]:
        lines.append(f"### {policy['source_policy_id']} ({policy['country']} {policy['asset_type']})")
        lines.append("")
        for coverage in policy["coverage"]:
            refs = coverage["primary_source_ids"] + coverage["fallback_source_ids"]
            lines.append(f"- `{coverage['data_class']}` — **{coverage['status']}** — {', '.join(refs) or 'N/A'} — {coverage['note']}")
        lines.append("")
    return "\n".join(lines)
