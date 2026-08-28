from __future__ import annotations

import copy
import subprocess
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from src.pipeline import (
    ANALYSIS_FIXTURE_PATH,
    CONFIG,
    FIXTURE_PATH,
    ROOT,
    SCHEMAS,
    SOURCE_REVISION_PATHS,
    build_run_record,
    build_signal,
    load_inputs,
    source_revision,
)
from src.validation.contracts import (
    ContractError,
    canonical_json,
    load_json_strict,
    validate_action_thresholds_contract,
    validate_agent_run_contract,
    validate_approvals_contract,
    validate_document,
    validate_model_weights_contract,
    validate_schedules_contract,
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
        cls.thresholds = load_json_strict(CONFIG / "action_thresholds.json")
        cls.signal = build_signal(
            cls.universe, cls.approvals, cls.model, cls.fixture,
            cls.themes, cls.benchmarks, cls.sources, cls.review
        )

    def test_signal_schema_and_domain_contract(self) -> None:
        validate_document(self.signal, SCHEMAS / "signal.schema.json")
        validate_signal_contract(self.signal, self.approvals, self.thresholds)

    def test_all_horizons_are_research_only_and_uncalibrated(self) -> None:
        self.assertEqual(self.signal["run"]["mode"], "research_only")
        self.assertEqual(self.signal["run"]["data_kind"], "research_fixture")
        for item in self.signal["instruments"]:
            self.assertEqual(item["status"], "proposed")
            self.assertFalse(item["enabled"])
            for horizon in item["horizons"]:
                self.assertIn(
                    horizon["calibration_status"], {"uncalibrated", "not_available"}
                )
                if horizon["stance"] in {"BUY", "SELL"}:
                    self.assertGreaterEqual(horizon["confidence"], 70)
                    self.assertIn("RESEARCH_FIXTURE", horizon["risk_flags"])
                    self.assertIn("MODEL_UNCALIBRATED", horizon["risk_flags"])

    def test_summary_stances_match_three_month_horizons(self) -> None:
        expected = Counter(
            next(
                horizon["stance"]
                for horizon in item["horizons"]
                if horizon["horizon"] == "3M"
            )
            for item in self.signal["instruments"]
        )
        self.assertEqual(
            self.signal["summary"]["stances"],
            {
                stance: expected.get(stance, 0)
                for stance in ("BUY", "HOLD", "SELL", "NO_SIGNAL")
            },
        )
        self.assertEqual(sum(self.signal["summary"]["stances"].values()), 30)

    def test_rejects_low_confidence_directional_research_stance(self) -> None:
        mutated = copy.deepcopy(self.signal)
        horizon = mutated["instruments"][0]["horizons"][0]
        horizon.update(
            {
                "score": 50,
                "stance": "BUY",
                "confidence": 69,
                "calibration_status": "uncalibrated",
                "risk_flags": ["RESEARCH_FIXTURE", "MODEL_UNCALIBRATED"],
            }
        )
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_production_claim(self) -> None:
        mutated_approvals = copy.deepcopy(self.approvals)
        mutated_approvals["production_signal_enabled"] = True
        with self.assertRaises(ContractError):
            validate_signal_contract(self.signal, mutated_approvals, self.thresholds)

    def test_rejects_calibrated_claim(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["instruments"][0]["horizons"][0]["calibration_status"] = "calibrated"
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_directional_stance_for_stale_data(self) -> None:
        mutated = copy.deepcopy(self.signal)
        item = mutated["instruments"][0]
        item["data_status"]["status"] = "stale"
        horizon = item["horizons"][0]
        horizon.update(
            {
                "score": 50,
                "stance": "BUY",
                "confidence": 70,
                "calibration_status": "uncalibrated",
                "risk_flags": ["RESEARCH_FIXTURE", "MODEL_UNCALIBRATED"],
            }
        )
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_directional_stance_with_critical_missing_data(self) -> None:
        mutated = copy.deepcopy(self.signal)
        item = mutated["instruments"][0]
        item["data_status"]["critical_missing"] = ["synthetic_required_feature"]
        item["data_status"]["warnings"].append("CRITICAL_MISSING")
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_directional_stance_with_source_contradiction(self) -> None:
        mutated = copy.deepcopy(self.signal)
        item = mutated["instruments"][0]
        item["data_status"]["warnings"].append("SOURCE_CONTRADICTION")
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_unbound_horizon_source_contradiction(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["instruments"][0]["horizons"][0]["risk_flags"].append(
            "SOURCE_CONTRADICTION"
        )
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_directional_stance_when_model_is_not_applicable(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["instruments"][0]["model_applicability"]["applicable"] = False
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_unevaluated_component_with_claimed_score(self) -> None:
        mutated = copy.deepcopy(self.signal)
        component = mutated["instruments"][0]["components"]["macro"]
        component.update({"score": 1, "confidence": 1, "status": "not_evaluated"})
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_stance_that_disagrees_with_thresholds(self) -> None:
        contradictions = (
            (-100, "BUY", 100),
            (100, "SELL", 100),
            (100, "HOLD", 100),
            (100, "NO_SIGNAL", 100),
        )
        for score, stance, confidence in contradictions:
            with self.subTest(score=score, stance=stance, confidence=confidence):
                mutated = copy.deepcopy(self.signal)
                horizon = mutated["instruments"][0]["horizons"][0]
                horizon.update(
                    {
                        "score": score,
                        "stance": stance,
                        "confidence": confidence,
                        "calibration_status": "uncalibrated",
                        "risk_flags": ["RESEARCH_FIXTURE", "MODEL_UNCALIBRATED"],
                    }
                )
                with self.assertRaises(ContractError):
                    validate_signal_contract(
                        mutated, self.approvals, self.thresholds
                    )

    def test_agent_run_is_research_analysis_build(self) -> None:
        record = build_run_record(self.signal, ["signals/runs/example.json"])
        self.assertEqual(record["run_type"], "research_analysis_build")
        self.assertEqual(record["schema_versions"]["agent_run"], "1.1.0")
        validate_document(record, SCHEMAS / "agent-run.schema.json")
        validate_agent_run_contract(record)

    def test_all_immutable_run_history_uses_compatible_contracts(self) -> None:
        for path in sorted((ROOT / "agent-runs").glob("**/*.json")):
            with self.subTest(path=path.name):
                record = load_json_strict(path)
                validate_document(record, SCHEMAS / "agent-run.schema.json")
                validate_agent_run_contract(record)

    def test_research_signal_identifies_resolvable_source_revision(self) -> None:
        revision = self.signal["run"]["git_sha"]
        self.assertRegex(revision, r"^[a-f0-9]{40}$")
        resolved = subprocess.run(
            ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=ROOT,
            check=False,
            capture_output=True,
        )
        self.assertEqual(resolved.returncode, 0)
        source_diff = subprocess.run(
            ["git", "diff", "--quiet", revision, "--", *SOURCE_REVISION_PATHS],
            cwd=ROOT,
            check=False,
        )
        self.assertEqual(source_diff.returncode, 0)

    def test_source_revision_change_creates_a_distinct_immutable_run(self) -> None:
        signals = []
        for revision in ("0" * 40, "1" * 40):
            with patch("src.pipeline.source_revision", return_value=revision):
                signals.append(
                    build_signal(
                        self.universe,
                        self.approvals,
                        self.model,
                        self.fixture,
                        self.themes,
                        self.benchmarks,
                        self.sources,
                        self.review,
                    )
                )

        self.assertNotEqual(signals[0]["run"]["input_hash"], signals[1]["run"]["input_hash"])
        self.assertNotEqual(signals[0]["run"]["run_id"], signals[1]["run"]["run_id"])

    def test_rejects_resolvable_revision_with_different_build_inputs(self) -> None:
        root_revision = subprocess.run(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()[0]
        with patch.dict(
            "os.environ",
            {"STOCKMARKETAGENT_SOURCE_REVISION": root_revision},
            clear=False,
        ):
            with self.assertRaisesRegex(ContractError, "does not match current build inputs"):
                source_revision()

    def test_historical_signal_schema_is_independent_of_current_thresholds(self) -> None:
        changed_thresholds = copy.deepcopy(self.thresholds)
        changed_thresholds["buy_min"] = 40
        validate_document(self.signal, SCHEMAS / "signal.schema.json")
        with self.assertRaises(ContractError):
            validate_signal_contract(
                self.signal,
                self.approvals,
                changed_thresholds,
            )

    def test_rejects_misaligned_research_fixtures(self) -> None:
        analysis_fixture = load_json_strict(ANALYSIS_FIXTURE_PATH)
        mutated = copy.deepcopy(self.fixture)
        mutated["as_of"] = "2030-01-01"
        with self.assertRaises(ContractError):
            build_signal(
                self.universe,
                self.approvals,
                self.model,
                mutated,
                self.themes,
                self.benchmarks,
                self.sources,
                self.review,
                analysis_fixture=analysis_fixture,
            )

    def test_rejects_event_published_after_research_run(self) -> None:
        mutated = copy.deepcopy(self.fixture)
        mutated["events"][0]["published_at"] = "2030-01-01T00:00:00Z"
        with self.assertRaises(ContractError):
            build_signal(
                self.universe,
                self.approvals,
                self.model,
                mutated,
                self.themes,
                self.benchmarks,
                self.sources,
                self.review,
            )

    def test_rejects_duplicate_signal_event_id(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["events"].append(copy.deepcopy(mutated["events"][0]))
        mutated["summary"]["critical_events"] += 1
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_unknown_signal_event_instrument_reference(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["events"][0]["instrument_ids"] = ["TW:STOCK:9999"]
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_signal_event_after_generated_at(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["events"][0]["published_at"] = "2030-01-01T00:00:00Z"
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_signal_provenance_after_generated_at(self) -> None:
        mutated = copy.deepcopy(self.signal)
        provenance = mutated["instruments"][0]["provenance"][0]
        provenance["observed_at"] = "2030-01-01T00:00:00Z"
        provenance["fetched_at"] = "2030-01-01T00:00:00Z"
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

    def test_rejects_signal_generated_outside_as_of_date(self) -> None:
        mutated = copy.deepcopy(self.signal)
        mutated["run"]["generated_at"] = "2026-08-28T00:00:00Z"
        with self.assertRaises(ContractError):
            validate_signal_contract(mutated, self.approvals, self.thresholds)

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

    def test_rejects_incompatible_fallback_source(self) -> None:
        mutated = copy.deepcopy(self.sources)
        policy = next(item for item in mutated["policies"] if item["source_policy_id"] == "TW_STOCK_V1")
        corporate_actions = next(item for item in policy["coverage"] if item["data_class"] == "corporate_actions")
        corporate_actions["fallback_source_ids"] = ["TWSE_OGL_COMPANY"]
        with self.assertRaises(ContractError):
            validate_source_contract(mutated)

    def test_rejects_restricted_license_published_to_pages(self) -> None:
        mutated = copy.deepcopy(self.sources)
        source = next(
            item for item in mutated["sources"]
            if item["source_id"] == "TWSE_OGL_COMPANY"
        )
        source["license_status"] = "contract_required"
        self.assertEqual(source["feasibility"], "conditional")
        self.assertNotEqual(source["pages_policy"], "not_allowed")
        with self.assertRaises(ContractError):
            validate_source_contract(mutated)

    def test_public_evidence_never_uses_pages_prohibited_source(self) -> None:
        pages_policy = {item["source_id"]: item["pages_policy"] for item in self.sources["sources"]}
        refs = [ref for item in self.review["instruments"] for ref in item["evidence"]]
        refs.extend(ref for item in self.review["overlap_groups"] for ref in item["evidence"])
        refs.extend(ref for item in self.review["issuer_concentration"] for ref in item["evidence"])
        self.assertTrue(all(pages_policy[ref["source_id"]] != "not_allowed" for ref in refs))

    def test_etfs_have_exact_tracking_index_source(self) -> None:
        for item in self.review["instruments"]:
            self.assertEqual("tracking_index" in item, item["asset_type"] == "etf")

    def test_rejects_unbound_evidence_source(self) -> None:
        mutated = copy.deepcopy(self.review)
        mutated["instruments"][0]["evidence"][0]["source_id"] = "UNKNOWN"
        with self.assertRaises(ContractError):
            validate_review_contract(self.universe, self.benchmarks, self.sources, mutated)


class ResearchConfigurationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = load_json_strict(CONFIG / "model_weights.json")
        cls.thresholds = load_json_strict(CONFIG / "action_thresholds.json")
        cls.approvals = load_json_strict(CONFIG / "approvals.json")
        cls.schedules = load_json_strict(CONFIG / "schedules.json")

    def test_configuration_schemas_and_domain_contracts(self) -> None:
        cases = (
            (self.model, "model_weights.schema.json", validate_model_weights_contract),
            (
                self.thresholds,
                "action_thresholds.schema.json",
                validate_action_thresholds_contract,
            ),
            (self.approvals, "approvals.schema.json", validate_approvals_contract),
            (self.schedules, "schedules.schema.json", validate_schedules_contract),
        )
        for document, schema_name, validator in cases:
            with self.subTest(schema=schema_name):
                validate_document(document, SCHEMAS / schema_name)
                validator(document)

    def test_rejects_model_weight_sum_other_than_one(self) -> None:
        mutated = copy.deepcopy(self.model)
        mutated["horizons"]["week_1"]["technical"] -= 0.01
        with self.assertRaises(ContractError):
            validate_model_weights_contract(mutated)

    def test_rejects_directional_confidence_below_seventy(self) -> None:
        mutated = copy.deepcopy(self.thresholds)
        mutated["directional_confidence_min"] = 69
        with self.assertRaises(ContractError):
            validate_action_thresholds_contract(mutated)

    def test_rejects_production_approval(self) -> None:
        mutated = copy.deepcopy(self.approvals)
        mutated["production_signal_enabled"] = True
        with self.assertRaises(ContractError):
            validate_approvals_contract(mutated)

    def test_rejects_enabled_schedule_automation(self) -> None:
        mutated = copy.deepcopy(self.schedules)
        mutated["automation_enabled"] = True
        with self.assertRaises(ContractError):
            validate_schedules_contract(mutated)
