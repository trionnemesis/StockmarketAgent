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


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "data" / "observations" / "twse" / "2330.json"
USER_AGENT = (
    "StockmarketAgent/0.2 "
    "(+https://github.com/trionnemesis/StockmarketAgent; research-only)"
)
MINIMUM_INTERVAL_SECONDS = 2

RESOURCE_SPECS = (
    {
        "resource_id": "eod_prices",
        "source_id": "TWSE_OGL_EOD",
        "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
        "dataset_url": "https://data.gov.tw/dataset/11549",
    },
    {
        "resource_id": "valuation",
        "source_id": "TWSE_OGL_EOD",
        "endpoint": "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL",
        "dataset_url": "https://data.gov.tw/dataset/11547",
    },
    {
        "resource_id": "monthly_revenue",
        "source_id": "TWSE_OGL_FINANCIALS",
        "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap05_L",
        "dataset_url": "https://data.gov.tw/dataset/18420",
    },
    {
        "resource_id": "quarterly_income",
        "source_id": "TWSE_OGL_FINANCIALS",
        "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap06_L_ci",
        "dataset_url": "https://data.gov.tw/dataset/91998",
    },
    {
        "resource_id": "balance_sheet",
        "source_id": "TWSE_OGL_FINANCIALS",
        "endpoint": "https://openapi.twse.com.tw/v1/opendata/t187ap07_L_ci",
        "dataset_url": "https://data.gov.tw/dataset/94831",
    },
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


def _records(raw: bytes, resource_id: str) -> list[dict[str, Any]]:
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"{resource_id}: response is not UTF-8 JSON") from exc
    if not isinstance(value, list) or not all(isinstance(item, dict) for item in value):
        raise IngestionError(f"{resource_id}: response must be an array of objects")
    return value


def _one_record(records: list[dict[str, Any]], resource_id: str) -> dict[str, Any]:
    code_key = "Code" if resource_id in {"eod_prices", "valuation"} else "公司代號"
    matches = [item for item in records if str(item.get(code_key, "")).strip() == "2330"]
    if len(matches) != 1:
        raise IngestionError(
            f"{resource_id}: expected exactly one 2330 record, found {len(matches)}"
        )
    return matches[0]


