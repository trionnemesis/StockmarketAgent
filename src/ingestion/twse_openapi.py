from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping
from urllib.request import Request, urlopen

from src.ingestion.twse_archive import ArchiveError, archive_and_publish


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = ROOT / "data" / "observations" / "twse"
USER_AGENT = (
    "StockmarketAgent/0.3 "
    "(+https://github.com/trionnemesis/StockmarketAgent; research-only)"
)
MINIMUM_INTERVAL_SECONDS = 2

INSTRUMENT_SPECS = (
    {"instrument_id": "TW:STOCK:2330", "symbol": "2330", "slug": "tsmc", "name_zh": "台積電", "asset_type": "stock", "financial_statement_type": "general_industry"},
    {"instrument_id": "TW:STOCK:2454", "symbol": "2454", "slug": "mediatek", "name_zh": "聯發科", "asset_type": "stock", "financial_statement_type": "general_industry"},
    {"instrument_id": "TW:STOCK:2308", "symbol": "2308", "slug": "delta-electronics", "name_zh": "台達電", "asset_type": "stock", "financial_statement_type": "general_industry"},
    {"instrument_id": "TW:STOCK:2412", "symbol": "2412", "slug": "chunghwa-telecom", "name_zh": "中華電信", "asset_type": "stock", "financial_statement_type": "general_industry"},
    {"instrument_id": "TW:STOCK:2891", "symbol": "2891", "slug": "ctbc-financial", "name_zh": "中信金", "asset_type": "stock", "financial_statement_type": "financial_holding"},
    {"instrument_id": "TW:ETF:0050", "symbol": "0050", "slug": "yuanta-taiwan-50", "name_zh": "元大台灣50", "asset_type": "etf"},
    {"instrument_id": "TW:ETF:006208", "symbol": "006208", "slug": "fubon-taiwan-50", "name_zh": "富邦台50", "asset_type": "etf"},
    {"instrument_id": "TW:ETF:00878", "symbol": "00878", "slug": "cathay-esg-high-dividend", "name_zh": "國泰永續高股息", "asset_type": "etf"},
    {"instrument_id": "TW:ETF:00919", "symbol": "00919", "slug": "capital-tip-customized-high-dividend", "name_zh": "群益台灣精選高息", "asset_type": "etf"},
    {"instrument_id": "TW:ETF:00965", "symbol": "00965", "slug": "yuanta-global-aerospace-defense", "name_zh": "元大全球航太與防衛科技", "asset_type": "etf"},
)

PAYLOAD_SPECS = (
    {"payload_id": "eod_prices", "resource_id": "eod_prices", "source_id": "TWSE_OGL_EOD", "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL", "dataset_url": "https://data.gov.tw/dataset/11549", "code_key": "Code"},
    {"payload_id": "valuation", "resource_id": "valuation", "source_id": "TWSE_OGL_EOD", "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL", "dataset_url": "https://data.gov.tw/dataset/11547", "code_key": "Code"},
    {"payload_id": "monthly_revenue", "resource_id": "monthly_revenue", "source_id": "TWSE_OGL_FINANCIALS", "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap05_L", "dataset_url": "https://data.gov.tw/dataset/18420", "code_key": "公司代號"},
    {"payload_id": "quarterly_income_general", "resource_id": "quarterly_income", "source_id": "TWSE_OGL_FINANCIALS", "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci", "dataset_url": "https://data.gov.tw/dataset/91998", "code_key": "公司代號"},
    {"payload_id": "balance_sheet_general", "resource_id": "balance_sheet", "source_id": "TWSE_OGL_FINANCIALS", "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap07_L_ci", "dataset_url": "https://data.gov.tw/dataset/94831", "code_key": "公司代號"},
    {"payload_id": "quarterly_income_financial_holding", "resource_id": "quarterly_income", "source_id": "TWSE_OGL_FINANCIALS", "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_fh", "dataset_url": "https://data.gov.tw/dataset/91999", "code_key": "公司代號"},
    {"payload_id": "balance_sheet_financial_holding", "resource_id": "balance_sheet", "source_id": "TWSE_OGL_FINANCIALS", "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap07_L_fh", "dataset_url": "https://data.gov.tw/dataset/94832", "code_key": "公司代號"},
    {"payload_id": "fund_profile", "resource_id": "fund_profile", "source_id": "TWSE_OGL_ETF", "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap47_L", "dataset_url": "https://data.gov.tw/dataset/157399", "code_key": "基金代號"},
)


