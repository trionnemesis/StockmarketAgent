# Universe evidence review

- Review version: `b1-2026-08-27`
- Evidence as of: `2026-08-27`
- Status: `owner_decision_required`
- Boundary: all 30 instruments remain `proposed` and `disabled`.

## Instrument findings

| ID | Identity | Live age | Usable PIT history | Liquidity | Replacement |
|---|---|---|---|---|---|
| TW:STOCK:2330 | verified_after_correction | sufficient | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 大型半導體製造候選；需確認資料授權、流動性與主題集中度。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [TWSE_OGL_COMPANY](https://www.tsmc.com/english/aboutTSMC/company_profile)

| TW:STOCK:2454 | verified | sufficient | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** IC 設計候選；需驗證財報與產業循環資料可得性。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [TWSE_OGL_COMPANY](https://corp.mediatek.com/about)

| TW:STOCK:2308 | verified | sufficient | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 電源與基礎設施候選；需評估主題曝險與來源完整性。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_COMPANY](https://www.deltaww.com/en-US/about/aboutDelta)

| TW:STOCK:2412 | verified | sufficient | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 電信與股息候選；需確認股利與估值資料的 point-in-time 可得性。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_COMPANY](https://www.cht.com.tw/en/home/cht/about-cht/company-profile)

| TW:STOCK:2891 | verified | sufficient | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 金融與股息候選；需另定金融業適用模型。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_COMPANY](https://www.ctbcholding.com/en/en_abo_intro.html)

| TW:ETF:0050 | verified | sufficient | conditional | quantitative_review_pending | replacement_candidate |

**Selection rationale:** 大型股基準型 ETF 候選；需核對持股歷史與費用。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_ETF](https://www.yuantaetfs.com/product/detail/0050/Basic_information), [FTSE_TWSE_INDEX_REFERENCE](https://www.yuantaetfs.com/product/detail/0050/Basic_information)

| TW:ETF:006208 | verified_after_correction | sufficient | conditional | quantitative_review_pending | replacement_candidate |

**Selection rationale:** 大型股 ETF 候選；需評估與 0050 的重疊度。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_ETF](https://www.twse.com.tw/en/ETFortune-institute/etfInfo/006208), [FTSE_TWSE_INDEX_REFERENCE](https://www.twse.com.tw/en/ETFortune-institute/etfInfo/006208)

| TW:ETF:00878 | verified | sufficient | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 高股息 ETF 候選；需驗證指數規則與持股穿透。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_ETF](https://www.twse.com.tw/en/ETFortune-institute/etfInfo/00878), [MSCI_INDEX_REFERENCE](https://www.twse.com.tw/en/ETFortune-institute/etfInfo/00878)

| TW:ETF:00919 | verified | limited | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 高股息 ETF 候選；需評估策略重疊與完整歷史。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_ETF](https://taiwanindex.com.tw/en/indexes/IX0170), [TIP_INDEX_REFERENCE](https://taiwanindex.com.tw/en/indexes/IX0170)

| TW:ETF:00965 | verified_after_correction | limited | conditional | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 跨市場主題 ETF 候選；僅承接視覺參考，不沿用既有報告數字。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [TWSE_OGL_ETF](https://www.yuantaetfs.com/product/detail/00965/Basic_information), [NYSE_FACTSET_INDEX_REFERENCE](https://www.yuantaetfs.com/product/detail/00965/Basic_information)

| JP:STOCK:7203 | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 大型製造候選；需核對匯率與全球營收曝險。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [JPX_LISTING_REFERENCE](https://global.toyota/en/company/profile/overview/)

| JP:STOCK:6758 | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 科技與內容候選；需定義跨事業部特徵。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_LISTING_REFERENCE](https://www.sony.com/en/SonyInfo/CorporateInfo/)

| JP:STOCK:8035 | verified_after_correction | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 半導體設備候選；需驗證產業循環與訂單資料。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [JPX_LISTING_REFERENCE](https://www.tel.com/about/profile/)

| JP:STOCK:7011 | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 國防與重工候選；需追蹤正式採購與交付來源。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [JPX_LISTING_REFERENCE](https://www.mhi.com/company/overview)

| JP:STOCK:9432 | verified_after_correction | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 電信與股息候選；需核對公司行動與股利歷史。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_LISTING_REFERENCE](https://group.ntt/en/group/at-a-glance.html)

| JP:ETF:1306 | verified | sufficient | blocked | quantitative_review_pending | replacement_candidate |

**Selection rationale:** TOPIX 廣泛市場候選；需核對追蹤誤差與費用。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1306/), [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1306/)

| JP:ETF:1321 | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 日經 225 候選；需評估與 TOPIX 的基準差異。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1321/), [NIKKEI_INDEX_REFERENCE](https://nextfunds.jp/en/lineup/1321/)

| JP:ETF:1475 | verified | sufficient | blocked | quantitative_review_pending | replacement_candidate |

**Selection rationale:** 低成本 TOPIX 候選；需驗證持股歷史可得性。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_ETF_REFERENCE](https://www.blackrock.com/jp/individual-en/en/products/279438/ishares-core-topix-etf-fund), [JPX_ETF_REFERENCE](https://www.blackrock.com/jp/individual-en/en/products/279438/ishares-core-topix-etf-fund)

| JP:ETF:1489 | verified_after_correction | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 高股息因子候選；需驗證指數規則與換股資料。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1489/), [NIKKEI_INDEX_REFERENCE](https://nextfunds.jp/en/lineup/1489/)

| JP:ETF:2568 | verified_after_correction | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 日圓計價海外科技曝險候選；需明確處理匯率。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [JPX_ETF_REFERENCE](https://global.amova-am.com/general/etf/detail/2568-us-equity-nasdaq100-no-currency-hedge), [NASDAQ_INDEX_REFERENCE](https://global.amova-am.com/general/etf/detail/2568-us-equity-nasdaq100-no-currency-hedge)

| US:STOCK:NVDA | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** AI 與半導體候選；需驗證估值與供應鏈資料。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [SEC_OPEN](https://www.sec.gov/edgar/browse/?CIK=1045810&owner=exclude)

| US:STOCK:MSFT | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 大型軟體與雲端候選；需定義事件與財報權重。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [SEC_OPEN](https://www.sec.gov/edgar/browse/?CIK=789019&owner=exclude)

| US:STOCK:GOOGL | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 大型科技候選；需評估多事業營運特徵。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [SEC_OPEN](https://www.sec.gov/edgar/browse/?CIK=1652044&owner=exclude)

| US:STOCK:LMT | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 國防航太候選；需追蹤採購、積壓訂單與交付。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。)
Evidence: [SEC_OPEN](https://www.sec.gov/edgar/browse/?CIK=936468&owner=exclude)

| US:STOCK:JNJ | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 醫療與股息候選；需定義訴訟事件的風險處理。

Model routing: h_model=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); reverse_dcf=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); etf_look_through=not_applicable (此模型不適用此資產類型或目前研究問題。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [SEC_OPEN](https://www.sec.gov/edgar/browse/?CIK=200406&owner=exclude)

| US:ETF:SPY | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 美國大型股基準候選；需核對持股與費用。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [STATE_STREET_ETF_REFERENCE](https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy), [STATE_STREET_ETF_REFERENCE](https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy)

| US:ETF:QQQ | verified_after_correction | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 大型成長科技候選；需評估集中度與估值。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [INVESCO_ETF_REFERENCE](https://www.invesco.com/qqq-etf/en/about.html), [NASDAQ_INDEX_REFERENCE](https://www.invesco.com/qqq-etf/en/about.html)

| US:ETF:SMH | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 半導體產業候選；需持股穿透與循環模型。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [VANECK_ETF_REFERENCE](https://www.vaneck.com/us/en/investments/semiconductor-etf-smh/overview/), [MVIS_INDEX_REFERENCE](https://www.vaneck.com/us/en/investments/semiconductor-etf-smh/overview/)

| US:ETF:CIBR | verified_after_correction | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 資安主題候選；需核對指數分類與重疊。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [FIRST_TRUST_ETF_REFERENCE](https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker=CIBR), [NASDAQ_INDEX_REFERENCE](https://www.ftportfolios.com/Retail/Etf/EtfSummary.aspx?Ticker=CIBR)

| US:ETF:USMV | verified | sufficient | blocked | quantitative_review_pending | retain_for_owner_review |

**Selection rationale:** 低波動因子候選；需檢驗因子與市場狀態適用性。

Model routing: h_model=not_applicable (此模型不適用此資產類型或目前研究問題。); reverse_dcf=not_applicable (此模型不適用此資產類型或目前研究問題。); etf_look_through=conditional (待 point-in-time 資料、回測與 owner 核准後才可適用。); cobweb_supply_demand=not_applicable (此模型不適用此資產類型或目前研究問題。)
Evidence: [ISHARES_ETF_REFERENCE](https://www.ishares.com/us/products/239695/ishares-msci-usa-minimum-volatility-etf), [MSCI_INDEX_REFERENCE](https://www.ishares.com/us/products/239695/ishares-msci-usa-minimum-volatility-etf)

## Overlap findings

- **TW_TAIWAN50_DUPLICATION (high)**: 兩檔追蹤相同 FTSE TWSE Taiwan 50 Index。 Members: TW:ETF:0050, TW:ETF:006208. Evidence: [FTSE_TWSE_INDEX_REFERENCE](https://www.yuantaetfs.com/product/detail/0050/Basic_information)
- **TW_TAIWAN50_SINGLE_STOCK_LOOKTHROUGH (high)**: 大型股 ETF 與三檔成分股存在 look-through 集中風險。 Members: TW:ETF:0050, TW:ETF:006208, TW:STOCK:2330, TW:STOCK:2454, TW:STOCK:2308. Evidence: [TWSE_OGL_ETF](https://www.twse.com.tw/en/ETFortune-institute/etfInfo/006208)
- **TW_HIGH_DIVIDEND_FACTOR (medium)**: 兩檔皆屬台灣高股息策略但指數規則不同。 Members: TW:ETF:00878, TW:ETF:00919. Evidence: [TIP_INDEX_REFERENCE](https://taiwanindex.com.tw/en/indexes/IX0170)
- **JP_TOPIX_DUPLICATION (high)**: 兩檔目前均以 TOPIX Total Return Index 為基準。 Members: JP:ETF:1306, JP:ETF:1475. Evidence: [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1306/)
- **JP_BROAD_LARGE_CAP_OVERLAP (medium)**: TOPIX 與 Nikkei 225 broad-market 曝險存在交集。 Members: JP:ETF:1306, JP:ETF:1321, JP:ETF:1475. Evidence: [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1321/)
- **US_MEGA_CAP_TECH_LOOKTHROUGH (high)**: ETF look-through 與個股直接持有造成大型科技集中。 Members: US:ETF:SPY, US:ETF:QQQ, US:ETF:SMH, US:STOCK:NVDA, US:STOCK:MSFT, US:STOCK:GOOGL. Evidence: [INVESCO_ETF_REFERENCE](https://www.invesco.com/qqq-etf/en/about.html)

## ETF issuer concentration

- **TW — Yuanta Securities Investment Trust**: 2 of 5 (40%). 同一發行人占兩檔；owner 應決定發行人上限。 Evidence: [TWSE_OGL_ETF](https://www.yuantaetfs.com/product/detail/0050/Basic_information)
- **JP — Nomura Asset Management**: 3 of 5 (60%). 同一發行人占三檔，為三市場中最高。 Evidence: [JPX_ETF_REFERENCE](https://nextfunds.jp/en/lineup/1306/)
- **US — No repeated issuer**: maximum 1 of 5 (20%). 五檔 ETF 發行人皆不同；仍需追蹤服務供應鏈集中。 Evidence: [STATE_STREET_ETF_REFERENCE](https://www.ssga.com/us/en/intermediary/etfs/spdr-sp-500-etf-trust-spy)

## Owner decisions required

- **ACCEPT_METADATA_AND_THEME_CORRECTIONS**: 是否接受本次名稱、交易所與主題修正？ Gap: 需要 owner 對 scope 與命名政策簽核。
- **RESOLVE_DUPLICATE_INDEX_WRAPPERS**: 0050/006208 與 1306/1475 是否各只保留一檔？ Gap: 尚未取得費用、價差與可交易容量的可比較資料。
- **APPROVE_SHORT_HISTORY_POLICY**: 是否允許 live age 未滿五年的候選？ Gap: 00919 與 00965 無完整五年 live history。
- **DEFINE_EXACT_BENCHMARK_SERIES**: 三市場應採 price、total-return 或 net-return 哪一條精確序列？ Gap: 精確 series ID、point-in-time 與再發布權尚未簽約。
- **PROCURE_LIVE_SOURCE_RIGHTS**: 是否採購並核准 live/PIT 資料來源？ Gap: 來源矩陣顯示 EOD、公司行動、ETF holdings 與 benchmark 仍有條件或阻擋。
- **SET_LIQUIDITY_AND_OVERLAP_THRESHOLDS**: 最低成交額、最大價差、issuer 與 look-through 上限為何？ Gap: 尚未有 owner 核准的量化門檻。
- **APPROVE_MODEL_ROUTING**: 是否接受個股、ETF 與金融股的模型分流？ Gap: 模型仍待 point-in-time 回測、校準與 owner 核准。
