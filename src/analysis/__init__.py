"""Deterministic research-fixture analysis primitives."""

from .scoring import (
    AnalysisInputError,
    build_research_analysis,
    calculate_confidence,
    calculate_horizon_score,
    classify_stance,
    evaluate_risk_gate,
    validate_research_fixture,
)

__all__ = [
    "AnalysisInputError",
    "build_research_analysis",
    "calculate_confidence",
    "calculate_horizon_score",
    "classify_stance",
    "evaluate_risk_gate",
    "validate_research_fixture",
]