class IngestionError(ValueError):
    """Raised when an official response cannot be normalized safely."""


def _roc_date(value: str) -> str:
    digits = value.strip()
    if len(digits) != 7 or not digits.isdigit():
        raise IngestionError(f"invalid ROC date: {value!r}")
    return f"{int(digits[:3]) + 1911:04d}-{digits[3:5]}-{digits[5:7]}"


def _roc_month(value: str) -> str:
    digits = value.strip()
    if len(digits) != 5 or not digits.isdigit():
        raise IngestionError(f"invalid ROC month: {value!r}")
    return f"{int(digits[:3]) + 1911:04d}-{digits[3:5]}"


def _decimal(record: Mapping[str, Any], key: str) -> Decimal:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise IngestionError(f"missing numeric field {key}")
    try:
        return Decimal(value.replace(",", "").strip())
    except InvalidOperation as exc:
        raise IngestionError(f"invalid numeric field {key}: {value!r}") from exc


def _number(record: Mapping[str, Any], key: str, decimals: int = 2) -> float:
    return round(float(_decimal(record, key)), decimals)


def _integer(record: Mapping[str, Any], key: str) -> int:
    value = _decimal(record, key)
    if value != value.to_integral_value():
        raise IngestionError(f"expected integer field {key}: {value}")
    return int(value)


def _twd_million(record: Mapping[str, Any], key: str) -> float:
    return round(float(_decimal(record, key) / Decimal(1000)), 3)


def _ratio(numerator: Decimal, denominator: Decimal) -> float:
    if denominator <= 0:
        raise IngestionError("ratio denominator must be positive")
    return round(float(numerator / denominator * Decimal(100)), 2)


def _yes_no(value: Any, field: str) -> bool:
    normalized = str(value).strip()
    if normalized == "是":
        return True
    if normalized == "否":
        return False
    raise IngestionError(f"invalid yes/no field {field}: {value!r}")


def _records(raw: bytes, payload_id: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"{payload_id}: response is not UTF-8 JSON") from exc
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise IngestionError(f"{payload_id}: response must be an array of objects")
    return value


def _payload_spec(payload_id: str) -> dict[str, str]:
    return next(item for item in PAYLOAD_SPECS if item["payload_id"] == payload_id)


def _required_payload_ids(instrument: Mapping[str, str]) -> tuple[str, ...]:
    if instrument["asset_type"] == "etf":
        return ("eod_prices", "fund_profile")
    suffix = "financial_holding" if instrument["financial_statement_type"] == "financial_holding" else "general"
    return (
        "eod_prices",
        "valuation",
        "monthly_revenue",
        f"quarterly_income_{suffix}",
        f"balance_sheet_{suffix}",
    )


def _one_record(records: list[dict[str, Any]], payload_id: str, symbol: str) -> dict[str, Any]:
    spec = _payload_spec(payload_id)
    matches = [item for item in records if str(item.get(spec["code_key"], "")).strip() == symbol]
    if len(matches) != 1:
        raise IngestionError(f"{payload_id}: expected exactly one {symbol} record, found {len(matches)}")
    return matches[0]


def _resource_observed_at(payload_id: str, record: Mapping[str, Any]) -> str:
    if payload_id in {"eod_prices", "valuation"}:
        return _roc_date(str(record["Date"]))
    return _roc_date(str(record["出表日期"]))


def _market_fact(record: Mapping[str, Any], observed_at: str) -> dict[str, Any]:
    return {
        "source_resource_id": "eod_prices",
        "date": observed_at,
        "currency": "TWD",
        "open": _number(record, "OpeningPrice"),
        "high": _number(record, "HighestPrice"),
        "low": _number(record, "LowestPrice"),
        "close": _number(record, "ClosingPrice"),
        "change": _number(record, "Change", 4),
        "volume_shares": _integer(record, "TradeVolume"),
        "trade_value_twd": _integer(record, "TradeValue"),
        "transaction_count": _integer(record, "Transaction"),
    }


