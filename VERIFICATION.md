# Verification record

Observed on 2026-08-27 and re-verified on 2026-08-28. This record distinguishes generated, committed, pushed, deployed, and publicly reachable states.

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
