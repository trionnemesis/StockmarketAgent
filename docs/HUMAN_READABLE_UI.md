# Human-readable analysis UI

StockmarketAgent 的公開 Pages 採「一般讀者優先、工程細節可追溯」的雙層呈現。

## 一般讀者預設看到的內容

個股與 ETF 詳細頁會先整理成白話分析摘要，直接回答：

- 目前約 3 個月的模擬研究看法是偏多、中性或偏空；
- 是否存在可用的即時買賣訊號；
- 官方資料日期與資料新鮮度；
- 官方資料是否已實際納入模型；
- 模擬情境中較正面與較需要留意的主要分析因素。

英文工程狀態與內部變數不再作為主要閱讀內容。常見顯示轉換包括：

| 工程語意 | 公開頁主要呈現 |
|---|---|
| `BUY` | 模擬情境偏多 |
| `HOLD` | 模擬情境中性 |
| `SELL` | 模擬情境偏空 |
| `NO_SIGNAL` | 目前沒有可用的即時買賣訊號 |
| `research_fixture` | 模擬研究資料 |
| `uncalibrated` | 尚未完成回測校準 |
| `Risk Gate` | 安全檢查／風險與限制 |
| `official_observation` | 官方市場資料 |

四個時間尺度顯示為「約 1 週、約 1 個月、約 3 個月、約 1 年」。六個模型構面顯示為「總體環境、公司基本面、估值合理性、價格趨勢、產業循環、事件影響」，並優先呈現偏正面／中性／偏負面，而不是直接要求使用者閱讀 raw score。

## 維護者仍可取得的技術資料

這項 UI 修正不修改 signal contract、model score、confidence、weight、threshold、official observation 或 production gate。原始技術值仍保留於：

- 頁面的 `data-*` attributes；
- strict JSON artifacts；
- 可展開的「維護者用原始技術值」區塊；
- immutable observation archive 與 provenance。

因此 human-readable UI 只是 presentation layer，不會改變分析結果或資料治理語意。