def _stock_facts(
    records: Mapping[str, Mapping[str, Any]],
    observed_dates: Mapping[str, str],
    statement_type: str,
) -> dict[str, Any]:
    valuation = records["valuation"]
    revenue = records["monthly_revenue"]
    income_key = "quarterly_income_financial_holding" if statement_type == "financial_holding" else "quarterly_income_general"
    balance_key = "balance_sheet_financial_holding" if statement_type == "financial_holding" else "balance_sheet_general"
    income = records[income_key]
    balance = records[balance_key]
    asset_key = "資產總額" if statement_type == "financial_holding" else "資產總計"
    liability_key = "負債總額" if statement_type == "financial_holding" else "負債總計"
    equity_key = "權益總額" if statement_type == "financial_holding" else "權益總計"
    total_assets = _decimal(balance, asset_key)
    total_liabilities = _decimal(balance, liability_key)

    quarterly_income: dict[str, Any] = {
        "source_resource_id": "quarterly_income",
        "statement_type": statement_type,
        "published_date": observed_dates[income_key],
        "period": f"{int(str(income['年度'])) + 1911}-Q{income['季別']}",
        "period_scope": "year_to_date",
        "currency": "TWD",
        "unit": "million",
        "pre_tax_income_twd_million": _twd_million(income, "繼續營業單位稅前損益" if statement_type == "financial_holding" else "稅前淨利（淨損）"),
        "net_income_parent_twd_million": _twd_million(income, "淨利（淨損）歸屬於母公司業主"),
        "basic_eps_twd": _number(income, "基本每股盈餘（元）"),
    }
    if statement_type == "general_industry":
        income_revenue = _decimal(income, "營業收入")
        gross_profit = _decimal(income, "營業毛利（毛損）")
        operating_income = _decimal(income, "營業利益（損失）")
        net_income_parent = _decimal(income, "淨利（淨損）歸屬於母公司業主")
        quarterly_income.update({
            "revenue_twd_million": _twd_million(income, "營業收入"),
            "gross_profit_twd_million": _twd_million(income, "營業毛利（毛損）"),
            "operating_income_twd_million": _twd_million(income, "營業利益（損失）"),
            "gross_margin_percent": _ratio(gross_profit, income_revenue),
            "operating_margin_percent": _ratio(operating_income, income_revenue),
            "net_margin_parent_percent": _ratio(net_income_parent, income_revenue),
        })
    else:
        quarterly_income.update({
            "net_interest_income_twd_million": _twd_million(income, "利息淨收益"),
            "non_interest_income_twd_million": _twd_million(income, "利息以外淨收益"),
        })

    return {
        "valuation": {
            "source_resource_id": "valuation",
            "date": observed_dates["valuation"],
            "pe_ratio": _number(valuation, "PEratio"),
            "pb_ratio": _number(valuation, "PBratio"),
            "dividend_yield_percent": _number(valuation, "DividendYield"),
        },
        "monthly_revenue": {
            "source_resource_id": "monthly_revenue",
            "published_date": observed_dates["monthly_revenue"],
            "period": _roc_month(str(revenue["資料年月"])),
            "currency": "TWD",
            "unit": "million",
            "revenue_twd_million": _twd_million(revenue, "營業收入-當月營收"),
            "previous_month_twd_million": _twd_million(revenue, "營業收入-上月營收"),
            "prior_year_month_twd_million": _twd_million(revenue, "營業收入-去年當月營收"),
            "month_over_month_percent": _number(revenue, "營業收入-上月比較增減(%)"),
            "year_over_year_percent": _number(revenue, "營業收入-去年同月增減(%)"),
            "year_to_date_twd_million": _twd_million(revenue, "累計營業收入-當月累計營收"),
            "year_to_date_yoy_percent": _number(revenue, "累計營業收入-前期比較增減(%)"),
            "audit_status": "company_reported_unaudited",
        },
        "quarterly_income": quarterly_income,
        "balance_sheet": {
            "source_resource_id": "balance_sheet",
            "statement_type": statement_type,
            "published_date": observed_dates[balance_key],
            "period": f"{int(str(balance['年度'])) + 1911}-Q{balance['季別']}",
            "currency": "TWD",
            "unit": "million",
            "total_assets_twd_million": _twd_million(balance, asset_key),
            "total_liabilities_twd_million": _twd_million(balance, liability_key),
            "total_equity_twd_million": _twd_million(balance, equity_key),
            "book_value_per_share_twd": _number(balance, "每股參考淨值"),
            "liabilities_to_assets_percent": _ratio(total_liabilities, total_assets),
        },
    }


