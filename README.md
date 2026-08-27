# StockmarketAgent

[公開儀表板](https://trionnemesis.github.io/StockmarketAgent/) · [Universe 證據審查](https://trionnemesis.github.io/StockmarketAgent/universe-review.html) · [來源可行性](https://trionnemesis.github.io/StockmarketAgent/source-feasibility.html) · [研究方法](https://trionnemesis.github.io/StockmarketAgent/methodology.html) · [資料狀態](https://trionnemesis.github.io/StockmarketAgent/status.html)

台灣、日本、美國三市場的可追溯股票研究情報系統。Repository 以嚴格 JSON 為唯一事實來源，再由同一份已驗證資料產生 Markdown 與 GitHub Pages 靜態 HTML。

> 目前是 research-only fixture MVP。30 個標的全部為 proposed、disabled；live sources、模型校準與正式 BUY／SELL 均未啟用。內容不是個人化投資建議。

![StockmarketAgent social preview](docs/assets/og.png)

## 目前完成

- 台／日／美各 5 個股 + 5 ETF，共 30 個候選標的。
- Owner approval gate；未核准標的不會進入 production signal。
- Universe、Signal、Event、Agent Run 的 strict JSON Schema。
- 固定 fixture 的 JSON → Markdown → HTML 端到端流程。
- 首頁、三個市場頁、30 個標的頁、方法、狀態與歷史頁。
- Responsive、keyboard focus、文字 + 圖示訊號、可水平捲動表格與 no-JavaScript fallback。
- Latest + archive 輸出、fixture provenance、Agent Run record 與 staged rollback-aware 寫入。
- 零 Python 第三方依賴的 contract、integration、link、consistency 與 secret-pattern tests。
- GitHub Actions quality gate 與 GitHub Pages deployment。

## B.1 Universe evidence review

30 個候選已逐筆以官方發行人、交易所、監管機關或指數提供者頁面查證。結果仍是「owner decision required」，不是 Universe 核准：

- 30 / 30 已確認 active listing、代號、交易場所、交易幣別與資產類型；其中 9 筆名稱、交易所或主題 metadata 經修正。
- 15 / 15 ETF 的實際 tracking index 已獨立保存，不與市場績效 benchmark 混用。
- 00919 與 00965 的 live age 未滿五年；其餘標示為 sufficient 只代表上市／基金年齡，不代表已取得同長度的可用 point-in-time 歷史。
- 30 / 30 流動性仍為 `quantitative_review_pending`；成交額、價差與容量不能由目前公開 reference metadata 推導。
- 找出 6 組明確重疊，以及台灣 Yuanta 2/5、日本 Nomura 3/5、美國無重複 ETF issuer 的候選集中情形。
- H-model、reverse DCF、ETF look-through 與 cobweb model 已逐檔標示 conditional / not applicable 及理由；尚未回測或啟用。

機器可讀事實來源為 [`config/universe-review.json`](config/universe-review.json)、[`config/sources.json`](config/sources.json) 與相對應 strict schemas；人類可讀輸出為 [`docs/universe-review.md`](docs/universe-review.md) 與 [`docs/source-feasibility.md`](docs/source-feasibility.md)。

### Owner 尚需決定

1. 接受本次 metadata / theme corrections。
2. 是否在 0050 / 006208 與 1306 / 1475 各只保留一個重複 index wrapper。
3. 是否允許 live history 未滿五年的 00919、00965。
4. 三市場 benchmark 的精確 price / total-return / net-return series。
5. Live、歷史、corporate actions、ETF holdings 與 benchmark 的資料授權／採購。
6. 最低成交額、最大價差、issuer concentration 與 look-through overlap 門檻。
7. 資產類型與產業別的模型 routing。

## 安全邊界

- 不抓 live market data；provider key 只允許由 GitHub Actions secret store 注入，絕不提交 repository 或送到瀏覽器。
- 不執行券商下單、自動交易或個人資產配置。
- 不以 LLM 決定價格、分數、信心或研究態度。
- 不用空值假裝 0 分；資料不足時強制 NO_SIGNAL。
- config/approvals.json 的 production_signal_enabled 預設且維持 false。

候選清單與核准條件見 [Universe proposal](docs/universe-proposal.md)，Owner 決策入口為 [Issue #1](https://github.com/trionnemesis/StockmarketAgent/issues/1)。完整產品契約見 [SPEC.md](SPEC.md)，參考資料的採用／排除邊界見 [references/README.md](references/README.md)，初次發布證據見 [VERIFICATION.md](VERIFICATION.md)。

## 本機執行

需要 Python 3.11+，不需安裝第三方套件。

    python3 -m src.pipeline build
    python3 -m unittest discover -s tests -p 'test_*.py' -v
    python3 -m http.server 8765 --directory docs

開啟 http://127.0.0.1:8765/。

## 資料流

    versioned config + fixed fixture
                  │
                  ▼
    strict JSON Schema + contracts
                  │
                  ▼
    research-only signal JSON
          ┌───────┼────────┐
          ▼       ▼        ▼
      Markdown   HTML   Agent Run
                  │
                  ▼
            GitHub Pages

Renderer 只讀取已驗證 JSON，不重算模型。相同 fixture、設定與程式版本會產生相同核心輸出。

本機 pipeline 會先完整 staging，並在可攔截錯誤時回復舊檔；它不宣稱能抵抗主機斷電等 process-termination crash。公開發布的原子邊界在 GitHub Pages：workflow 只有在 build 與全部測試通過後才上傳完整 artifact，失敗執行不會部署半套網站。

## Repository map

| Path | Responsibility |
|---|---|
| config/ | Universe、evidence review、benchmark、source、approval、schedule 與 model policy |
| schemas/ | Strict JSON contracts |
| src/validation/ | Zero-dependency schema and domain validation |
| src/render/ | Markdown and static HTML renderers |
| signals/, reports/ | Latest + archived research outputs |
| agent-runs/ | Reproducible execution records |
| docs/ | Generated GitHub Pages artifact |
| tests/fixtures/ | Fixed, non-live test inputs |
| .github/workflows/ | Quality and Pages deployment gates |

## 下一階段

正式資料功能必須拆成可審查變更：先由 Owner 回覆上述 7 個決策，再另開 PR 實作獲授權的 point-in-time adapter、last-known-good、回測與校準。本 PR 不包含 live adapter、排程、模型分數或 BUY／SELL；Owner 核准前 `production_signal_enabled` 維持 `false`。
