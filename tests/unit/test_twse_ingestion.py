from __future__ import annotations

import copy
import json
import unittest

from src.ingestion.twse_openapi import IngestionError, build_snapshot


def _payload(value: list[dict[str, str]]) -> dict[str, object]:
    return {
        "body": json.dumps(value, ensure_ascii=False).encode("utf-8"),
        "etag": '"fixture"',
        "last_modified": "Fri, 28 Aug 2026 00:00:00 GMT",
    }


def _payloads() -> dict[str, dict[str, object]]:
    return {
        "eod_prices": _payload(
            [
                {
                    "Date": "1150827",
                    "Code": "2330",
                    "OpeningPrice": "2430.00",
                    "HighestPrice": "2435.00",
                    "LowestPrice": "2410.00",
                    "ClosingPrice": "2410.00",
                    "Change": "-5.0000",
                    "TradeVolume": "19214481",
                    "TradeValue": "46545167227",
                    "Transaction": "60122",
                }
            ]
        ),
        "valuation": _payload(
            [
                {
                    "Date": "1150827",
                    "Code": "2330",
                    "PEratio": "27.94",
                    "DividendYield": "0.91",
                    "PBratio": "9.72",
                }
            ]
        ),
        "monthly_revenue": _payload(
            [
                {
                    "出表日期": "1150817",
                    "資料年月": "11507",
                    "公司代號": "2330",
                    "營業收入-當月營收": "467580548",
                    "營業收入-上月營收": "442679969",
                    "營業收入-去年當月營收": "323165707",
                    "營業收入-上月比較增減(%)": "5.624961765550318",
                    "營業收入-去年同月增減(%)": "44.68755126916978",
                    "累計營業收入-當月累計營收": "2872064238",
                    "累計營業收入-前期比較增減(%)": "37.01215713355301",
                }
            ]
        ),
        "quarterly_income": _payload(
            [
                {
                    "出表日期": "1150828",
                    "年度": "115",
                    "季別": "2",
                    "公司代號": "2330",
                    "營業收入": "2404483690.00",
                    "營業毛利（毛損）": "1611606116.00",
                    "營業利益（損失）": "1425568793.00",
                    "淨利（淨損）歸屬於母公司業主": "1279041690.00",
                    "基本每股盈餘（元）": "49.33",
                }
            ]
        ),
        "balance_sheet": _payload(
            [
                {
                    "出表日期": "1150828",
                    "年度": "115",
                    "季別": "2",
                    "公司代號": "2330",
                    "資產總計": "9375654727.00",
                    "負債總計": "2901183746.00",
                    "權益總計": "6474470981.00",
                    "每股參考淨值": "248.05",
                }
            ]
        ),
    }


class TwseOpenApiIngestionTests(unittest.TestCase):
    def test_normalizes_official_tsmc_snapshot(self) -> None:
        snapshot = build_snapshot(
            _payloads(), fetched_at="2026-08-28T05:00:00Z"
        )
        self.assertEqual(snapshot["as_of"], "2026-08-28")
        self.assertFalse(snapshot["used_in_signal"])
        self.assertFalse(snapshot["automated_refresh_enabled"])
        self.assertFalse(snapshot["collection_policy"]["html_scraping"])
        self.assertEqual(snapshot["facts"]["market_session"]["close"], 2410.0)
        self.assertEqual(
            snapshot["facts"]["monthly_revenue"]["revenue_twd_million"],
            467580.548,
        )
        self.assertEqual(
            snapshot["facts"]["quarterly_income"]["period"], "2026-Q2"
        )
        self.assertEqual(
            snapshot["facts"]["quarterly_income"]["basic_eps_twd"], 49.33
        )
        self.assertEqual(len(snapshot["resources"]), 5)
        self.assertTrue(
            all(len(item["content_sha256"]) == 64 for item in snapshot["resources"])
        )

    def test_rejects_missing_resource(self) -> None:
        payloads = _payloads()
        payloads.pop("valuation")
        with self.assertRaises(IngestionError):
            build_snapshot(payloads, fetched_at="2026-08-28T05:00:00Z")

    def test_rejects_duplicate_symbol_record(self) -> None:
        payloads = _payloads()
        duplicate = json.loads(payloads["eod_prices"]["body"].decode("utf-8"))
        duplicate.append(copy.deepcopy(duplicate[0]))
        payloads["eod_prices"] = _payload(duplicate)
        with self.assertRaises(IngestionError):
            build_snapshot(payloads, fetched_at="2026-08-28T05:00:00Z")

    def test_rejects_observation_after_fetch_time(self) -> None:
        with self.assertRaises(IngestionError):
            build_snapshot(_payloads(), fetched_at="2026-08-27T23:59:59Z")


if __name__ == "__main__":
    unittest.main()