def _fund_fact(record: Mapping[str, Any], observed_at: str) -> dict[str, Any]:
    return {
        "source_resource_id": "fund_profile",
        "profile_date": observed_at,
        "fund_type": str(record["基金類型"]).strip(),
        "official_name": str(record["基金中文名稱"]).strip(),
        "tracking_index_name": str(record["標的指數/追蹤指數名稱"]).strip(),
        "custom_index_or_disclosure_required": _yes_no(record["標的指數是否為客製化或需揭露相關資訊之指數"], "標的指數是否為客製化或需揭露相關資訊之指數"),
        "includes_foreign_constituents": _yes_no(record["是否包含國外成分股"], "是否包含國外成分股"),
        "inception_date": _roc_date(str(record["成立日期"])),
        "listing_date": _roc_date(str(record["上市日期"])),
        "issued_units": _integer(record, "發行單位數/轉換數"),
    }


def _evidence_assessment(asset_type: str) -> dict[str, Any]:
    supporting = ["官方 EOD 單一代號紀錄已通過日期、OHLC、成交量與來源雜湊驗證。"]
    if asset_type == "stock":
        supporting.append("估值、月營收與適用產業別的季度財務皆有同代號官方紀錄。")
        contrary = [
            "修訂感知 archive 從 C1 baseline 開始；baseline 以前的完整 PIT 修訂歷史仍不可得。",
            "單日行情與未基準化估值不足以支持方向性投資結論。",
        ]
    else:
        supporting.append("基金代號、基金類型、上市日與追蹤指數皆有同代號官方紀錄。")
        contrary = [
            "ETF 不適用公司月營收與公司財務報表，不能以個股基本面欄位比較。",
            "尚缺 PIT 持股、NAV、折溢價與可再發布的 benchmark 報酬序列。",
        ]
    return {
        "scope": "data_quality_context_only",
        "used_in_signal": False,
        "supporting_evidence": supporting,
        "contrary_evidence": contrary,
        "invalidation_conditions": [
            "代號、資產類型或來源綁定不一致時，整份快照失效。",
            "官方後續修訂改變已保存事實時，必須以新版本取代並保留修訂紀錄。",
            "資源日期晚於取得時間、必要紀錄不是唯一一筆或契約驗證失敗時，拒絕發布。",
        ],
    }


