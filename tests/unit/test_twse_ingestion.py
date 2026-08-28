from __future__ import annotations

import copy
import json
import unittest

from src.ingestion.twse_openapi import IngestionError, build_snapshots


STOCKS = ("2330", "2454", "2308", "2412", "2891")
GENERAL_STOCKS = STOCKS[:-1]
ETFS = ("0050", "006208", "00878", "00919", "00965")


def _payload(value: list[dict[str, str]]) -> dict[str, object]:
    return {
        "body": json.dumps(value, ensure_ascii=False).encode("utf-8"),
        "etag": '"fixture"',
        "last_modified": "Fri, 28 Aug 2026 00:00:00 GMT",
    }


def _payloads() -> dict[str, dict[str, object]]:
    eod = [
        {
            "Date": "1150827",
            "Code": symbol,
            "OpeningPrice": "100.00",
            "HighestPrice": "105.00",
            "LowestPrice": "99.00",
            "ClosingPrice": "103.00",
            "Change": "3.0000",
            "TradeVolume": "19214481",
            "TradeValue": "1980000000",
            "Transaction": "60122",
        }
        for symbol in STOCKS + ETFS
    ]
    valuation = [
        {
            "Date": "1150827",
            "Code": symbol,
            "PEratio": "27.94",
            "DividendYield": "0.91",
            "PBratio": "9.72",
        }
        for symbol in STOCKS
    ]
    revenue = [
        {
            "出表日期": "1150817",
            "資料年月": "11507",
            "公司代號": symbol,
            "營業收入-當月營收": "467580548",
            "營業收入-上月營收": "442679969",
            "營業收入-去年當月營收": "323165707",
            "營業收入-上月比較增減(%)": "5.62",
            "營業收入-去年同月增減(%)": "44.69",
            "累計營業收入-當月累計營收": "2872064238",
            "累計營業收入-前期比較增減(%)": "37.01",
        }
        for symbol in STOCKS
    ]
    general_income = [
        {
            "出表日期": "1150828",
            "年度": "115",
            "季別": "2",
            "公司代號": symbol,
            "營業收入": "2404483690.00",
            "營業毛利（毛損）": "1611606116.00",
            "營業利益（損失）": "1425568793.00",
            "稅前淨利（淨損）": "1350000000.00",
            "淨利（淨損）歸屬於母公司業主": "1279041690.00",
            "基本每股盈餘（元）": "49.33",
        }
        for symbol in GENERAL_STOCKS
    ]
    general_balance = [
        {
            "出表日期": "1150828",
            "年度": "115",
            "季別": "2",
            "公司代號": symbol,
            "資產總計": "9375654727.00",
            "負債總計": "2901183746.00",
            "權益總計": "6474470981.00",
            "每股參考淨值": "248.05",
        }
        for symbol in GENERAL_STOCKS
    ]
    holding_income = [
        {
            "出表日期": "1150828",
            "年度": "115",
            "季別": "2",
            "公司代號": "2891",
            "利息淨收益": "84427855.00",
            "利息以外淨收益": "118597501.00",
            "繼續營業單位稅前損益": "50000000.00",
            "淨利（淨損）歸屬於母公司業主": "39537275.00",
            "基本每股盈餘（元）": "1.96",
        }
    ]
    holding_balance = [
        {
            "出表日期": "1150828",
            "年度": "115",
            "季別": "2",
            "公司代號": "2891",
            "資產總額": "9500000000.00",
            "負債總額": "8700000000.00",
            "權益總額": "800000000.00",
            "每股參考淨值": "35.50",
        }
    ]
    profiles = [
        {
            "出表日期": "1150828",
            "基金代號": symbol,
            "基金中文名稱": f"測試基金{symbol}",
            "基金類型": "指數股票型基金",
            "標的指數/追蹤指數名稱": f"測試指數{symbol}",
            "標的指數是否為客製化或需揭露相關資訊之指數": (
                "否" if symbol in {"0050", "006208"} else "是"
            ),
            "是否包含國外成分股": "是" if symbol == "00965" else "否",
            "成立日期": "1000101",
            "上市日期": "1000103",
            "發行單位數/轉換數": "100000000",
        }
        for symbol in ETFS
    ]
    return {
        "eod_prices": _payload(eod),
        "valuation": _payload(valuation),
        "monthly_revenue": _payload(revenue),
        "quarterly_income_general": _payload(general_income),
        "balance_sheet_general": _payload(general_balance),
        "quarterly_income_financial_holding": _payload(holding_income),
        "balance_sheet_financial_holding": _payload(holding_balance),
        "fund_profile": _payload(profiles),
    }


class TwseOpenApiIngestionTests(unittest.TestCase):
    def test_normalizes_all_ten_official_snapshots(self) -> None:
        snapshots = build_snapshots(
            _payloads(), fetched_at="2026-08-28T05:00:00Z"
        )
        self.assertEqual(set(snapshots), set(STOCKS + ETFS))
        self.assertTrue(all(not item["used_in_signal"] for item in snapshots.values()))
        self.assertTrue(
            all(not item["collection_policy"]["html_scraping"] for item in snapshots.values())
        )

        tsmc = snapshots["2330"]
        self.assertEqual(tsmc["facts"]["market_session"]["close"], 103.0)
        self.assertEqual(
            tsmc["facts"]["monthly_revenue"]["revenue_twd_million"],
            467580.548,
        )
        self.assertEqual(
            tsmc["facts"]["quarterly_income"]["statement_type"],
            "general_industry",
        )
        self.assertEqual(len(tsmc["resources"]), 5)

        holding = snapshots["2891"]
        self.assertEqual(
            holding["facts"]["quarterly_income"]["statement_type"],
            "financial_holding",
        )
        self.assertIn(
            "net_interest_income_twd_million",
            holding["facts"]["quarterly_income"],
        )

        etf = snapshots["00965"]
        self.assertEqual(set(etf["facts"]), {"market_session", "fund_profile"})
        self.assertTrue(etf["facts"]["fund_profile"]["includes_foreign_constituents"])
        self.assertEqual(len(etf["resources"]), 2)
        for snapshot in snapshots.values():
            self.assertTrue(snapshot["evidence_assessment"]["supporting_evidence"])
            self.assertTrue(snapshot["evidence_assessment"]["contrary_evidence"])
            self.assertTrue(snapshot["evidence_assessment"]["invalidation_conditions"])

    def test_rejects_missing_resource(self) -> None:
        payloads = _payloads()
        payloads.pop("valuation")
        with self.assertRaises(IngestionError):
            build_snapshots(payloads, fetched_at="2026-08-28T05:00:00Z")

    def test_rejects_duplicate_symbol_record(self) -> None:
        payloads = _payloads()
        duplicate = json.loads(payloads["eod_prices"]["body"].decode("utf-8"))
        duplicate.append(copy.deepcopy(duplicate[0]))
        payloads["eod_prices"] = _payload(duplicate)
        with self.assertRaises(IngestionError):
            build_snapshots(payloads, fetched_at="2026-08-28T05:00:00Z")

    def test_rejects_observation_after_fetch_time(self) -> None:
        with self.assertRaises(IngestionError):
            build_snapshots(_payloads(), fetched_at="2026-08-27T23:59:59Z")


if __name__ == "__main__":
    unittest.main()
