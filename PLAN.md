# StockmarketAgent implementation plan

## Product boundary

TRI_MARKET_STOCK_INTELLIGENCE_SPEC.md is the product contract. The Produce Watch specification contributes only reusable engineering patterns (deterministic generation, fixture-only CI, source traceability, last-known-good publication). The 00965 HTML contributes visual and information-architecture cues only.

The public MVP is deliberately research_only. It will not approve a production universe, publish calibrated BUY/SELL calls, schedule provider refreshes, or automate trading. A manually fetched TWSE OGL snapshot may be shown as separately labelled observed facts, but it must never enter the synthetic signal path.

## Delivery slice

1. Preserve the primary specification and record hashes and usage boundaries for all supplied references.
2. Define a proposed 30-instrument universe and explicit owner-approval gate.
3. Add strict, deterministic fixture validation and a single JSON source of truth.
4. Generate Markdown and a responsive static Pages site atomically from that JSON.
5. Test universe contracts, strict JSON, research-only gating, determinism, generated-content consistency, links, and secret-like output.
6. Publish the repository and deploy GitHub Pages from main through GitHub Actions.
7. Add the smallest safe official-data slice for 2330: five documented TWSE OpenAPI resources, strict observed-facts JSON, OGL attribution, response hashes, and a visible signal-isolation boundary.
8. Map the same policy-gated pattern to all ten Taiwan candidates, route stock／financial-holding／ETF facts correctly, and publish supporting evidence, counter-evidence, and invalidation conditions without changing signals.

## Release gates

- No credentials, generic HTML crawling, or scheduled live-provider dependencies.
- production_signal_enabled remains false.
- Official observations remain `used_in_signal=false` and `automated_refresh_enabled=false`.
- Proposed instruments are never emitted as production signals.
- Generated artifacts are reproducible and keep an archive alongside latest; Pages uploads only a fully validated artifact.
- Local test/build evidence, independent review, green remote checks, aligned origin/main, and HTTP 200 for the public Pages routes are all required before completion.

## Deferred by design

Complete point-in-time archives, correction streams, exact benchmark history, complete corporate-action history, market calendars, news classification, scoring calibration, backtesting, scheduled refresh PRs, and production BUY/SELL activation require separate reviewed changes and explicit owner approval where specified. A current-forecast slice of corporate actions (ex-right/ex-dividend) for the five Taiwan stock candidates is now ingestible as an optional, signal-isolated observed fact (see TW-C2 below); it is not a complete historical golden source and its field mapping awaits a human diff review against a live TWSE response.

## TW-C2: optional corporate-action forecast (not yet populated)

`src/ingestion/twse_openapi.py` can now fetch and normalize the documented "上市個股除權除息預告表" TWSE OpenAPI dataset (`data.gov.tw/dataset/89748`) into an optional `facts.corporate_actions` group on each of the five Taiwan stock snapshots, filtered by stock code with zero-or-more matches (most stocks have no upcoming event at any given time). It remains `used_in_signal=false` and is additive to the existing observed-facts contract: snapshots without it stay valid. This sandbox's network policy blocks `openapi.twse.com.tw`, so the endpoint path and field keys are the author's best-effort mapping, not verified against a live response — consistent with this project's existing policy that API values need manual diff review before a live run, no committed snapshot has been re-fetched with this capability yet.
