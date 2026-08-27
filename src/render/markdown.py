from __future__ import annotations

from typing import Any


MARKET_NAMES = {"TW": "台灣", "JP": "日本", "US": "美國"}


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
        "> 本報告使用固定 fixture 驗證資料契約與頁面產生流程，不是個人化投資建議。",
        "",
        "## 市場狀態",
        "",
        "| 市場 | 狀態 | 最新完成交易日 | 說明 |",
        "|---|---|---|---|",
    ]
    for market in signal["markets"]:
        lines.append(
            f"| {MARKET_NAMES[market['country']]} | {market['status']} | "
            f"{market['last_market_session'] or '未提供（fixture）'} | {market['notice']} |"
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
    for stance in ("BUY", "HOLD", "SELL", "NO_SIGNAL"):
        lines.append(f"| {stance} | {summary['stances'][stance]} |")

    lines.extend(
        [
            "",
            "## 候選標的",
            "",
            "| 市場 | 類型 | 代號 | 名稱 | 1W | 1M | 3M | 12M |",
            "|---|---|---|---|---|---|---|---|",
        ]
    )
    for item in signal["instruments"]:
        stances = [entry["stance"] for entry in item["horizons"]]
        lines.append(
            f"| {item['country']} | {item['asset_type']} | {item['symbol']} | "
            f"{item['name_zh']} | {' | '.join(stances)} |"
        )

    lines.extend(["", "## 高優先事件", ""])
    for event in signal["events"]:
        lines.append(f"- **{event['title']}**：{event['summary']}")

    lines.extend(
        [
            "",
            "## 限制",
            "",
            "- Live source adapters 尚未啟用。",
            "- Universe 全部為 proposed，等待 Owner 核准。",
            "- 模型尚未回測與校準。",
            "- 所有方向性輸出均由 Risk Gate 強制為 NO_SIGNAL。",
        ]
    )
    return "\n".join(lines)
