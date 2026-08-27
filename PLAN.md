# StockmarketAgent implementation plan

## Product boundary

TRI_MARKET_STOCK_INTELLIGENCE_SPEC.md is the product contract. The Produce Watch specification contributes only reusable engineering patterns (deterministic generation, fixture-only CI, source traceability, last-known-good publication). The 00965 HTML contributes visual and information-architecture cues only.

The public MVP is deliberately research_only. It will not fetch live market data, approve a production universe, publish calibrated BUY/SELL calls, or automate trading. Until the owner approves the universe and model, every fixture instrument resolves to NO_SIGNAL.

## Delivery slice

1. Preserve the primary specification and record hashes and usage boundaries for all supplied references.
2. Define a proposed 30-instrument universe and explicit owner-approval gate.
3. Add strict, deterministic fixture validation and a single JSON source of truth.
4. Generate Markdown and a responsive static Pages site atomically from that JSON.
5. Test universe contracts, strict JSON, research-only gating, determinism, generated-content consistency, links, and secret-like output.
6. Publish the repository and deploy GitHub Pages from main through GitHub Actions.

## Release gates

- No credentials or live-provider dependencies.
- production_signal_enabled remains false.
- Proposed instruments are never emitted as production signals.
- Generated artifacts are reproducible and keep an archive alongside latest; Pages uploads only a fully validated artifact.
- Local test/build evidence, independent review, green remote checks, aligned origin/main, and HTTP 200 for the public Pages routes are all required before completion.

## Deferred by design

Live source adapters, point-in-time fundamentals, market calendars, news classification, scoring calibration, backtesting, automated refresh PRs, and production BUY/SELL activation require separate reviewed changes and explicit owner approval where specified.
