# Proposed tri-market universe

Status: **Owner approval required**

Version: proposal-2026-08-27

This list is an engineering proposal for data-availability and model-coverage review. It is not an investment recommendation. Every item remains proposed and disabled.

## Taiwan

| Type | Symbols |
|---|---|
| Stocks | 2330, 2454, 2308, 2412, 2891 |
| ETFs | 0050, 006208, 00878, 00919, 00965 |

## Japan

| Type | Symbols |
|---|---|
| Stocks | 7203, 6758, 8035, 7011, 9432 |
| ETFs | 1306, 1321, 1475, 1489, 2568 |

## United States

| Type | Symbols |
|---|---|
| Stocks | NVDA, MSFT, GOOGL, LMT, JNJ |
| ETFs | SPY, QQQ, SMH, CIBR, USMV |

## Approval checklist

- Verify current listing status, symbol, exchange, legal name, currency, and asset type.
- Verify official or licensed price, financial, holdings, corporate-action, and market-calendar sources.
- Review rate limits, redistribution rights, retention limits, and public Pages usage.
- Confirm liquidity and sufficient point-in-time history.
- Measure market, theme, issuer, and holdings overlap.
- Confirm the benchmark and model applicability policy for each instrument.
- Approve a versioned 5-stock + 5-ETF set per market.
- Record approver and timestamp in config/approvals.json.

Approval of the Universe does not approve the model. Production signals remain disabled until the separate backtest, calibration, data-quality, and model-version gates pass.
