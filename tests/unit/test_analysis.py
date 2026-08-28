from __future__ import annotations

import copy
import unittest
from collections import Counter
from pathlib import Path

from src.analysis import (
    AnalysisInputError,
    build_research_analysis,
    calculate_confidence,
    classify_stance,
    validate_research_fixture,
)
from src.validation.contracts import canonical_json, load_json_strict, validate_document


ROOT = Path(__file__).resolve().parents[2]


class ResearchAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.universe = load_json_strict(ROOT / "config" / "universe.json")
        cls.weights = load_json_strict(ROOT / "config" / "model_weights.json")
        cls.thresholds = load_json_strict(ROOT / "config" / "action_thresholds.json")
        cls.fixture = load_json_strict(
            ROOT / "tests" / "fixtures" / "research_analysis_snapshot.json"
        )
        cls.analysis = build_research_analysis(
            cls.universe,
            cls.weights,
            cls.thresholds,
            cls.fixture,
        )

    def _instrument(self, profile_id: str) -> dict:
        return next(
            item
            for item in self.analysis["instruments"]
            if item["scenario_profile_id"] == profile_id
        )

    def test_output_schema_and_exact_universe_membership(self) -> None:
        validate_document(
            self.analysis,
            ROOT / "schemas" / "research-analysis.schema.json",
        )
        expected = [item["instrument_id"] for item in self.universe["instruments"]]
        actual = [item["instrument_id"] for item in self.analysis["instruments"]]
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 30)
        self.assertEqual(len(actual), len(set(actual)))

    def test_all_six_profiles_are_assigned_five_times(self) -> None:
        counts = Counter(
            assignment["profile_id"] for assignment in self.fixture["assignments"]
        )
        self.assertEqual(set(counts.values()), {5})
        self.assertEqual(len(counts), 6)

    def test_generation_is_deterministic(self) -> None:
        again = build_research_analysis(
            self.universe,
            self.weights,
            self.thresholds,
            self.fixture,
        )
        self.assertEqual(canonical_json(self.analysis), canonical_json(again))

    def test_spec_confidence_formula_and_weighted_horizons(self) -> None:
        profile = next(
            item for item in self.fixture["profiles"] if item["profile_id"] == "synthetic_positive"
        )
        self.assertEqual(
            calculate_confidence(profile["confidence_factors"], self.thresholds),
            75,
        )
        positive = self._instrument("synthetic_positive")
        self.assertEqual(
            [item["score"] for item in positive["horizons"]],
            [44.5, 40.75, 37.75, 34.5],
        )
        self.assertEqual(
            [item["stance"] for item in positive["horizons"]],
            ["BUY", "BUY", "BUY", "BUY"],
        )
        self.assertEqual(
            set(positive["components"]),
            {"macro", "fundamental", "valuation", "technical", "cycle", "events"},
        )

    def test_threshold_boundaries_come_from_configuration(self) -> None:
        self.assertEqual(classify_stance(25, 70, self.thresholds), "BUY")
        self.assertEqual(classify_stance(-25, 70, self.thresholds), "SELL")
        self.assertEqual(classify_stance(24, 70, self.thresholds), "HOLD")
        self.assertEqual(classify_stance(-24, 70, self.thresholds), "HOLD")
        self.assertEqual(classify_stance(25, 69, self.thresholds), "HOLD")
        self.assertEqual(classify_stance(100, 49, self.thresholds), "NO_SIGNAL")
        self.assertEqual(
            classify_stance(100, 100, self.thresholds, ["CRITICAL_MISSING"]),
            "NO_SIGNAL",
        )

    def test_risk_gate_overrides_all_four_horizons(self) -> None:
        expected = {
            "synthetic_critical_missing": "CRITICAL_MISSING",
            "synthetic_stale": "STALE_DATA",
            "synthetic_contradiction": "SOURCE_CONTRADICTION",
        }
        for profile_id, flag in expected.items():
            instrument = self._instrument(profile_id)
            self.assertTrue(instrument["data_status"]["risk_gate_triggered"])
            self.assertIn(flag, instrument["data_status"]["risk_gate_reasons"])
            for horizon in instrument["horizons"]:
                self.assertEqual(horizon["stance"], "NO_SIGNAL")
                self.assertIn(flag, horizon["risk_flags"])

    def test_directional_outputs_remain_uncalibrated_research(self) -> None:
        self.assertTrue(
            all(
                profile["confidence_factors"]["calibration_quality"] == 0
                for profile in self.fixture["profiles"]
            )
        )
        directional = 0
        for instrument in self.analysis["instruments"]:
            self.assertEqual(instrument["data_status"]["status"], "research_fixture")
            for horizon in instrument["horizons"]:
                self.assertEqual(horizon["calibration_status"], "uncalibrated")
                self.assertIn("RESEARCH_FIXTURE", horizon["risk_flags"])
                self.assertIn("MODEL_UNCALIBRATED", horizon["risk_flags"])
                directional += horizon["stance"] in {"BUY", "SELL"}
        self.assertGreater(directional, 0)

    def test_provenance_explicitly_rejects_market_fact_interpretation(self) -> None:
        provenance = self.analysis["provenance"]
        self.assertEqual(provenance["source_type"], "synthetic_research_fixture")
        self.assertEqual(provenance["license_class"], "project_fixture")
        self.assertIn("not market facts", provenance["disclaimer"])
        self.assertIn("not market facts", self.analysis["instruments"][0]["provenance"][0]["disclaimer"])

    def test_rejects_profile_input_after_as_of(self) -> None:
        mutated = copy.deepcopy(self.fixture)
        mutated["profiles"][0]["input_as_of"] = "2026-08-28"
        with self.assertRaisesRegex(AnalysisInputError, "after fixture as_of"):
            validate_research_fixture(self.universe, mutated)

    def test_rejects_source_observed_after_as_of(self) -> None:
        mutated = copy.deepcopy(self.fixture)
        mutated["source"]["observed_at"] = "2026-08-28T00:00:00Z"
        mutated["source"]["fetched_at"] = "2026-08-28T00:00:00Z"
        with self.assertRaisesRegex(AnalysisInputError, "after as_of"):
            validate_research_fixture(self.universe, mutated)

    def test_rejects_source_timestamp_after_generation_on_same_day(self) -> None:
        mutated = copy.deepcopy(self.fixture)
        mutated["source"]["observed_at"] = "2026-08-27T13:00:00Z"
        mutated["source"]["fetched_at"] = "2026-08-27T13:00:00Z"
        with self.assertRaisesRegex(AnalysisInputError, "after generated_at"):
            validate_research_fixture(self.universe, mutated)

    def test_rejects_missing_or_duplicate_universe_assignment(self) -> None:
        missing = copy.deepcopy(self.fixture)
        missing["assignments"].pop()
        with self.assertRaisesRegex(AnalysisInputError, "exactly match universe"):
            validate_research_fixture(self.universe, missing)

        duplicate = copy.deepcopy(self.fixture)
        duplicate["assignments"][-1]["instrument_id"] = duplicate["assignments"][0]["instrument_id"]
        with self.assertRaisesRegex(AnalysisInputError, "duplicate instrument assignments"):
            validate_research_fixture(self.universe, duplicate)

    def test_rejects_non_unit_model_weight_sum(self) -> None:
        mutated = copy.deepcopy(self.weights)
        mutated["horizons"]["week_1"]["technical"] = 0.44
        with self.assertRaisesRegex(AnalysisInputError, "weights must sum to 1"):
            build_research_analysis(
                self.universe,
                mutated,
                self.thresholds,
                self.fixture,
            )


if __name__ == "__main__":
    unittest.main()