def build_snapshot(
    payloads: Mapping[str, Mapping[str, Any]], *, fetched_at: str
) -> dict[str, Any]:
    try:
        parsed_fetched_at = datetime.fromisoformat(
            fetched_at[:-1] + "+00:00" if fetched_at.endswith("Z") else fetched_at
        )
    except ValueError as exc:
        raise IngestionError("fetched_at must be an ISO date-time") from exc
    if parsed_fetched_at.tzinfo is None:
        raise IngestionError("fetched_at must include a timezone")

    expected_ids = {item["resource_id"] for item in RESOURCE_SPECS}
    if set(payloads) != expected_ids:
        raise IngestionError(
            f"resource set mismatch: expected {sorted(expected_ids)}, got {sorted(payloads)}"
        )

    records_by_id: dict[str, list[dict[str, Any]]] = {}
    record_by_id: dict[str, dict[str, Any]] = {}
    resources: list[dict[str, Any]] = []
    for spec in RESOURCE_SPECS:
        resource_id = spec["resource_id"]
        raw = payloads[resource_id].get("body")
        if not isinstance(raw, bytes):
            raise IngestionError(f"{resource_id}: body must be bytes")
        records = _records(raw, resource_id)
        record = _one_record(records, resource_id)
        records_by_id[resource_id] = records
        record_by_id[resource_id] = record

    eod = record_by_id["eod_prices"]
    valuation = record_by_id["valuation"]
    revenue = record_by_id["monthly_revenue"]
    income = record_by_id["quarterly_income"]
    balance = record_by_id["balance_sheet"]

    observed_dates = {
        "eod_prices": _roc_date(str(eod["Date"])),
        "valuation": _roc_date(str(valuation["Date"])),
        "monthly_revenue": _roc_date(str(revenue["出表日期"])),
        "quarterly_income": _roc_date(str(income["出表日期"])),
        "balance_sheet": _roc_date(str(balance["出表日期"])),
    }
    for spec in RESOURCE_SPECS:
        resource_id = spec["resource_id"]
        payload = payloads[resource_id]
        resources.append(
            {
                "resource_id": resource_id,
                "source_id": spec["source_id"],
                "endpoint": spec["endpoint"],
                "dataset_url": spec["dataset_url"],
                "observed_at": observed_dates[resource_id],
                "records_received": len(records_by_id[resource_id]),
                "content_sha256": hashlib.sha256(payload["body"]).hexdigest(),
                "etag": payload.get("etag"),
                "last_modified": payload.get("last_modified"),
                "raw_retained": False,
            }
        )

    income_revenue = _decimal(income, "營業收入")
    gross_profit = _decimal(income, "營業毛利（毛損）")
    operating_income = _decimal(income, "營業利益（損失）")
    net_income_parent = _decimal(income, "淨利（淨損）歸屬於母公司業主")
    total_assets = _decimal(balance, "資產總計")
    total_liabilities = _decimal(balance, "負債總計")

    facts = {
        "market_session": {
            "source_resource_id": "eod_prices",
            "date": observed_dates["eod_prices"],
            "currency": "TWD",
            "open": _number(eod, "OpeningPrice"),
            "high": _number(eod, "HighestPrice"),
            "low": _number(eod, "LowestPrice"),
            "close": _number(eod, "ClosingPrice"),
            "change": _number(eod, "Change", 4),
            "volume_shares": _integer(eod, "TradeVolume"),
            "trade_value_twd": _integer(eod, "TradeValue"),
            "transaction_count": _integer(eod, "Transaction"),
        },
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
        "quarterly_income": {
            "source_resource_id": "quarterly_income",
            "published_date": observed_dates["quarterly_income"],
            "period": f"{int(str(income['年度'])) + 1911}-Q{income['季別']}",
            "period_scope": "year_to_date",
            "currency": "TWD",
            "unit": "million",
            "revenue_twd_million": _twd_million(income, "營業收入"),
            "gross_profit_twd_million": _twd_million(income, "營業毛利（毛損）"),
            "operating_income_twd_million": _twd_million(income, "營業利益（損失）"),
            "net_income_parent_twd_million": _twd_million(income, "淨利（淨損）歸屬於母公司業主"),
            "basic_eps_twd": _number(income, "基本每股盈餘（元）"),
            "gross_margin_percent": _ratio(gross_profit, income_revenue),
            "operating_margin_percent": _ratio(operating_income, income_revenue),
            "net_margin_parent_percent": _ratio(net_income_parent, income_revenue),
        },
        "balance_sheet": {
            "source_resource_id": "balance_sheet",
            "published_date": observed_dates["balance_sheet"],
            "period": f"{int(str(balance['年度'])) + 1911}-Q{balance['季別']}",
            "currency": "TWD",
            "unit": "million",
            "total_assets_twd_million": _twd_million(balance, "資產總計"),
            "total_liabilities_twd_million": _twd_million(balance, "負債總計"),
            "total_equity_twd_million": _twd_million(balance, "權益總計"),
            "book_value_per_share_twd": _number(balance, "每股參考淨值"),
            "liabilities_to_assets_percent": _ratio(total_liabilities, total_assets),
        },
    }

    as_of = max(observed_dates.values())
    if as_of > parsed_fetched_at.date().isoformat():
        raise IngestionError("official observation date is after fetched_at")
    return {
        "schema_version": "1.0.0",
        "instrument_id": "TW:STOCK:2330",
        "symbol": "2330",
        "name_zh": "台積電",
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
            "statement": (
                "金融監督管理委員會證券期貨局／臺灣證券交易所（2026）開放資料；"
                "依政府資料開放授權條款－第1版使用。"
            ),
        },
        "collection_policy": {
            "interface": "documented_openapi",
            "html_scraping": False,
            "minimum_interval_seconds": MINIMUM_INTERVAL_SECONDS,
            "user_agent": USER_AGENT,
            "robots_url": "https://openapi.twse.com.tw/robots.txt",
            "robots_status": "not_published_404_checked_2026-08-28",
            "basis": (
                "Only documented OpenAPI endpoints tied to OGL datasets are collected; "
                "generic TWSE/MOPS HTML crawling is excluded."
            ),
        },
        "normalization": {
            "roc_calendar": "Gregorian year = ROC year + 1911",
            "financial_source_unit": "TWD thousands",
            "financial_display_unit": "TWD millions",
            "ratio_rounding_decimals": 2,
        },
        "resources": resources,
        "facts": facts,
        "warnings": [
            "Point-in-time revision history is incomplete.",
            "Snapshot facts are not used to calculate or upgrade research attitudes.",
            "No automatic refresh schedule is enabled.",
        ],
    }


def fetch_payloads(*, timeout_seconds: int = 90) -> dict[str, dict[str, Any]]:
    payloads: dict[str, dict[str, Any]] = {}
    for index, spec in enumerate(RESOURCE_SPECS):
        if index:
            time.sleep(MINIMUM_INTERVAL_SECONDS)
        request = Request(
            spec["endpoint"],
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                body = response.read()
                payloads[spec["resource_id"]] = {
                    "body": body,
                    "etag": response.headers.get("ETag"),
                    "last_modified": response.headers.get("Last-Modified"),
                }
        except OSError as exc:
            raise IngestionError(f"{spec['resource_id']}: fetch failed: {exc}") from exc
    return payloads


def write_atomically(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
        + "\n"
    ).encode("utf-8")
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch a manual, research-only TSMC snapshot from TWSE OGL OpenAPI"
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--fetched-at")
    args = parser.parse_args()
    fetched_at = args.fetched_at or datetime.now(timezone.utc).replace(
        microsecond=0
    ).isoformat().replace("+00:00", "Z")
    try:
        snapshot = build_snapshot(
            fetch_payloads(timeout_seconds=args.timeout), fetched_at=fetched_at
        )
        write_atomically(args.output, snapshot)
    except IngestionError as exc:
        print(f"ingestion error: {exc}")
        return 1
    print(
        json.dumps(
            {
                "status": "success",
                "instrument_id": snapshot["instrument_id"],
                "as_of": snapshot["as_of"],
                "resources": len(snapshot["resources"]),
                "output": str(args.output),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
