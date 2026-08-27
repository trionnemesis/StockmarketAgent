# StockmarketAgent

[公開儀表板](https://trionnemesis.github.io/StockmarketAgent/) · [研究方法](https://trionnemesis.github.io/StockmarketAgent/methodology.html) · [資料狀態](https://trionnemesis.github.io/StockmarketAgent/status.html)

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

## 安全邊界

- 不抓 live market data，不使用 provider key。
- 不執行券商下單、自動交易或個人資產配置。
- 不以 LLM 決定價格、分數、信心或研究態度。
- 不用空值假裝 0 分；資料不足時強制 NO_SIGNAL。
- config/approvals.json 的 production_signal_enabled 預設且維持 false。

候選清單與核准條件見 [Universe proposal](docs/universe-proposal.md)。完整產品契約見 [SPEC.md](SPEC.md)，參考資料的採用／排除邊界見 [references/README.md](references/README.md)。

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
| config/ | Universe、approval、source、schedule 與 model policy |
| schemas/ | Strict JSON contracts |
| src/validation/ | Zero-dependency schema and domain validation |
| src/render/ | Markdown and static HTML renderers |
| signals/, reports/ | Latest + archived research outputs |
| agent-runs/ | Reproducible execution records |
| docs/ | Generated GitHub Pages artifact |
| tests/fixtures/ | Fixed, non-live test inputs |
| .github/workflows/ | Quality and Pages deployment gates |

## 下一階段

正式資料功能必須拆成可審查變更：先核准 Universe，再逐一查證各市場官方來源、授權與速率限制，接著實作 point-in-time adapter、last-known-good、回測與校準。Owner 核准模型版本前，不會開啟 production BUY／SELL。
