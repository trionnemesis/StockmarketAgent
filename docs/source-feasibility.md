# Source feasibility matrix

- Reviewed at: `2026-08-28T04:45:00Z`
- Live adapters enabled: `false`
- Publication boundary: {'raw_data_commit': 'Commit only official open-data fixtures with attribution; contract feeds and bulk archives stay out of the repository.', 'github_pages': 'Publish evidence metadata, citations, fixtures, and expressly reusable summaries only; licensed prices, holdings, and index values stay off Pages.', 'secrets': 'Credentials belong only in GitHub Actions repository/environment secret stores, never repository files or browser assets.'}

## Providers

| Source | Countries | Classes | Auth/key | PIT | License / Pages | Feasibility |
|---|---|---|---|---|---|---|
| [TWSE_OGL_COMPANY](https://data.gov.tw/dataset/18419) | TW | listing_metadata | none / False | partial | [open_with_attribution](https://data.gov.tw/license) / raw_with_attribution_allowed | conditional |
  - Access: Documented TWSE OpenAPI /opendata/t187ap03_L only; generic TWSE/MOPS HTML crawling is excluded.
  - Limits: No numeric limit is documented; identify the client, retrieve sequentially, cache snapshots, and back off on errors. History: Current published company snapshot; complete revision history is not promised.
  - Retention: Versioned normalized snapshots may be retained with attribution and retrieval time. Redistribution: Raw and adapted OGL records may be redistributed with attribution.
  - Fallback: Manual official issuer identity review. Gaps: No immutable correction stream or complete historical identity vintages.
| [TWSE_OGL_FINANCIALS](https://data.gov.tw/dataset/91998) | TW | filings_financials | none / False | partial | [open_with_attribution](https://data.gov.tw/license) / raw_with_attribution_allowed | conditional |
  - Access: Documented TWSE OpenAPI monthly revenue, general-industry income-statement, and balance-sheet endpoints; no MOPS HTML scraping.
  - Limits: No numeric limit is documented; the research adapter uses five sequential requests, a declared User-Agent, at least two seconds between requests, caching, and backoff. History: Current monthly and quarterly published snapshots; every observed version must be archived for future PIT use.
  - Retention: Normalized OGL facts and response hashes may be retained with attribution; raw full-market payloads are not committed. Redistribution: Normalized facts may be published with OGL attribution and source links.
  - Fallback: Official issuer releases as manual cross-checks; a separately licensed feed is required for complete PIT backfill. Gaps: Historical revisions, correction semantics, taxonomy drift, and complete PIT backfill are not provided by the current snapshot endpoints.
| [TWSE_OGL_EOD](https://data.gov.tw/dataset/11549) | TW | eod_prices | none / False | partial | [open_with_attribution](https://data.gov.tw/license) / raw_with_attribution_allowed | conditional |
  - Access: Documented TWSE OpenAPI /exchangeReport/STOCK_DAY_ALL and /exchangeReport/BWIBBU_ALL; no generic HTML scraping.
  - Limits: No numeric limit is documented; identify the client, retrieve sequentially, use at least two seconds between requests, cache ETag/Last-Modified, and back off. History: Current daily market and valuation snapshots; the official historical UI is not an approved bulk API.
  - Retention: Observed OGL snapshots and response hashes may be retained with attribution. Redistribution: OGL records and normalized facts may be redistributed with attribution.
  - Fallback: Separately licensed historical market-data feed. Gaps: No verified OGL full-history API, total-return series, or immutable correction stream.
| [TWSE_OGL_ACTIONS](https://data.gov.tw/dataset/89748) | TW | corporate_actions | none / False | partial | [open_with_attribution](https://data.gov.tw/en/license) / raw_with_attribution_allowed | conditional |
  - Access: TWSE OpenAPI ex-right/ex-dividend snapshots
  - Limits: Not documented; cache and back off conservatively. History: Current and forecast snapshots; complete action history is not documented.
  - Retention: Preserve every observed version with retrieval time. Redistribution: OGL snapshots may be redistributed with attribution.
  - Fallback: Issuer notices, filings, then a licensed golden source. Gaps: Not a complete split, rename, suspension, and delisting golden source.
| [TWSE_OGL_ETF](https://data.gov.tw/dataset/157399) | TW | listing_metadata, etf_fund_data | none / False | partial | [open_with_attribution](https://data.gov.tw/en/license) / raw_with_attribution_allowed | conditional |
  - Access: Monthly TWSE ETF issuance snapshot
  - Limits: Not documented; monthly retrieval is sufficient. History: Current monthly snapshot; immutable historical versions are not promised.
  - Retention: Observed OGL snapshots may be retained with attribution. Redistribution: OGL metadata may be redistributed with attribution.
  - Fallback: Official issuer product pages as metadata-only references. Gaps: No complete PIT holdings history.
| [SITCA_OGL_ETF](https://data.gov.tw/dataset/11109) | TW | etf_fund_data, filings_financials | none / False | partial | [open_with_attribution](https://data.gov.tw/en/license) / raw_with_attribution_allowed | conditional |
  - Access: Official ETF NAV open-data files plus fee datasets
  - Limits: Not documented; one daily cached retrieval is sufficient. History: Current published files; complete historical retention is not promised.
  - Retention: Observed OGL snapshots may be retained with attribution. Redistribution: OGL records may be redistributed with attribution.
  - Fallback: Issuer filings and a licensed fund-data source. Gaps: No complete holdings, AUM, fee, and NAV vintage archive.
| [TWSE_OGL_CALENDAR](https://data.gov.tw/dataset/11761) | TW | market_calendar | none / False | partial | [open_with_attribution](https://data.gov.tw/en/license) / raw_with_attribution_allowed | ready |
  - Access: Annual TWSE holiday schedule
  - Limits: Annual retrieval is sufficient. History: Latest annual schedule; archive each version.
  - Retention: Annual versions may be retained with attribution. Redistribution: OGL calendar records may be redistributed with attribution.
  - Fallback: Manually versioned official schedule. Gaps: Historical versions are not guaranteed by the endpoint.
| [TWSE_OGL_BENCHMARK](https://data.gov.tw/dataset/11755) | TW | benchmark | none / False | partial | [open_with_attribution](https://data.gov.tw/en/license) / raw_with_attribution_allowed | conditional |
  - Access: TAIEX daily OHLC open-data snapshots
  - Limits: Not documented; cache and back off conservatively. History: Latest-month style snapshots; no verified OGL full backfill.
  - Retention: Observed OGL snapshots may be retained with attribution. Redistribution: TAIEX price-index observations may be published with attribution.
  - Fallback: Licensed price or total-return index history. Gaps: Dataset 11755 does not establish total-return coverage.
| [CBC_OGL_FX](https://www.cbc.gov.tw/tw/cp-520-36599-75987-1.html) | TW, JP, US | fx | none / False | partial | [open_with_attribution](https://data.gov.tw/en/license) / raw_with_attribution_allowed | conditional |
  - Access: Official daily currency workbooks
  - Limits: Not documented; daily cached retrieval is sufficient. History: Daily observations from 1993; review on 2026-08-27 observed data only through 2026-07-31.
  - Retention: Versioned open-data snapshots may be retained with attribution. Redistribution: Open-data observations may be redistributed with attribution.
  - Fallback: Federal Reserve H.10 for JPY/USD; TWD current fallback remains unresolved. Gaps: Publication can lag and TWD triangulation policy is not approved.
| [FTSE_TWSE_INDEX_REFERENCE](https://www.yuantaetfs.com/product/detail/0050/Basic_information) | TW | benchmark | manual_download / False | not_supported | [metadata_only](https://www.lseg.com/en/policies/terms-and-conditions) / metadata_only | reference_only |
  - Access: Manual official product/index identity review; series data require a separate license
  - Limits: No automated collection approved. History: Identity only; historical series and constituents are contract-gated.
  - Retention: Retain citation metadata only. Redistribution: Index identity and source links only.
  - Fallback: Issuer prospectus and TWSE product page. Gaps: Exact PR/TR/NR series, constituents, and model-use rights are unapproved.
| [MSCI_INDEX_REFERENCE](https://www.msci.com/indexes) | TW, US | benchmark | manual_download / False | not_supported | [metadata_only](https://www.msci.com/legal/terms-of-use) / metadata_only | reference_only |
  - Access: Manual official index identity review; data require a provider contract
  - Limits: No automated collection approved. History: Identity only; historical series and constituents are contract-gated.
  - Retention: Retain citation metadata only. Redistribution: Index identity and source links only.
  - Fallback: Issuer prospectus. Gaps: Exact return variant, PIT constituents, and redistribution rights are unapproved.
| [TIP_INDEX_REFERENCE](https://taiwanindex.com.tw/en/indexes/IX0170) | TW | benchmark | manual_download / False | not_supported | [metadata_only](https://taiwanindex.com.tw/en/terms) / metadata_only | reference_only |
  - Access: Manual official index profile review; historical data require authorization
  - Limits: No automated collection approved. History: Identity and current methodology metadata only.
  - Retention: Retain citation metadata only. Redistribution: Index identity and source links only.
  - Fallback: Fund prospectus and TWSE product page. Gaps: Return variant, methodology vintages, and constituent history are unapproved.
| [NYSE_FACTSET_INDEX_REFERENCE](https://www.yuantaetfs.com/product/detail/00965/Basic_information) | TW | benchmark | manual_download / False | not_supported | [metadata_only](https://www.nyse.com/terms-of-use) / metadata_only | reference_only |
  - Access: Manual official fund/index identity review; data require provider contracts
  - Limits: No automated collection approved. History: Identity only; historical series and constituents are contract-gated.
  - Retention: Retain citation metadata only. Redistribution: Index identity and source links only.
  - Fallback: Fund prospectus. Gaps: Return/currency variant, PIT constituents, and redistribution rights are unapproved.
| [JPX_LISTING_REFERENCE](https://www.jpx.co.jp/english/markets/statistics-equities/misc/01.html) | JP | listing_metadata | manual_download / False | not_supported | [metadata_only](https://www.jpx.co.jp/english/corporate/terms-of-use/index.html) / metadata_only | reference_only |
  - Access: Manual official listed-issues files and issuer search
  - Limits: No automated collection approved. History: Current reference files; vintage guarantees require a contract.
  - Retention: Retain citation metadata only. Redistribution: Listing identity and source links only.
  - Fallback: Issuer corporate pages. Gaps: Exact historical identity vintages are not available as open data.
| [JQUANTS_CONTRACT](https://jpx-jquants.com/en/spec) | JP | listing_metadata, eod_prices, corporate_actions, filings_financials | contract_credentials / True | unknown | [contract_required](https://jpx-jquants.com/en/terms-of-use) / not_allowed | conditional |
  - Access: Business contract API; individual plan is not a recurring public backend
  - Limits: Contract-specific. History: Contract-specific PIT and backfill scope.
  - Retention: Contract-specific. Redistribution: No repository or Pages rights until expressly licensed.
  - Fallback: JPX references plus EDINET; incomplete for canonical EOD/actions. Gaps: Owner must procure storage, model-use, retention, and public-display rights.
| [EDINET_V2](https://disclosure2.edinet-fsa.go.jp/week0020.aspx) | JP | corporate_actions, filings_financials, etf_fund_data | api_key / True | supported | [open_with_attribution](https://disclosure2.edinet-fsa.go.jp/guide/static/disclosure/WZEK0090.html) / derived_only | conditional |
  - Access: EDINET API v2 document list and retrieval
  - Limits: Numeric quota not published; short-period bulk access is prohibited. History: Date-list search under ten years; major periodic filings generally ten years.
  - Retention: Retain normalized filing metadata and permitted documents with accession dates. Redistribution: Derived summaries with attribution; document reuse follows filing terms.
  - Fallback: Issuer filings and a licensed disclosure feed. Gaps: API key, taxonomy drift, and fund-holdings normalization need implementation.
| [JPX_ETF_REFERENCE](https://www.jpx.co.jp/english/equities/products/etfs/issues/01.html) | JP | listing_metadata, etf_fund_data, benchmark | manual_download / False | not_supported | [metadata_only](https://www.jpx.co.jp/english/corporate/terms-of-use/index.html) / metadata_only | reference_only |
  - Access: Manual official ETF list, tracking-index identity, and issuer links
  - Limits: No automated collection approved. History: Current facts and tracking-index identity; no immutable historical holdings or index-series API.
  - Retention: Retain citation metadata only. Redistribution: Fund and tracking-index identity with source links only.
  - Fallback: Issuer product pages and EDINET filings. Gaps: No open PIT holdings, NAV, AUM, spread history, or benchmark series.
| [JPX_CALENDAR_REFERENCE](https://www.jpx.co.jp/english/corporate/about-jpx/calendar/) | JP | market_calendar | manual_download / False | not_supported | [metadata_only](https://www.jpx.co.jp/english/corporate/terms-of-use/index.html) / metadata_only | reference_only |
  - Access: Manual official current and next-year calendar review
  - Limits: No automated collection approved. History: Current and next year only.
  - Retention: Retain citation and manually versioned schedule metadata. Redistribution: Links and derived schedule summary only.
  - Fallback: Licensed calendar feed. Gaps: No approved normalized historical calendar API.
| [JPX_BENCHMARK_CONTRACT](https://www.jpx.co.jp/english/markets/paid-info-equities/historical/index.html) | JP | benchmark | contract_credentials / True | unknown | [contract_required](https://www.jpx.co.jp/english/markets/paid-info-equities/index.html) / not_allowed | blocked |
  - Access: Licensed TOPIX series and constituent history
  - Limits: Contract-specific. History: Contract-specific price/total-return and constituent vintages.
  - Retention: Contract-specific. Redistribution: No repository or Pages rights until expressly licensed.
  - Fallback: Identity-only JPX and issuer references. Gaps: Owner must choose exact series and procure PIT/model/display rights.
| [NIKKEI_INDEX_REFERENCE](https://indexes.nikkei.co.jp/en/nkave/index/profile?idx=nk225) | JP | benchmark | manual_download / False | not_supported | [metadata_only](https://indexes.nikkei.co.jp/en/nkave/license) / metadata_only | reference_only |
  - Access: Manual official index identity review; data require a Nikkei license
  - Limits: No automated collection approved. History: Identity only; historical series and constituents are contract-gated.
  - Retention: Retain citation metadata only. Redistribution: Index identity and links only.
  - Fallback: ETF issuer prospectus. Gaps: Total-return series, methodology vintages, and constituent rights are unapproved.
| [NASDAQ_INDEX_REFERENCE](https://indexes.nasdaqomx.com/) | JP, US | benchmark | manual_download / False | not_supported | [metadata_only](https://www.nasdaq.com/legal) / metadata_only | reference_only |
  - Access: Manual official index identity review; data require a Nasdaq license
  - Limits: No automated collection approved. History: Identity only; historical series and constituents are contract-gated.
  - Retention: Retain citation metadata only. Redistribution: Index identity and links only.
  - Fallback: SEC fund filings and issuer prospectuses. Gaps: Exact return/currency variants and constituent/model-use rights are unapproved.
| [SEC_OPEN](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) | US | listing_metadata, corporate_actions, filings_financials, etf_fund_data | none / False | supported | [free_reuse](https://www.sec.gov/about/privacy-information) / derived_only | ready |
  - Access: SEC ticker/exchange, submissions, XBRL, and N-PORT datasets
  - Limits: Declared User-Agent and aggregate maximum 10 requests per second. History: EDGAR since 1994/95; XBRL broadly since 2009; N-PORT datasets since October 2019.
  - Retention: Public datasets and accession metadata may be retained with provenance. Redistribution: Public facts and derived summaries may be reused with source attribution.
  - Fallback: Issuer filings and venue notices. Gaps: SEC does not provide canonical exchange EOD prices or all venue actions.
| [CBOE_EOD_CONTRACT](https://datashop.cboe.com/equity-eod-summary) | US | eod_prices | contract_credentials / True | unknown | [contract_required](https://datashop.cboe.com/data-policies) / not_allowed | blocked |
  - Access: Licensed Equity EOD Summary for nationally listed U.S. securities
  - Limits: Contract-specific. History: Product advertises January 2010-present.
  - Retention: Contract-specific. Redistribution: No repository or Pages rights until expressly licensed.
  - Fallback: No verified open official national EOD series. Gaps: Pre-2010 history and correction vintages require another licensed source.
| [NASDAQ_ACTIONS_CONTRACT](https://www.nasdaqtrader.com/Trader.aspx?id=dailylistpd) | US | listing_metadata, corporate_actions | contract_credentials / True | partial | [contract_required](https://www.nasdaqtrader.com/Trader.aspx?id=DPUSdata) / not_allowed | blocked |
  - Access: Licensed Nasdaq Daily List
  - Limits: Contract-specific. History: Listing and action history advertised from 1999 for Nasdaq venues.
  - Retention: Contract-specific. Redistribution: No repository or Pages rights until expressly licensed.
  - Fallback: SEC accessions and issuer notices. Gaps: Nasdaq-only venue scope.
| [NYSE_ACTIONS_CONTRACT](https://www.nyse.com/market-data/corporate-actions) | US | listing_metadata, corporate_actions | contract_credentials / True | partial | [contract_required](https://www.nyse.com/market-data/agreements) / not_allowed | blocked |
  - Access: Licensed NYSE Group Market Event Feed
  - Limits: Contract-specific. History: Historical NYSE Group actions; exact contracted depth is undecided.
  - Retention: Contract-specific. Redistribution: No repository or Pages rights until expressly licensed.
  - Fallback: SEC accessions and issuer notices. Gaps: NYSE Group venue scope and revision vintages need contract confirmation.
| [CBOE_ACTIONS_CONTRACT](https://datashop.cboe.com/listings-distributions-and-corporate-actions) | US | listing_metadata, corporate_actions | contract_credentials / True | partial | [contract_required](https://datashop.cboe.com/data-policies) / not_allowed | blocked |
  - Access: Licensed Cboe BZX listings, distributions, and corporate-action reports
  - Limits: Subscription-specific. History: Product advertises 2012-05-01-present.
  - Retention: Contract-specific. Redistribution: External redistribution requires additional terms and fees; none are approved.
  - Fallback: SEC accessions and issuer notices. Gaps: Cboe BZX-only venue scope and revision vintages are undecided.
| [STATE_STREET_ETF_REFERENCE](https://www.ssga.com/us/en/intermediary/etfs/state-street-spdr-sp-500-etf-trust-spy) | US | listing_metadata, etf_fund_data, benchmark | manual_download / False | not_supported | [metadata_only](https://www.ssga.com/us/en/intermediary/footer/terms-of-use) / metadata_only | reference_only |
  - Access: Manual official SPY product and tracking-index identity review
  - Limits: No automated collection approved. History: Current product and tracking-index identity; no approved PIT holdings or benchmark-series archive.
  - Retention: Retain citation metadata only. Redistribution: Product and tracking-index identity with source links only.
  - Fallback: SEC fund filings. Gaps: Holdings, AUM, fees, trading history, and benchmark series need authorized vintages.
| [INVESCO_ETF_REFERENCE](https://www.invesco.com/us/en/financial-products/etfs/invesco-qqq-trust-series-1.html) | US | listing_metadata, etf_fund_data | manual_download / False | not_supported | [metadata_only](https://www.invesco.com/us/en/footer/terms-of-use.html) / metadata_only | reference_only |
  - Access: Manual official QQQ product-page review
  - Limits: No automated collection approved. History: Current product metadata; no approved PIT holdings archive.
  - Retention: Retain citation metadata only. Redistribution: Product identity and links only.
  - Fallback: SEC fund filings. Gaps: 2025 trust-structure break and PIT holdings require explicit handling.
| [VANECK_ETF_REFERENCE](https://www.vaneck.com/us/en/investments/semiconductor-etf-smh/) | US | listing_metadata, etf_fund_data | manual_download / False | not_supported | [metadata_only](https://www.vaneck.com/us/en/terms-and-conditions/) / metadata_only | reference_only |
  - Access: Manual official SMH product-page review
  - Limits: No automated collection approved. History: Current product metadata; no approved PIT holdings archive.
  - Retention: Retain citation metadata only. Redistribution: Product identity and links only.
  - Fallback: SEC fund filings. Gaps: PIT holdings and MVIS index data require licenses.
| [FIRST_TRUST_ETF_REFERENCE](https://www.ftportfolios.com/retail/etf/etfsummary.aspx?Ticker=CIBR) | US | listing_metadata, etf_fund_data | manual_download / False | not_supported | [metadata_only](https://www.ftportfolios.com/Common/Legal.aspx) / metadata_only | reference_only |
  - Access: Manual official CIBR product-page review
  - Limits: No automated collection approved. History: Current product metadata; no approved PIT holdings archive.
  - Retention: Retain citation metadata only. Redistribution: Product identity and links only.
  - Fallback: SEC fund filings. Gaps: PIT holdings and Nasdaq CTA index data require licenses.
| [ISHARES_ETF_REFERENCE](https://www.ishares.com/us/products/239695/ishares-msci-usa-minimum-volatility-etf) | US | listing_metadata, etf_fund_data | manual_download / False | not_supported | [metadata_only](https://www.ishares.com/us/legal/terms-and-conditions) / metadata_only | reference_only |
  - Access: Manual official USMV product-page review
  - Limits: No automated collection approved. History: Current product metadata; no approved PIT holdings archive.
  - Retention: Retain citation metadata only. Redistribution: Product identity and links only.
  - Fallback: SEC fund filings. Gaps: PIT holdings and MSCI index data require licenses.
| [NYSE_CALENDAR_REFERENCE](https://www.nyse.com/markets/hours-calendars) | US | market_calendar | manual_download / False | partial | [metadata_only](https://www.nyse.com/terms-of-use) / metadata_only | reference_only |
  - Access: Manual official holiday and early-close schedule review
  - Limits: No automated collection approved. History: Current published multi-year schedule.
  - Retention: Retain citation and derived schedule metadata only. Redistribution: Links and derived schedule summary only.
  - Fallback: Licensed U.S. calendar feed. Gaps: No approved normalized historical API.
| [NASDAQ_CALENDAR_REFERENCE](https://www.nasdaqtrader.com/trader.aspx?id=calendar) | US | market_calendar | manual_download / False | partial | [metadata_only](https://www.nasdaq.com/legal) / metadata_only | reference_only |
  - Access: Manual official equity-calendar review
  - Limits: No automated collection approved. History: Current annual schedule plus selected alerts.
  - Retention: Retain citation and derived schedule metadata only. Redistribution: Links and derived schedule summary only.
  - Fallback: Licensed U.S. calendar feed. Gaps: No approved normalized historical API.
| [CBOE_CALENDAR_REFERENCE](https://www.cboe.com/en/about/hours/) | US | market_calendar | manual_download / False | partial | [metadata_only](https://www.cboe.com/us/terms_conditions/) / metadata_only | reference_only |
  - Access: Manual official equities-hours and holiday review
  - Limits: No automated collection approved. History: Current annual schedule.
  - Retention: Retain citation and derived schedule metadata only. Redistribution: Links and derived schedule summary only.
  - Fallback: Licensed U.S. calendar feed. Gaps: Historical retention is not promised.
| [FED_H10_FX](https://www.federalreserve.gov/releases/h10/hist/) | TW, JP, US | fx | none / False | partial | [free_reuse](https://www.federalreserve.gov/aboutthefed/termsofuse.htm) / derived_only | conditional |
  - Access: Official H.10 pages and downloadable series
  - Limits: Direct-page numeric limit is not documented; cache conservatively. History: Daily JPY and TWD observations generally from 2000, published weekly.
  - Retention: Public observations may be retained with provenance. Redistribution: Derived summaries may be published with attribution.
  - Fallback: CBC open data. Gaps: Release lag and exact TWD cross-rate policy remain owner decisions.
| [SPDJI_BENCHMARK_CONTRACT](https://www.spglobal.com/spdji/en/about-us/data-index-licensing/) | US | benchmark | contract_credentials / True | unknown | [contract_required](https://www.spglobal.com/spdji/en/legal/) / not_allowed | blocked |
  - Access: Licensed S&P 500 series and constituent history
  - Limits: Contract-specific. History: Contract-specific price/total-return and constituent vintages.
  - Retention: Contract-specific. Redistribution: No repository or Pages rights until expressly licensed.
  - Fallback: SEC fund filings verify identity but not index history. Gaps: Exact series, PIT constituents, and model/display rights are unapproved.
| [MVIS_INDEX_REFERENCE](https://www.marketvector.com/indexes/sector/mvis-us-listed-semiconductor-25) | US | benchmark | manual_download / False | not_supported | [metadata_only](https://www.marketvector.com/legal) / metadata_only | reference_only |
  - Access: Manual official index identity review; data require a provider license
  - Limits: No automated collection approved. History: Identity only; historical series and constituents are contract-gated.
  - Retention: Retain citation metadata only. Redistribution: Index identity and links only.
  - Fallback: VanEck prospectus and SEC filings. Gaps: Exact return variant, PIT constituents, and model-use rights are unapproved.

## Country / asset policies

### TW_STOCK_V1 (TW stock)

- `listing_metadata` — **conditional** — TWSE_OGL_COMPANY — Official identity snapshots; historical vintages incomplete.
- `eod_prices` — **conditional** — TWSE_OGL_EOD — Current OGL snapshot only; full history unresolved.
- `corporate_actions` — **conditional** — TWSE_OGL_ACTIONS — Incomplete golden-source coverage; no compatible fallback is approved.
- `filings_financials` — **conditional** — TWSE_OGL_FINANCIALS — Manual OGL snapshots are publishable with attribution; archive every revision before PIT model use.
- `etf_fund_data` — **not_applicable** — N/A — Not applicable to stocks.
- `market_calendar` — **ready** — TWSE_OGL_CALENDAR — Archive annual versions.
- `fx` — **conditional** — CBC_OGL_FX, FED_H10_FX — Needed for cross-market comparison.
- `benchmark` — **conditional** — TWSE_OGL_BENCHMARK — Portfolio comparator series variant remains unapproved.

### TW_ETF_V1 (TW etf)

- `listing_metadata` — **conditional** — TWSE_OGL_ETF — Current official ETF identity snapshots.
- `eod_prices` — **conditional** — TWSE_OGL_EOD — Current OGL snapshot only.
- `corporate_actions` — **conditional** — TWSE_OGL_ACTIONS — Fund events and distributions need fuller history.
- `filings_financials` — **conditional** — SITCA_OGL_ETF — Fund disclosure history is incomplete; no compatible fallback is approved.
- `etf_fund_data` — **conditional** — TWSE_OGL_ETF, SITCA_OGL_ETF — NAV and basics available; PIT holdings remain a gap.
- `market_calendar` — **ready** — TWSE_OGL_CALENDAR — Archive annual versions.
- `fx` — **conditional** — CBC_OGL_FX, FED_H10_FX — Required for 00965 and cross-market comparison.
- `benchmark` — **conditional** — TWSE_OGL_BENCHMARK, FTSE_TWSE_INDEX_REFERENCE, MSCI_INDEX_REFERENCE, TIP_INDEX_REFERENCE, NYSE_FACTSET_INDEX_REFERENCE — Portfolio comparator is partial; all four tracking-index providers are identity-only until licensed.

### JP_STOCK_V1 (JP stock)

- `listing_metadata` — **reference_only** — JPX_LISTING_REFERENCE — Official current identity, link-only.
- `eod_prices` — **conditional** — JQUANTS_CONTRACT — Business rights must be procured.
- `corporate_actions` — **conditional** — JQUANTS_CONTRACT, EDINET_V2 — Exchange actions need contract; filings are partial fallback.
- `filings_financials` — **conditional** — EDINET_V2, JQUANTS_CONTRACT — API implementation and taxonomy handling remain.
- `etf_fund_data` — **not_applicable** — N/A — Not applicable to stocks.
- `market_calendar` — **reference_only** — JPX_CALENDAR_REFERENCE — Manual reference only.
- `fx` — **conditional** — CBC_OGL_FX, FED_H10_FX — JPY normalization remains policy-gated.
- `benchmark` — **blocked** — JPX_BENCHMARK_CONTRACT — TOPIX series and PIT constituents require a license.

### JP_ETF_V1 (JP etf)

- `listing_metadata` — **reference_only** — JPX_ETF_REFERENCE — Official current identity, link-only.
- `eod_prices` — **conditional** — JQUANTS_CONTRACT — Business rights must be procured.
- `corporate_actions` — **conditional** — JQUANTS_CONTRACT, EDINET_V2 — Fund events require combined sources.
- `filings_financials` — **conditional** — EDINET_V2 — Fund disclosure parsing remains.
- `etf_fund_data` — **conditional** — JPX_ETF_REFERENCE, EDINET_V2 — Current facts and filings only; PIT holdings unavailable.
- `market_calendar` — **reference_only** — JPX_CALENDAR_REFERENCE — TSE calendar plus underlying U.S. calendar for 2568.
- `fx` — **conditional** — CBC_OGL_FX, FED_H10_FX — JPY conversion and hedging policy remain.
- `benchmark` — **blocked** — JPX_BENCHMARK_CONTRACT, NIKKEI_INDEX_REFERENCE, NASDAQ_INDEX_REFERENCE — TOPIX, Nikkei, and Nasdaq provider-specific data rights are unapproved.

### US_STOCK_V1 (US stock)

- `listing_metadata` — **ready** — SEC_OPEN, NASDAQ_ACTIONS_CONTRACT, NYSE_ACTIONS_CONTRACT, CBOE_ACTIONS_CONTRACT — SEC reference plus venue-specific contracts.
- `eod_prices` — **blocked** — CBOE_EOD_CONTRACT — No approved open national EOD source.
- `corporate_actions` — **blocked** — NASDAQ_ACTIONS_CONTRACT, NYSE_ACTIONS_CONTRACT, CBOE_ACTIONS_CONTRACT, SEC_OPEN — Venue contracts required; SEC is incomplete fallback.
- `filings_financials` — **ready** — SEC_OPEN — Accession-based PIT reconstruction required.
- `etf_fund_data` — **not_applicable** — N/A — Not applicable to stocks.
- `market_calendar` — **reference_only** — NYSE_CALENDAR_REFERENCE, NASDAQ_CALENDAR_REFERENCE, CBOE_CALENDAR_REFERENCE — Venue-specific schedules are manual references.
- `fx` — **conditional** — FED_H10_FX, CBC_OGL_FX — USD base and cross-market policy remain.
- `benchmark` — **blocked** — SPDJI_BENCHMARK_CONTRACT — S&P 500 series and constituents require a license.

### US_ETF_V1 (US etf)

- `listing_metadata` — **conditional** — SEC_OPEN, STATE_STREET_ETF_REFERENCE, INVESCO_ETF_REFERENCE, VANECK_ETF_REFERENCE, FIRST_TRUST_ETF_REFERENCE, ISHARES_ETF_REFERENCE — Each issuer is documented separately; SEC confirms registrations.
- `eod_prices` — **blocked** — CBOE_EOD_CONTRACT — No approved open national EOD source.
- `corporate_actions` — **blocked** — NASDAQ_ACTIONS_CONTRACT, NYSE_ACTIONS_CONTRACT, CBOE_ACTIONS_CONTRACT, SEC_OPEN — Venue contracts required; SEC is incomplete fallback.
- `filings_financials` — **ready** — SEC_OPEN — Fund filings and accessions are reusable.
- `etf_fund_data` — **conditional** — SEC_OPEN, STATE_STREET_ETF_REFERENCE, INVESCO_ETF_REFERENCE, VANECK_ETF_REFERENCE, FIRST_TRUST_ETF_REFERENCE, ISHARES_ETF_REFERENCE — N-PORT is lagged; issuer current holdings are metadata-only.
- `market_calendar` — **reference_only** — NYSE_CALENDAR_REFERENCE, NASDAQ_CALENDAR_REFERENCE, CBOE_CALENDAR_REFERENCE — Venue-specific schedules are manual references.
- `fx` — **conditional** — FED_H10_FX, CBC_OGL_FX — USD base and cross-market policy remain.
- `benchmark` — **blocked** — SPDJI_BENCHMARK_CONTRACT, NASDAQ_INDEX_REFERENCE, MVIS_INDEX_REFERENCE, MSCI_INDEX_REFERENCE — S&P, Nasdaq, MVIS, and MSCI provider-specific series/constituents remain unlicensed.