def build_snapshots(payloads: Mapping[str, Mapping[str, Any]], *, fetched_at: str) -> dict[str, dict[str, Any]]:
    try:
        parsed_fetched_at = datetime.fromisoformat(fetched_at[:-1] + "+00:00" if fetched_at.endswith("Z") else fetched_at)
    except ValueError as exc:
        raise IngestionError("fetched_at must be an ISO date-time") from exc
    if parsed_fetched_at.tzinfo is None:
        raise IngestionError("fetched_at must include a timezone")

    expected_payload_ids = {item["payload_id"] for item in PAYLOAD_SPECS}
    if set(payloads) != expected_payload_ids:
        raise IngestionError(f"payload set mismatch: expected {sorted(expected_payload_ids)}, got {sorted(payloads)}")
    records_by_payload: dict[str, list[dict[str, Any]]] = {}
    for spec in PAYLOAD_SPECS:
        raw = payloads[spec["payload_id"]].get("body")
        if not isinstance(raw, bytes):
            raise IngestionError(f"{spec['payload_id']}: body must be bytes")
        records_by_payload[spec["payload_id"]] = _records(raw, spec["payload_id"])

    snapshots: dict[str, dict[str, Any]] = {}
    for instrument in INSTRUMENT_SPECS:
        symbol = instrument["symbol"]
        required_ids = _required_payload_ids(instrument)
        selected = {payload_id: _one_record(records_by_payload[payload_id], payload_id, symbol) for payload_id in required_ids}
        observed_dates = {payload_id: _resource_observed_at(payload_id, selected[payload_id]) for payload_id in required_ids}
        resources = []
        for payload_id in required_ids:
            spec = _payload_spec(payload_id)
            payload = payloads[payload_id]
            resources.append({
                "resource_id": spec["resource_id"],
                "source_id": spec["source_id"],
                "endpoint": spec["endpoint"],
                "dataset_url": spec["dataset_url"],
                "observed_at": observed_dates[payload_id],
                "records_received": len(records_by_payload[payload_id]),
                "content_sha256": hashlib.sha256(payload["body"]).hexdigest(),
                "etag": payload.get("etag"),
                "last_modified": payload.get("last_modified"),
                "raw_retained": False,
            })
        facts = {"market_session": _market_fact(selected["eod_prices"], observed_dates["eod_prices"])}
        if instrument["asset_type"] == "stock":
            facts.update(_stock_facts(selected, observed_dates, instrument["financial_statement_type"]))
            available = ["market_session", "valuation", "monthly_revenue", "quarterly_income", "balance_sheet"]
            not_applicable = ["fund_profile"]
            gaps = ["pre_archive_revision_history", "full_eod_history", "benchmark_return_series", "corporate_action_history"]
        else:
            facts["fund_profile"] = _fund_fact(selected["fund_profile"], observed_dates["fund_profile"])
            available = ["market_session", "fund_profile"]
            not_applicable = ["valuation", "monthly_revenue", "quarterly_income", "balance_sheet"]
            gaps = ["pre_archive_revision_history", "full_eod_history", "pit_holdings", "nav_and_premium_discount_history", "benchmark_return_series"]
        as_of = max(observed_dates.values())
        if as_of > parsed_fetched_at.date().isoformat():
            raise IngestionError(f"{symbol}: official observation date is after fetched_at")
        snapshots[symbol] = {
            "schema_version": "1.1.0",
            "instrument_id": instrument["instrument_id"],
            "symbol": symbol,
            "slug": instrument["slug"],
            "name_zh": instrument["name_zh"],
            "asset_type": instrument["asset_type"],
            "as_of": as_of,
            "fetched_at": fetched_at,
            "mode": "observed_research_snapshot",
            "used_in_signal": False,
            "automated_refresh_enabled": False,
            "attribution": {
                "publisher": "金融監督管理委員會證券期貨局／臺灣證券交易所",
                "license_name": "政府資料開放授權條款－第1版",
                "license_url": "https://data.gov.tw/license",
                "terms_url": "https://www.twse.com.tw/zh/terms/use.html",
                "api_documentation_url": "https://openapi.twse.com.tw/v1/swagger.json",
                "statement": "金融監督管理委員會證券期貨局／臺灣證券交易所（2026）開放資料；依政府資料開放授權條款－第1版使用。",
            },
            "collection_policy": {
                "interface": "documented_openapi",
                "html_scraping": False,
                "minimum_interval_seconds": MINIMUM_INTERVAL_SECONDS,
                "user_agent": USER_AGENT,
                "robots_url": "https://openapi.twse.com.tw/robots.txt",
                "robots_status": "not_published_404_checked_2026-08-28",
                "basis": "Only documented OpenAPI endpoints tied to OGL datasets are collected; generic TWSE/MOPS HTML crawling is excluded.",
            },
            "normalization": {
                "roc_calendar": "Gregorian year = ROC year + 1911",
                "financial_source_unit": "TWD thousands",
                "financial_display_unit": "TWD millions",
                "ratio_rounding_decimals": 2,
            },
            "coverage": {"available_fact_groups": available, "not_applicable_fact_groups": not_applicable, "gaps": gaps},
            "resources": resources,
            "facts": facts,
            "evidence_assessment": _evidence_assessment(instrument["asset_type"]),
            "warnings": [
                "Revision-aware history starts at the committed C1 baseline; earlier PIT revisions are unavailable.",
                "Snapshot facts and evidence assessment are not used to calculate or upgrade research attitudes.",
                "No automatic refresh schedule is enabled.",
            ],
        }
    return snapshots


def fetch_payloads(*, timeout_seconds: int = 90) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(PAYLOAD_SPECS):
        if index:
            time.sleep(MINIMUM_INTERVAL_SECONDS)
        request = Request(spec["endpoint"], headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                payloads[spec["payload_id"]] = {
                    "body": response.read(),
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
        except OSError as exc:
            raise IngestionError(f"{spec['payload_id']}: fetch failed: {exc}") from exc
    return payloads


def write_atomically(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch manual, research-only snapshots for the ten Taiwan candidates from TWSE OGL OpenAPI")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--fetched-at")
    args = parser.parse_args()
    fetched_at = args.fetched_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    try:
        snapshots = build_snapshots(fetch_payloads(timeout_seconds=args.timeout), fetched_at=fetched_at)
        archive_result = archive_and_publish(
            snapshots,
            observation_dir=args.output_dir,
            evaluated_at=fetched_at,
        )
    except (IngestionError, ArchiveError) as exc:
        print(f"ingestion error: {exc}")
        return 1
    print(json.dumps({
        "status": "success",
        "as_of": max(item["as_of"] for item in snapshots.values()),
        "instruments": len(snapshots),
        "resources_fetched": len(PAYLOAD_SPECS),
        "output_dir": str(args.output_dir),
        "archive": archive_result,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
