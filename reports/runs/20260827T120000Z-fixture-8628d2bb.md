# StockmarketAgent 最新研究快照

- 執行時間：2026-08-27T12:00:00Z
- 資料日期：2026-08-27
- 模式：research_only
- 資料類型：fixture
- 追蹤候選：30
- 正式核准並啟用：0

> 本報告使用固定 fixture 驗證資料契約與頁面產生流程，不是個人化投資建議。

## 市場狀態

| 市場 | 狀態 | 最新完成交易日 | 說明 |
|---|---|---|---|
| 台灣 | fixture | 未提供（fixture） | 未連線市場資料；本頁僅驗證資料契約與呈現。 |
| 日本 | fixture | 未提供（fixture） | 未連線市場資料；本頁僅驗證資料契約與呈現。 |
| 美國 | fixture | 未提供（fixture） | 未連線市場資料；本頁僅驗證資料契約與呈現。 |

## 研究態度

| 態度 | 數量 |
|---|---:|
| BUY | 0 |
| HOLD | 0 |
| SELL | 0 |
| NO_SIGNAL | 30 |

## 候選標的

| 市場 | 類型 | 代號 | 名稱 | 1W | 1M | 3M | 12M |
|---|---|---|---|---|---|---|---|
| TW | stock | 2330 | 台積電 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | stock | 2454 | 聯發科 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | stock | 2308 | 台達電 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | stock | 2412 | 中華電信 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | stock | 2891 | 中信金 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | etf | 0050 | 元大台灣50 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | etf | 006208 | 富邦台50 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | etf | 00878 | 國泰永續高股息 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | etf | 00919 | 群益台灣精選高息 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| TW | etf | 00965 | 元大全球航太與防衛科技 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | stock | 7203 | 豐田汽車 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | stock | 6758 | 索尼集團 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | stock | 8035 | 東京威力科創 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | stock | 7011 | 三菱重工 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | stock | 9432 | 日本電信電話 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | etf | 1306 | NEXT FUNDS TOPIX連動型上市投資信託 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | etf | 1321 | NEXT FUNDS 日經225連動型上市投資信託 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | etf | 1475 | iShares Core TOPIX ETF | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | etf | 1489 | NEXT FUNDS 日經平均高股息股票50指數連動型上市投資信託 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| JP | etf | 2568 | 上場インデックスファンド米国株式 NASDAQ100 為替ヘッジなし | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | stock | NVDA | 輝達 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | stock | MSFT | 微軟 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | stock | GOOGL | Alphabet Inc. | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | stock | LMT | 洛克希德馬丁 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | stock | JNJ | 嬌生 | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | etf | SPY | SPDR S&P 500 ETF Trust | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | etf | QQQ | Invesco QQQ | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | etf | SMH | VanEck 半導體 ETF | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | etf | CIBR | First Trust NASDAQ Cybersecurity ETF | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |
| US | etf | USMV | iShares MSCI USA Min Vol Factor ETF | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL | NO_SIGNAL |

## 高優先事件

- **30 個候選標的等待 Owner 核准**：目前清單全部為 proposed 且 disabled；不會進入 production signal。
- **Live source adapters 尚未啟用**：行情、財報、新聞與 ETF 持股皆未抓取；Risk Gate 將所有期間輸出為 NO_SIGNAL。

## 限制

- Live source adapters 尚未啟用。
- Universe 全部為 proposed，等待 Owner 核准。
- 模型尚未回測與校準。
- 所有方向性輸出均由 Risk Gate 強制為 NO_SIGNAL。
