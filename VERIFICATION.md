# Verification record

Observed on 2026-08-27 and re-verified on 2026-08-28. This record distinguishes generated, committed, pushed, deployed, and publicly reachable states.


## Taiwan 10-candidate official-evidence matrix (2026-08-28)

This candidate maps the policy-gated TWSE OGL observation pattern to all ten Taiwan candidates. Five stocks receive EOD, valuation, monthly revenue, and the applicable general-industry or financial-holding statements; five ETFs receive EOD and fund-profile facts. Each observation adds data-quality supporting evidence, counter-evidence, and invalidation conditions while remaining isolated from synthetic research attitudes.

### Acceptance evidence

- `python3 -m src.ingestion.twse_openapi`
  - success; eight documented OpenAPI resources fetched sequentially with a declared User-Agent and at least two seconds between requests; ten normalized snapshots written without retaining full-market payloads.
- Remote source revision `3dc74da28c830d9dfe21fd74bf7a5e357f875683`
  - exact remote tree used by the deterministic build; run `20260827T120000Z-research-bb91267a`; 30 instruments; `research_only`; 84 generated outputs.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v`
  - 69 tests passed locally and again on GitHub Actions. Coverage includes all-ten membership, schema and source bindings, general-industry／financial-holding／ETF routing, evidence lists, Pages JSON mirrors, ten matrix rows, internal links, and synthetic-provenance isolation.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m src.pipeline validate`
  - strict signal, source, observed-facts, generated-artifact, immutable-run, and source-revision consistency passed locally and on GitHub Actions.
- Python compilation, workflow YAML parsing, and `git diff --check`
  - passed.
- Local GitHub Pages smoke test
  - HTTP 200 with expected content types for home, Taiwan matrix, representative general stock, financial-holding and foreign-constituent ETF pages, two observation JSON files, latest signal JSON, source feasibility, and status.
- Remote branch artifact build
  - [GitHub Actions run 33147291878](https://github.com/trionnemesis/StockmarketAgent/actions/runs/33147291878) succeeded. Its branch-only bootstrap workflow removed itself before the output commit; the final tree contains only the normal Quality and Deploy Pages workflows.

The observation matrix is data-quality context only: every snapshot and evidence assessment remains `used_in_signal=false`, automation remains disabled, and the 3M synthetic stance is explicitly unchanged by official facts. Remote PR checks and the post-merge public Pages verification remain separate release gates.

## TSMC official-observation candidate (2026-08-28)

This candidate adds a manually refreshed, policy-gated snapshot of five documented TWSE OpenAPI resources to the 2330 page. The normalized facts are separately labeled, attributed under Taiwan Open Government Data License 1.0, and contractually excluded from synthetic scores, research attitudes, production routing, and trade execution.

### Local acceptance

- `python3 -m src.ingestion.twse_openapi`
  - success; one `TW:STOCK:2330` record selected from each of five official resources; fetched at `2026-08-28T04:54:39Z`; response hashes and source metadata retained without retaining full-market payloads.
- `python3 -m src.pipeline build`
  - success from remote source revision `89522477741adb23613e5844cc22176e4de2d78b`; run `20260827T120000Z-research-17b9049d`; 30 instruments; `research_only`; 75 generated outputs.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py'`
  - 69 tests passed, including response normalization, missing/duplicate-record rejection, observed-facts schema and domain contracts, Pages isolation, and signal-provenance invariance.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m src.pipeline validate`
  - strict signal, source, observed-facts, generated-artifact, and source-revision consistency passed.
- Python compilation, workflow YAML parsing, and `git diff --check`
  - passed.
- Local GitHub Pages smoke test
  - HTTP 200 with expected content types for home, Taiwan market, 2330, source feasibility, status, the strict TSMC observation JSON, and latest signal JSON.
  - the 2330 page showed the official observation section while the observation remained `used_in_signal=false`, `automated_refresh_enabled=false`, and `html_scraping=false`.

Remote PR checks and the post-merge Pages deployment remain separate release gates.

## Research-analysis candidate (2026-08-28)

This candidate enables deterministic, synthetic research analysis without enabling live adapters or production signals. Its BUY/HOLD/SELL labels are uncalibrated scenario outputs, not current market facts or investment recommendations.

### Local acceptance

- `python3 -m src.pipeline build`
  - success; run `20260827T120000Z-research-10ff9eb1`; 30 instruments; `research_only`; 73 generated outputs.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v`
  - 67 tests passed. Mutation coverage includes threshold classification, Risk Gate overrides, event/provenance integrity, intraday no-lookahead, and source-revision mismatch; positive validation also covers immutable-history cross-binding and loading each research run's versioned policy config.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m src.pipeline validate`
  - strict schemas, configuration contracts, risk gates, and generated-artifact consistency passed.
- `git diff --check`, tracked/untracked artifact checks, and Python compilation
  - passed.
- Local GitHub Pages smoke test
  - HTTP 200 for home, all market pages, a representative instrument page, methodology, status, history, universe review, source feasibility, and latest JSON.
  - synthetic-research warnings and `research_fixture` provenance were present.

Remote PR checks, merge alignment, and the post-merge Pages deployment are verified separately before this candidate is called released.

## Scope

The verified release is a research-only fixture MVP. It does not verify live market adapters, point-in-time financial data, an approved Universe, calibrated models, or production BUY/SELL signals.

## Local acceptance

- python3 -m src.pipeline build
  - success; 30 instruments; research_only; 55 generated outputs.
- PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p 'test_*.py' -v
  - 23 tests passed.
- PYTHONDONTWRITEBYTECODE=1 python3 -m src.pipeline validate
  - strict schemas and latest/docs/archive consistency passed.
- Ruby YAML parsing of quality.yml and deploy-pages.yml
  - both workflow files parsed successfully.
- git diff --cached --check
  - no whitespace errors before the initial commit.
- Independent read-only review
  - PASS after the dated history index and publication-boundary wording were corrected.

## Initial remote release

- Repository: https://github.com/trionnemesis/StockmarketAgent
- Initial main commit: 04ba6ed752fa861037348b5382070acb52a2755a
- Quality run: https://github.com/trionnemesis/StockmarketAgent/actions/runs/33086223879
  - conclusion: success.
- Deploy Pages run: https://github.com/trionnemesis/StockmarketAgent/actions/runs/33086223947
  - build and deploy jobs: success.
- Pages mode: GitHub Actions workflow; HTTPS enforced.

The initial release returned HTTP 200 with the expected content types for:

- https://trionnemesis.github.io/StockmarketAgent/
- https://trionnemesis.github.io/StockmarketAgent/markets/tw.html
- https://trionnemesis.github.io/StockmarketAgent/instruments/tsmc.html
- https://trionnemesis.github.io/StockmarketAgent/methodology.html
- https://trionnemesis.github.io/StockmarketAgent/status.html
- https://trionnemesis.github.io/StockmarketAgent/data/latest.json
- https://trionnemesis.github.io/StockmarketAgent/assets/og.png

## Intentional limitations

- Browser-rendered desktop/mobile and keyboard QA was not performed; static accessibility, link, responsive-CSS, and no-JavaScript contracts were tested.
- Local multi-file writes are staged and rollback-aware for interceptable errors, not crash-atomic across host termination.
- GitHub Pages is the public atomic boundary: only a complete artifact is uploaded after build and tests pass.
- History is date-keyed; multiple runs on the same date remain available as Agent Run records rather than separate signal snapshot rows.
- Every follow-up commit must independently pass Quality, Deploy Pages, remote-main alignment, and public HTTP checks before it is called released.
