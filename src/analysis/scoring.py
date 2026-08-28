"""Deterministic scoring for explicitly synthetic research scenarios.

This module deliberately does not fetch data.  Its inputs are versioned test
fixtures, not market facts, and its directional outputs are always labelled as
uncalibrated research results.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Mapping, Sequence


COMPONENT_NAMES = (
    "macro",
    "fundamental",
    "valuation",
    "technical",
    "cycle",
    "events",
)
HORIZONS = (
    ("1W", "week_1"),
    ("1M", "month_1"),
    ("3M", "month_3"),
    ("12M", "month_12"),
)
CONFIDENCE_FACTOR_WEIGHTS = {
    "data_quality": Decimal("0.30"),
    "source_quality": Decimal("0.25"),
    "model_agreement": Decimal("0.20"),
    "calibration_quality": Decimal("0.15"),
    "regime_similarity": Decimal("0.10"),
}
BASE_RISK_FLAGS = ("RESEARCH_FIXTURE", "MODEL_UNCALIBRATED")
RESEARCH_DISCLAIMER = (
    "Synthetic research fixture inputs; not market facts or live market data."
)


class AnalysisInputError(ValueError):
    """Raised when research-analysis input violates its deterministic contract."""


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        raise AnalysisInputError(f"{label} must be a finite number")
    if isinstance(value, float) and not math.isfinite(value):
        raise AnalysisInputError(f"{label} must be a finite number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise AnalysisInputError(f"{label} must be a finite number")
    return result


def _bounded_decimal(value: Any, label: str, minimum: int, maximum: int) -> Decimal:
    result = _decimal(value, label)
    if result < minimum or result > maximum:
        raise AnalysisInputError(f"{label} must be between {minimum} and {maximum}")
    return result


def _integer(value: Any, label: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise AnalysisInputError(f"{label} must be an integer")
    if value < minimum or value > maximum:
        raise AnalysisInputError(f"{label} must be between {minimum} and {maximum}")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise AnalysisInputError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _iso_date(value: Any, label: str) -> date:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise AnalysisInputError(f"{label} must be an ISO 8601 date")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AnalysisInputError(f"{label} must be an ISO 8601 date") from exc


def _iso_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or "T" not in value:
        raise AnalysisInputError(f"{label} must be an ISO 8601 date-time")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise AnalysisInputError(f"{label} must be an ISO 8601 date-time") from exc
    if result.tzinfo is None:
        raise AnalysisInputError(f"{label} must include a timezone")
    return result


def _canonical_hash(value: Any) -> str:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise AnalysisInputError(f"fixture is not strict JSON data: {exc}") from exc
    return hashlib.sha256(encoded).hexdigest()


def _json_score(value: Decimal) -> int | float:
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded == rounded.to_integral_value():
        return int(rounded)
    return float(rounded)


def _validate_thresholds(action_thresholds: Mapping[str, Any]) -> None:
    required = {
        "confidence_no_signal_below",
        "directional_confidence_min",
        "hold_min",
        "hold_max",
        "buy_min",
        "sell_max",
        "contradiction_penalty_max",
    }
    missing = required - set(action_thresholds)
    if missing:
        raise AnalysisInputError(f"action thresholds missing {sorted(missing)}")
    confidence_floor = _integer(
        action_thresholds["confidence_no_signal_below"],
        "confidence_no_signal_below",
        0,
        100,
    )
    directional_floor = _integer(
        action_thresholds["directional_confidence_min"],
        "directional_confidence_min",
        0,
        100,
    )
    hold_min = _bounded_decimal(action_thresholds["hold_min"], "hold_min", -100, 100)
    hold_max = _bounded_decimal(action_thresholds["hold_max"], "hold_max", -100, 100)
    buy_min = _bounded_decimal(action_thresholds["buy_min"], "buy_min", -100, 100)
    sell_max = _bounded_decimal(action_thresholds["sell_max"], "sell_max", -100, 100)
    _integer(
        action_thresholds["contradiction_penalty_max"],
        "contradiction_penalty_max",
        0,
        30,
    )
    if directional_floor < confidence_floor:
        raise AnalysisInputError("directional confidence cannot be below NO_SIGNAL floor")
    if not sell_max < hold_min <= hold_max < buy_min:
        raise AnalysisInputError("SELL, HOLD, and BUY score thresholds overlap or have gaps")


def _validate_model_weights(model_weights: Mapping[str, Any]) -> None:
    if model_weights.get("status") not in {"uncalibrated", "uncalibrated_research"}:
        raise AnalysisInputError("research fixture model must remain uncalibrated")
    horizons = model_weights.get("horizons")
    if not isinstance(horizons, Mapping):
        raise AnalysisInputError("model weights must contain horizons")
    expected_horizons = {config_name for _, config_name in HORIZONS}
    if set(horizons) != expected_horizons:
        raise AnalysisInputError("model weight horizons must exactly cover 1W/1M/3M/12M")
    for horizon_name, weights in horizons.items():
        if not isinstance(weights, Mapping) or set(weights) != set(COMPONENT_NAMES):
            raise AnalysisInputError(f"{horizon_name} must weight all six components exactly")
        total = sum(
            (_bounded_decimal(weight, f"{horizon_name}.{name}", 0, 1) for name, weight in weights.items()),
            Decimal("0"),
        )
        if total != Decimal("1"):
            raise AnalysisInputError(f"{horizon_name} weights must sum to 1")


def calculate_confidence(
    confidence_factors: Mapping[str, Any],
    action_thresholds: Mapping[str, Any],
) -> int:
    """Calculate confidence with the formula in SPEC section 9.2."""

    _validate_thresholds(action_thresholds)
    expected = set(CONFIDENCE_FACTOR_WEIGHTS) | {"contradiction_penalty"}
    _exact_keys(confidence_factors, expected, "confidence_factors")
    weighted = sum(
        (
            _bounded_decimal(confidence_factors[name], name, 0, 100) * weight
            for name, weight in CONFIDENCE_FACTOR_WEIGHTS.items()
        ),
        Decimal("0"),
    )
    penalty_max = action_thresholds["contradiction_penalty_max"]
    penalty = _bounded_decimal(
        confidence_factors["contradiction_penalty"],
        "contradiction_penalty",
        0,
        penalty_max,
    )
    result = min(Decimal("100"), max(Decimal("0"), weighted - penalty))
    return int(result.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def calculate_horizon_score(
    components: Mapping[str, Mapping[str, Any]],
    weights: Mapping[str, Any],
) -> int | float:
    """Return a deterministic weighted score rounded to two decimal places."""

    if set(components) != set(COMPONENT_NAMES):
        raise AnalysisInputError("components must exactly contain the six model components")
    if set(weights) != set(COMPONENT_NAMES):
        raise AnalysisInputError("weights must exactly contain the six model components")
    total_weight = sum(
        (_bounded_decimal(weights[name], f"weight.{name}", 0, 1) for name in COMPONENT_NAMES),
        Decimal("0"),
    )
    if total_weight != Decimal("1"):
        raise AnalysisInputError("component weights must sum to 1")
    score = sum(
        (
            _bounded_decimal(components[name]["score"], f"component.{name}.score", -100, 100)
            * _decimal(weights[name], f"weight.{name}")
            for name in COMPONENT_NAMES
        ),
        Decimal("0"),
    )
    return _json_score(min(Decimal("100"), max(Decimal("-100"), score)))


def evaluate_risk_gate(data_status: Mapping[str, Any]) -> list[str]:
    """Return ordered Risk Gate reasons for missing, stale, or contradictory data."""

    expected = {"freshness", "critical_missing", "contradiction"}
    _exact_keys(data_status, expected, "data_status")
    freshness = data_status["freshness"]
    if freshness not in {"fresh", "stale"}:
        raise AnalysisInputError("data_status.freshness must be fresh or stale")
    critical_missing = data_status["critical_missing"]
    if not isinstance(critical_missing, list) or any(
        not isinstance(item, str) or not item for item in critical_missing
    ):
        raise AnalysisInputError("data_status.critical_missing must contain non-empty strings")
    if len(critical_missing) != len(set(critical_missing)):
        raise AnalysisInputError("data_status.critical_missing must be unique")
    if not isinstance(data_status["contradiction"], bool):
        raise AnalysisInputError("data_status.contradiction must be boolean")
    reasons: list[str] = []
    if critical_missing:
        reasons.append("CRITICAL_MISSING")
    if freshness == "stale":
        reasons.append("STALE_DATA")
    if data_status["contradiction"]:
        reasons.append("SOURCE_CONTRADICTION")
    return reasons


def classify_stance(
    score: int | float,
    confidence: int,
    action_thresholds: Mapping[str, Any],
    risk_gate_reasons: Sequence[str] = (),
) -> str:
    """Apply configured score/confidence thresholds after the Risk Gate."""

    _validate_thresholds(action_thresholds)
    normalized_score = _bounded_decimal(score, "score", -100, 100)
    normalized_confidence = _integer(confidence, "confidence", 0, 100)
    if risk_gate_reasons:
        return "NO_SIGNAL"
    if normalized_confidence < action_thresholds["confidence_no_signal_below"]:
        return "NO_SIGNAL"
    if (
        normalized_score >= _decimal(action_thresholds["buy_min"], "buy_min")
        and normalized_confidence >= action_thresholds["directional_confidence_min"]
    ):
        return "BUY"
    if (
        normalized_score <= _decimal(action_thresholds["sell_max"], "sell_max")
        and normalized_confidence >= action_thresholds["directional_confidence_min"]
    ):
        return "SELL"
    return "HOLD"


def _validate_component(component: Mapping[str, Any], label: str) -> None:
    _exact_keys(component, {"score", "confidence"}, label)
    _bounded_decimal(component["score"], f"{label}.score", -100, 100)
    _integer(component["confidence"], f"{label}.confidence", 0, 100)


def _validate_evidence_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise AnalysisInputError(f"{label} must be an array of non-empty strings")


def validate_research_fixture(
    universe: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> None:
    """Validate exact universe assignment and point-in-time fixture constraints."""

    fixture_keys = {
        "schema_version",
        "fixture_id",
        "as_of",
        "generated_at",
        "model_version",
        "source",
        "profiles",
        "assignments",
    }
    _exact_keys(fixture, fixture_keys, "fixture")
    if fixture["schema_version"] != "1.0.0":
        raise AnalysisInputError("unsupported research fixture schema_version")
    if not isinstance(fixture["fixture_id"], str) or not fixture["fixture_id"]:
        raise AnalysisInputError("fixture_id must be a non-empty string")
    as_of = _iso_date(fixture["as_of"], "fixture.as_of")
    generated_at = _iso_datetime(fixture["generated_at"], "fixture.generated_at")
    if generated_at.date() > as_of:
        raise AnalysisInputError("fixture.generated_at is after as_of")

    source = fixture["source"]
    if not isinstance(source, Mapping):
        raise AnalysisInputError("fixture.source must be an object")
    source_keys = {
        "source_id",
        "publisher",
        "source_type",
        "source_url",
        "observed_at",
        "fetched_at",
        "parser_version",
        "license_class",
        "raw_retained",
        "disclaimer",
    }
    _exact_keys(source, source_keys, "fixture.source")
    if source["source_type"] != "synthetic_research_fixture":
        raise AnalysisInputError("fixture source_type must be synthetic_research_fixture")
    if source["license_class"] != "project_fixture" or source["raw_retained"] is not False:
        raise AnalysisInputError("fixture source must use project_fixture and raw_retained=false")
    if source["disclaimer"] != RESEARCH_DISCLAIMER:
        raise AnalysisInputError("fixture source must explicitly state that inputs are not market facts")
    for key in ("source_id", "publisher", "source_url", "parser_version"):
        if not isinstance(source[key], str) or not source[key]:
            raise AnalysisInputError(f"fixture.source.{key} must be a non-empty string")
    observed_at = _iso_datetime(source["observed_at"], "fixture.source.observed_at")
    fetched_at = _iso_datetime(source["fetched_at"], "fixture.source.fetched_at")
    if observed_at > fetched_at:
        raise AnalysisInputError("fixture source observed_at cannot be after fetched_at")
    if observed_at.date() > as_of or fetched_at.date() > as_of:
        raise AnalysisInputError("fixture source timestamp is after as_of")
    if observed_at > generated_at or fetched_at > generated_at:
        raise AnalysisInputError("fixture source timestamp is after generated_at")

    profiles = fixture["profiles"]
    if not isinstance(profiles, list) or not profiles:
        raise AnalysisInputError("fixture.profiles must be a non-empty array")
    profile_ids: list[str] = []
    for index, profile in enumerate(profiles):
        if not isinstance(profile, Mapping):
            raise AnalysisInputError(f"profile[{index}] must be an object")
        profile_keys = {
            "profile_id",
            "input_as_of",
            "components",
            "confidence_factors",
            "data_status",
            "supporting_evidence",
            "contrary_evidence",
            "invalidation_conditions",
        }
        _exact_keys(profile, profile_keys, f"profile[{index}]")
        profile_id = profile["profile_id"]
        if not isinstance(profile_id, str) or not profile_id:
            raise AnalysisInputError(f"profile[{index}].profile_id must be non-empty")
        profile_ids.append(profile_id)
        if _iso_date(profile["input_as_of"], f"profile[{index}].input_as_of") > as_of:
            raise AnalysisInputError(f"{profile_id}: input_as_of is after fixture as_of")
        components = profile["components"]
        if not isinstance(components, Mapping) or set(components) != set(COMPONENT_NAMES):
            raise AnalysisInputError(f"{profile_id}: components must exactly cover six components")
        for name in COMPONENT_NAMES:
            if not isinstance(components[name], Mapping):
                raise AnalysisInputError(f"{profile_id}.{name} must be an object")
            _validate_component(components[name], f"{profile_id}.{name}")
        factors = profile["confidence_factors"]
        if not isinstance(factors, Mapping):
            raise AnalysisInputError(f"{profile_id}.confidence_factors must be an object")
        factor_keys = set(CONFIDENCE_FACTOR_WEIGHTS) | {"contradiction_penalty"}
        _exact_keys(factors, factor_keys, f"{profile_id}.confidence_factors")
        for name in CONFIDENCE_FACTOR_WEIGHTS:
            _bounded_decimal(factors[name], f"{profile_id}.{name}", 0, 100)
        _bounded_decimal(factors["contradiction_penalty"], f"{profile_id}.contradiction_penalty", 0, 30)
        if not isinstance(profile["data_status"], Mapping):
            raise AnalysisInputError(f"{profile_id}.data_status must be an object")
        evaluate_risk_gate(profile["data_status"])
        for key in ("supporting_evidence", "contrary_evidence", "invalidation_conditions"):
            _validate_evidence_list(profile[key], f"{profile_id}.{key}")
    if len(profile_ids) != len(set(profile_ids)):
        raise AnalysisInputError("duplicate scenario profile_id")

    instruments = universe.get("instruments")
    if not isinstance(instruments, list) or len(instruments) != 30:
        raise AnalysisInputError("universe must contain exactly 30 instruments")
    universe_ids = [item.get("instrument_id") for item in instruments if isinstance(item, Mapping)]
    if len(universe_ids) != 30 or any(not isinstance(item, str) or not item for item in universe_ids):
        raise AnalysisInputError("every universe instrument must have an instrument_id")
    if len(universe_ids) != len(set(universe_ids)):
        raise AnalysisInputError("universe instrument_id values must be unique")

    assignments = fixture["assignments"]
    if not isinstance(assignments, list):
        raise AnalysisInputError("fixture.assignments must be an array")
    assigned_ids: list[str] = []
    referenced_profiles: set[str] = set()
    for index, assignment in enumerate(assignments):
        if not isinstance(assignment, Mapping):
            raise AnalysisInputError(f"assignment[{index}] must be an object")
        _exact_keys(assignment, {"instrument_id", "profile_id"}, f"assignment[{index}]")
        assigned_ids.append(assignment["instrument_id"])
        referenced_profiles.add(assignment["profile_id"])
        if assignment["profile_id"] not in set(profile_ids):
            raise AnalysisInputError(f"assignment references unknown profile {assignment['profile_id']}")
    if len(assigned_ids) != len(set(assigned_ids)):
        raise AnalysisInputError("fixture contains duplicate instrument assignments")
    if set(assigned_ids) != set(universe_ids) or len(assigned_ids) != 30:
        missing = sorted(set(universe_ids) - set(assigned_ids))
        extra = sorted(set(assigned_ids) - set(universe_ids))
        raise AnalysisInputError(
            f"fixture assignments must exactly match universe; missing={missing}, extra={extra}"
        )
    if referenced_profiles != set(profile_ids):
        raise AnalysisInputError("every scenario profile must be assigned to an instrument")


def _provenance(fixture: Mapping[str, Any]) -> dict[str, Any]:
    source = fixture["source"]
    return {
        "source_id": source["source_id"],
        "publisher": source["publisher"],
        "source_type": source["source_type"],
        "source_url": source["source_url"],
        "published_at": None,
        "observed_at": source["observed_at"],
        "fetched_at": source["fetched_at"],
        "market_session_date": None,
        "content_hash": _canonical_hash(fixture),
        "parser_version": source["parser_version"],
        "license_class": source["license_class"],
        "raw_retained": source["raw_retained"],
        "disclaimer": source["disclaimer"],
    }


def build_research_analysis(
    universe: Mapping[str, Any],
    model_weights: Mapping[str, Any],
    action_thresholds: Mapping[str, Any],
    fixture: Mapping[str, Any],
) -> dict[str, Any]:
    """Build all 30 deterministic, uncalibrated research-scenario results."""

    validate_research_fixture(universe, fixture)
    _validate_model_weights(model_weights)
    _validate_thresholds(action_thresholds)
    if fixture["model_version"] != model_weights.get("model_version"):
        raise AnalysisInputError("fixture and configured model_version must match")

    profiles = {profile["profile_id"]: profile for profile in fixture["profiles"]}
    assignments = {
        assignment["instrument_id"]: assignment["profile_id"]
        for assignment in fixture["assignments"]
    }
    provenance = _provenance(fixture)
    instruments: list[dict[str, Any]] = []
    for candidate in universe["instruments"]:
        instrument_id = candidate["instrument_id"]
        profile = profiles[assignments[instrument_id]]
        confidence = calculate_confidence(profile["confidence_factors"], action_thresholds)
        risk_gate_reasons = evaluate_risk_gate(profile["data_status"])
        components = {
            name: {
                "score": _json_score(_decimal(profile["components"][name]["score"], f"{name}.score")),
                "confidence": profile["components"][name]["confidence"],
                "status": "evaluated",
            }
            for name in COMPONENT_NAMES
        }
        horizons: list[dict[str, Any]] = []
        for public_name, config_name in HORIZONS:
            score = calculate_horizon_score(components, model_weights["horizons"][config_name])
            stance = classify_stance(score, confidence, action_thresholds, risk_gate_reasons)
            risk_flags = list(BASE_RISK_FLAGS) + list(risk_gate_reasons)
            if stance == "NO_SIGNAL" and not risk_gate_reasons:
                risk_flags.append("LOW_CONFIDENCE")
            horizons.append(
                {
                    "horizon": public_name,
                    "score": score,
                    "stance": stance,
                    "confidence": confidence,
                    "calibration_status": "uncalibrated",
                    "supporting_evidence": list(profile["supporting_evidence"]),
                    "contrary_evidence": list(profile["contrary_evidence"]),
                    "risk_flags": risk_flags,
                    "invalidation_conditions": list(profile["invalidation_conditions"]),
                }
            )
        instruments.append(
            {
                "instrument_id": instrument_id,
                "scenario_profile_id": profile["profile_id"],
                "data_status": {
                    "status": "research_fixture",
                    "freshness": profile["data_status"]["freshness"],
                    "critical_missing": list(profile["data_status"]["critical_missing"]),
                    "contradiction": profile["data_status"]["contradiction"],
                    "risk_gate_triggered": bool(risk_gate_reasons),
                    "risk_gate_reasons": risk_gate_reasons,
                },
                "components": components,
                "horizons": horizons,
                "provenance": [dict(provenance)],
            }
        )

    return {
        "schema_version": "1.0.0",
        "fixture_id": fixture["fixture_id"],
        "run": {
            "as_of": fixture["as_of"],
            "generated_at": fixture["generated_at"],
            "mode": "research_only",
            "data_kind": "research_fixture",
            "model_version": model_weights["model_version"],
            "calibration_status": "uncalibrated",
        },
        "provenance": provenance,
        "instruments": instruments,
    }
