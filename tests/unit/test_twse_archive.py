from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.ingestion.twse_archive import (
    ArchiveError,
    archive_and_publish,
    evaluate_freshness,
    load_and_validate_store,
)
from src.pipeline import CONFIG, ROOT
from src.validation.contracts import ContractError, load_json_strict


class TaiwanObservationArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.universe = load_json_strict(CONFIG / "universe.json")
        cls.sources = load_json_strict(CONFIG / "sources.json")
        cls.calendar = load_json_strict(CONFIG / "twse_calendar.json")
        cls.snapshots = {
            path.stem: load_json_strict(path)
            for path in sorted((ROOT / "data" / "observations" / "twse").glob("*.json"))
            if path.stem.isdigit()
        }

    def _copy_latest(self, root: Path) -> None:
        for symbol, snapshot in self.snapshots.items():
            (root / f"{symbol}.json").write_text(
                json.dumps(snapshot, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

    def test_initial_archive_catalog_and_freshness(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_latest(root)
            result = archive_and_publish(
                self.snapshots,
                observation_dir=root,
                evaluated_at="2026-08-28T05:56:32Z",
                universe=self.universe,
                sources=self.sources,
                calendar=self.calendar,
            )
            self.assertEqual(result["initial"], 10)
            catalog, entries = load_and_validate_store(
                self.universe,
                self.sources,
                observation_dir=root,
                calendar=self.calendar,
            )
            self.assertEqual(len(entries), 10)
            self.assertEqual(len(catalog["instruments"]), 10)
            self.assertTrue(
                all(item["history_count"] == 1 for item in catalog["instruments"])
            )
            self.assertTrue(
                all(item["freshness"]["freshness"] == "fresh" for item in catalog["instruments"])
            )
            self.assertTrue(
                all(item["model_input_coverage"]["coverage_percent"] == 0 for item in catalog["instruments"])
            )

    def test_correction_lineage_and_duplicate_noop(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_latest(root)
            archive_and_publish(
                self.snapshots,
                observation_dir=root,
                evaluated_at="2026-08-28T05:56:32Z",
                universe=self.universe,
                sources=self.sources,
                calendar=self.calendar,
            )
            corrected = copy.deepcopy(self.snapshots)
            corrected["2330"]["facts"]["valuation"]["pe_ratio"] += 0.01
            corrected["2330"]["fetched_at"] = "2026-08-28T06:00:00Z"
            result = archive_and_publish(
                corrected,
                observation_dir=root,
                evaluated_at="2026-08-28T06:00:00Z",
                universe=self.universe,
                sources=self.sources,
                calendar=self.calendar,
            )
            self.assertEqual(result["corrections"], 1)
            catalog, entries = load_and_validate_store(
                self.universe,
                self.sources,
                observation_dir=root,
                calendar=self.calendar,
            )
            tsmc_entries = sorted(
                (item for item in entries.values() if item["symbol"] == "2330"),
                key=lambda item: item["revision"]["sequence"],
            )
            self.assertEqual(len(tsmc_entries), 2)
            self.assertEqual(tsmc_entries[1]["revision"]["relation"], "correction")
            self.assertEqual(
                tsmc_entries[1]["revision"]["correction_of_archive_id"],
                tsmc_entries[0]["archive_id"],
            )
            duplicate = copy.deepcopy(corrected)
            duplicate["2330"]["fetched_at"] = "2026-08-28T06:30:00Z"
            result = archive_and_publish(
                duplicate,
                observation_dir=root,
                evaluated_at="2026-08-28T06:30:00Z",
                universe=self.universe,
                sources=self.sources,
                calendar=self.calendar,
            )
            self.assertEqual(result["new_archive_entries"], 0)
            self.assertEqual(result["duplicates"], 10)
            catalog_after, entries_after = load_and_validate_store(
                self.universe,
                self.sources,
                observation_dir=root,
                calendar=self.calendar,
            )
            self.assertEqual(len(entries_after), 11)
            tsmc_item = next(
                item for item in catalog_after["instruments"] if item["symbol"] == "2330"
            )
            self.assertEqual(tsmc_item["history_count"], 2)

    def test_invalid_batch_preserves_latest_and_catalog(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_latest(root)
            archive_and_publish(
                self.snapshots,
                observation_dir=root,
                evaluated_at="2026-08-28T05:56:32Z",
                universe=self.universe,
                sources=self.sources,
                calendar=self.calendar,
            )
            before_catalog = (root / "status" / "catalog.json").read_bytes()
            before_latest = (root / "2330.json").read_bytes()
            before_archives = sorted(path.relative_to(root) for path in root.glob("archive/*/*/*.json"))
            invalid = copy.deepcopy(self.snapshots)
            del invalid["2454"]["facts"]["market_session"]
            with self.assertRaises((ArchiveError, ContractError)):
                archive_and_publish(
                    invalid,
                    observation_dir=root,
                    evaluated_at="2026-08-28T06:10:00Z",
                    universe=self.universe,
                    sources=self.sources,
                    calendar=self.calendar,
                )
            self.assertEqual((root / "status" / "catalog.json").read_bytes(), before_catalog)
            self.assertEqual((root / "2330.json").read_bytes(), before_latest)
            self.assertEqual(
                sorted(path.relative_to(root) for path in root.glob("archive/*/*/*.json")),
                before_archives,
            )

    def test_holiday_stale_and_missing_semantics(self) -> None:
        missing = evaluate_freshness(
            None,
            evaluated_at="2026-09-25T01:00:00Z",
            calendar=self.calendar,
        )
        self.assertEqual(missing["market_state"], "holiday")
        self.assertEqual(missing["expected_latest_session"], "2026-09-24")
        self.assertEqual(missing["freshness"], "missing")
        fresh = evaluate_freshness(
            "2026-09-24",
            evaluated_at="2026-09-25T01:00:00Z",
            calendar=self.calendar,
        )
        self.assertEqual(fresh["freshness"], "fresh")
        stale = evaluate_freshness(
            "2026-09-23",
            evaluated_at="2026-09-25T01:00:00Z",
            calendar=self.calendar,
        )
        self.assertEqual(stale["freshness"], "stale")
        self.assertEqual(stale["sessions_behind"], 1)

    def test_tampered_archive_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._copy_latest(root)
            archive_and_publish(
                self.snapshots,
                observation_dir=root,
                evaluated_at="2026-08-28T05:56:32Z",
                universe=self.universe,
                sources=self.sources,
                calendar=self.calendar,
            )
            target = next(root.glob("archive/2330/*/*.json"))
            entry = json.loads(target.read_text(encoding="utf-8"))
            entry["observation"]["facts"]["valuation"]["pe_ratio"] += 1
            target.write_text(
                json.dumps(entry, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ArchiveError):
                load_and_validate_store(
                    self.universe,
                    self.sources,
                    observation_dir=root,
                    calendar=self.calendar,
                )


if __name__ == "__main__":
    unittest.main()
