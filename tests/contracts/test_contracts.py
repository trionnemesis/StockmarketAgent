from __future__ import annotations

import copy
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.pipeline import (
    CONFIG,
    FIXTURE_PATH,
    ROOT,
    SCHEMAS,
    build_signal,
    load_inputs,
)
from src.validation.contracts import (
    ContractError,
    canonical_json,
    load_json_strict,
    validate_document,
    validate_signal_contract,
    validate_source_contract,
    validate_review_contract,
    validate_universe_contract,
)


class UniverseContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (cls.universe, cls.approvals, cls.model, cls.fixture, cls.themes,
         cls.benchmarks, cls.sources, cls.review) = load_inputs()

    def test_exact_market_and_asset_counts(self) -> None:
        counts = Counter(
            (item["country"], item["asset_type"])
            for item in self.universe["instruments"]
        )
        self.assertEqual(
            counts,
            Counter(
                {
                    ("TW", "stock"): 5,
                    ("TW", "etf"): 5,
                    ("JP", "stock"): 5,
                    ("JP", "etf"): 5,
                    ("US", "stock"): 5,
                    ("US", "etf"): 5,
                }
            ),
        )

    def test_universe_schema_and_domain_contract(self) -> None:
        validate_document(self.universe, SCHEMAS / "universe.schema.json")
        validate_universe_contract(self.universe, self.approvals)

    def test_all_candidates_remain_proposed_and_disabled(self) -> None:
        self.assertFalse(self.approvals["production_signal_enabled"])
        self.assertTrue(
            all(
                item["status"] == "proposed" and item["enabled"] is False
                for item in self.universe["instruments"]
            )
        )

    def test_rejects_unapproved_enabled_candidate(self) -> None:
        mutated = copy.deepcopy(self.universe)
        mutated["instruments"][0]["enabled"] = True
        with self.assertRaises(ContractError):
            validate_universe_contract(mutated, self.approvals)

    def test_rejects_wrong_market_count(self) -> None:
        mutated = copy.deepcopy(self.universe)
        mutated["instruments"].pop()
        with self.assertRaises(ContractError):
            validate_universe_contract(mutated, self.approvals)


class StrictJsonTests(unittest.TestCase):
    def _write(self, content: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "document.json"
        path.write_text(content, encoding="utf-8")
        return path

    def test_rejects_nan(self) -> None:
        with self.assertRaises(ContractError):
            load_json_strict(self._write('{"score": NaN}'))

    def test_rejects_infinity(self) -> None:
        with self.assertRaises(ContractError):
            load_json_strict(self._write('{"score": Infinity}'))

    def test_rejects_duplicate_keys(self) -> None:
        with self.assertRaises(ContractError):
            load_json_strict(self._write('{"score": 1, "score": 2}'))

    def test_rejects_unknown_schema_property(self) -> None:
        universe = load_json_strict(CONFIG / "universe.json")
        universe["unexpected"] = True
        with self.assertRaises(ContractError):
            from src.validation.contracts import validate_schema

            schema = load_json_strict(SCHEMAS / "universe.schema.json")
            validate_schema(
                universe,
                schema,
                schema_path=SCHEMAS / "universe.schema.json",
            )


class SignalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (cls.universe, cls.approvals, cls.model, cls.fixture, cls.themes,
         cls.benchmarks, cls.sources, cls.review) = load_inputs()
        cls.signal = build_signal(
            cls.universe, cls.approvals, cls.model, cls.fixture,
            cls.themes, cls.benchmarks, cls.sources, cls.review
        )

    def test_signal_schema_and_domain_contract(self) -> None:
        validate_document(self.signal, SCHEMAS / "signal.schema.json")
        validate_signal_contract(self.signal, self.approvals)

    def test_all_horizons_are_guarded(self) -> None:
        for item in self.signal["instruments"]:
            for horizon in item["horizons"]:
                self.assertEqual(horizon["stance"], "NO_SIGNAL")
                self.assertIsNone(horizon["score"])
                self.assertEqual(horizon["confidence"], 0)
                self.assertIn("LIVE_DATA_MISSING", horizon["risk_flags"])

    def test_generation_is_deterministic(self) -> None:
        again = build_signal(
            self.universe, self.approvals, self.model, self.fixture,
            self.themes, self.benchmarks, self.sources, self.review
        )
        self.assertEqual(canonical_json(self.signal), canonical_json(again))

    def test_fixture_hash_is_stable_and_exposed(self) -> None:
        fixture = load_json_strict(FIXTURE_PATH)
        self.assertEqual(
            self.signal["source_manifest"][0]["content_hash"],
            self.signal["instruments"][0]["provenance"][0]["content_hash"],
        )
        self.assertNotIn("content_hash", fixture["source"])

    def test_selection_rationale_is_schema_bound(self) -> None:
        for candidate, signal_item in zip(self.universe["instruments"], self.signal["instruments"]):
            self.assertEqual(candidate["selection_rationale"], signal_item["selection_rationale"])

    def test_latest_signal_matches_contract(self) -> None:
        latest = load_json_strict(ROOT / "signals" / "latest.json")
        self.assertEqual(canonical_json(latest), canonical_json(self.signal))


class EvidenceReviewContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (cls.universe, _, _, _, _, cls.benchmarks, cls.sources, cls.review) = load_inputs()

    def test_all_thirty_have_structured_evidence(self) -> None:
        self.assertEqual(len(self.review["instruments"]), 30)
        for item in self.review["instruments"]:
            self.assertTrue(item["evidence"])
            self.assertEqual(item["liquidity"]["status"], "quantitative_review_pending")

    def test_source_and_review_domain_contracts(self) -> None:
        validate_source_contract(self.sources)
        validate_review_contract(self.universe, self.benchmarks, self.sources, self.review)

    def test_etfs_have_exact_tracking_index_source(self) -> None:
        for item in self.review["instruments"]:
            self.assertEqual("tracking_index" in item, item["asset_type"] == "etf")

    def test_rejects_unbound_evidence_source(self) -> None:
        mutated = copy.deepcopy(self.review)
        mutated["instruments"][0]["evidence"][0]["source_id"] = "UNKNOWN"
        with self.assertRaises(ContractError):
            validate_review_contract(self.universe, self.benchmarks, self.sources, mutated)
