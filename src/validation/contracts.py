from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when an input violates a versioned project contract."""


def _reject_constant(value: str) -> None:
    raise ContractError(f"non-standard JSON constant: {value}")


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ContractError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    try:
        return json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=_reject_constant,
            object_pairs_hook=_pairs_no_duplicates,
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"{path}: invalid JSON: {exc}") from exc


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def content_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _resolve_fragment(document: dict[str, Any], fragment: str) -> dict[str, Any]:
    value: Any = document
    if fragment:
        for token in fragment.removeprefix("/").split("/"):
            token = token.replace("~1", "/").replace("~0", "~")
            value = value[token]
    if not isinstance(value, dict):
        raise ContractError(f"schema reference is not an object: #{fragment}")
    return value


def _type_matches(value: Any, expected: str) -> bool:
    return {
        "null": value is None,
        "boolean": isinstance(value, bool),
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value),
    }.get(expected, False)


def _format_matches(value: str, format_name: str) -> bool:
    try:
        if format_name == "date":
            date.fromisoformat(value)
            return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))
        if format_name == "date-time":
            normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
            datetime.fromisoformat(normalized)
            return "T" in value
    except ValueError:
        return False
    return True


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    *,
    schema_path: Path,
    root_schema: dict[str, Any] | None = None,
    location: str = "$",
) -> None:
    root = root_schema or schema

    if "$ref" in schema:
        reference = schema["$ref"]
        if reference.startswith("#"):
            target = _resolve_fragment(root, reference[1:])
            validate_schema(
                value,
                target,
                schema_path=schema_path,
                root_schema=root,
                location=location,
            )
            return
        target_name, _, fragment = reference.partition("#")
        target_path = (schema_path.parent / target_name).resolve()
        target_root = load_json_strict(target_path)
        validate_schema(
            value,
            _resolve_fragment(target_root, fragment),
            schema_path=target_path,
            root_schema=target_root,
            location=location,
        )
        return

    if "const" in schema and value != schema["const"]:
        raise ContractError(f"{location}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        raise ContractError(f"{location}: {value!r} is not in the allowed values")

    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else expected
        if not any(_type_matches(value, item) for item in expected_types):
            raise ContractError(f"{location}: expected type {expected_types}, got {type(value).__name__}")

    if isinstance(value, dict):
        required = schema.get("required", [])
        missing = [key for key in required if key not in value]
        if missing:
            raise ContractError(f"{location}: missing required properties {missing}")
        properties = schema.get("properties", {})
        extra = set(value) - set(properties)
        additional = schema.get("additionalProperties", True)
        if extra and additional is False:
            raise ContractError(f"{location}: unexpected properties {sorted(extra)}")
        for key, child in value.items():
            if key in properties:
                validate_schema(
                    child,
                    properties[key],
                    schema_path=schema_path,
                    root_schema=root,
                    location=f"{location}.{key}",
                )
            elif isinstance(additional, dict):
                validate_schema(
                    child,
                    additional,
                    schema_path=schema_path,
                    root_schema=root,
                    location=f"{location}.{key}",
                )

    if isinstance(value, list):
        minimum = schema.get("minItems")
        maximum = schema.get("maxItems")
        if minimum is not None and len(value) < minimum:
            raise ContractError(f"{location}: expected at least {minimum} items")
        if maximum is not None and len(value) > maximum:
            raise ContractError(f"{location}: expected at most {maximum} items")
        if schema.get("uniqueItems"):
            serialized = [canonical_json(item) for item in value]
            if len(serialized) != len(set(serialized)):
                raise ContractError(f"{location}: items must be unique")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, child in enumerate(value):
                validate_schema(
                    child,
                    item_schema,
                    schema_path=schema_path,
                    root_schema=root,
                    location=f"{location}[{index}]",
                )

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if minimum is not None and len(value) < minimum:
            raise ContractError(f"{location}: string is shorter than {minimum}")
        pattern = schema.get("pattern")
        if pattern and re.search(pattern, value) is None:
            raise ContractError(f"{location}: string does not match {pattern}")
        format_name = schema.get("format")
        if format_name and not _format_matches(value, format_name):
            raise ContractError(f"{location}: invalid {format_name}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        maximum = schema.get("maximum")
        if minimum is not None and value < minimum:
            raise ContractError(f"{location}: value is below {minimum}")
        if maximum is not None and value > maximum:
            raise ContractError(f"{location}: value is above {maximum}")


def validate_document(value: Any, schema_path: Path) -> None:
    schema = load_json_strict(schema_path)
    validate_schema(value, schema, schema_path=schema_path)


def validate_universe_contract(
    universe: dict[str, Any], approvals: dict[str, Any]
) -> None:
    instruments = universe["instruments"]
    ids = [item["instrument_id"] for item in instruments]
    slugs = [item["slug"] for item in instruments]
    market_symbols = [(item["market"], item["symbol"]) for item in instruments]
    for label, values in (
        ("instrument_id", ids),
        ("slug", slugs),
        ("market + symbol", market_symbols),
    ):
        if len(values) != len(set(values)):
            raise ContractError(f"duplicate {label}")

    expected = {
        ("TW", "stock"): 5,
        ("TW", "etf"): 5,
        ("JP", "stock"): 5,
        ("JP", "etf"): 5,
        ("US", "stock"): 5,
        ("US", "etf"): 5,
    }
    actual = Counter((item["country"], item["asset_type"]) for item in instruments)
    if actual != Counter(expected):
        raise ContractError(f"universe market/type counts mismatch: {dict(actual)}")

    production = [
        item
        for item in instruments
        if item["status"] == "approved" and item["enabled"]
    ]
    if approvals["production_signal_enabled"]:
        if len(production) != 30:
            raise ContractError("production mode requires exactly 30 approved + enabled instruments")
        if approvals["approved_universe_version"] != universe["universe_version"]:
            raise ContractError("approved universe version does not match")
    else:
        if production:
            raise ContractError("research-only universe must not include production instruments")
        if any(item["status"] != "proposed" or item["enabled"] for item in instruments):
            raise ContractError("unapproved instruments must remain proposed and disabled")


def validate_theme_contract(universe: dict[str, Any], themes: dict[str, Any]) -> None:
    allowed = set(themes["themes"])
    used = {theme for item in universe["instruments"] for theme in item["themes"]}
    if used - allowed:
        raise ContractError(f"undefined themes: {sorted(used - allowed)}")


def validate_source_contract(sources: dict[str, Any]) -> None:
    source_map = {item["source_id"]: item for item in sources["sources"]}
    if len(source_map) != len(sources["sources"]):
        raise ContractError("duplicate source_id")
    policies = sources["policies"]
    expected = {(c, a) for c in ("TW", "JP", "US") for a in ("stock", "etf")}
    actual = {(item["country"], item["asset_type"]) for item in policies}
    if actual != expected or len(policies) != 6:
        raise ContractError("source policies must cover the six country/asset pairs")
    classes = {"listing_metadata", "eod_prices", "corporate_actions", "filings_financials", "etf_fund_data", "market_calendar", "fx", "benchmark"}
    referenced: set[str] = set()
    for policy in policies:
        coverage = policy["coverage"]
        if {item["data_class"] for item in coverage} != classes or len(coverage) != 8:
            raise ContractError(f"{policy['source_policy_id']}: must cover exactly eight data classes")
        for entry in coverage:
            refs = entry["primary_source_ids"] + entry["fallback_source_ids"]
            if entry["status"] == "not_applicable" and refs:
                raise ContractError(f"{policy['source_policy_id']}/{entry['data_class']}: N/A cannot reference sources")
            if entry["status"] != "not_applicable" and not refs:
                raise ContractError(f"{policy['source_policy_id']}/{entry['data_class']}: missing source")
            for source_id in refs:
                if source_id not in source_map:
                    raise ContractError(f"unknown source_id: {source_id}")
                source = source_map[source_id]
                if entry["data_class"] not in source["data_classes"]:
                    raise ContractError(f"{source_id}: incompatible data class {entry['data_class']}")
                if policy["country"] not in source["countries"] and "GLOBAL" not in source["countries"]:
                    raise ContractError(f"{source_id}: incompatible country {policy['country']}")
                referenced.add(source_id)
            primary_feasibility = {source_map[source_id]["feasibility"] for source_id in entry["primary_source_ids"]}
            status = entry["status"]
            if status == "ready" and "ready" not in primary_feasibility:
                raise ContractError(f"{policy['source_policy_id']}/{entry['data_class']}: ready without a ready source")
            if status == "reference_only" and primary_feasibility != {"reference_only"}:
                raise ContractError(f"{policy['source_policy_id']}/{entry['data_class']}: reference-only status mismatch")
            if status == "blocked" and (not primary_feasibility or not primary_feasibility <= {"blocked", "reference_only"} or "blocked" not in primary_feasibility):
                raise ContractError(f"{policy['source_policy_id']}/{entry['data_class']}: blocked status mismatch")
            if status == "conditional" and not primary_feasibility.intersection({"ready", "conditional"}):
                raise ContractError(f"{policy['source_policy_id']}/{entry['data_class']}: conditional status lacks feasible primary")
    if set(source_map) != referenced:
        raise ContractError(f"unreferenced sources: {sorted(set(source_map) - referenced)}")
    for source in source_map.values():
        if source["authentication"] == "none" and source["key_required"]:
            raise ContractError(f"{source['source_id']}: auth/key inconsistency")
        if source["feasibility"] in {"contract_required", "not_usable"} and source["pages_policy"] != "not_allowed":
            raise ContractError(f"{source['source_id']}: restricted source cannot publish to Pages")
        if source["license_status"] == "metadata_only" and source["pages_policy"] not in {"metadata_only", "not_allowed"}:
            raise ContractError(f"{source['source_id']}: metadata-only license mismatch")


def _validate_evidence_refs(refs: list[dict[str, Any]], source_ids: set[str], as_of: str) -> None:
    for ref in refs:
        if ref["source_id"] not in source_ids:
            raise ContractError(f"evidence references unknown source {ref['source_id']}")
        if ref["observed_at"] > as_of:
            raise ContractError("evidence observed_at is after review evidence_as_of")


def validate_review_contract(
    universe: dict[str, Any], benchmarks: dict[str, Any], sources: dict[str, Any], review: dict[str, Any]
) -> None:
    if review["universe_version"] != universe["universe_version"]:
        raise ContractError("review universe_version mismatch")
    universe_map = {item["instrument_id"]: item for item in universe["instruments"]}
    review_map = {item["instrument_id"]: item for item in review["instruments"]}
    if list(review_map) != list(universe_map) or len(review_map) != 30:
        raise ContractError("review membership/order must exactly match universe")
    benchmark_ids = {item["benchmark_id"] for item in benchmarks["benchmarks"]}
    source_ids = {item["source_id"] for item in sources["sources"]}
    for iid, item in review_map.items():
        candidate = universe_map[iid]
        expected = {
            "symbol": candidate["symbol"], "exchange": candidate["market"],
            "legal_name": candidate["name_en"], "asset_type": candidate["asset_type"],
            "trading_currency": candidate["currency"], "benchmark_id": candidate["benchmark_id"],
            "selection_rationale": candidate["selection_rationale"], "theme_evidence": candidate["themes"],
        }
        for key, value in expected.items():
            if item[key] != value:
                raise ContractError(f"{iid}: review {key} diverges from universe")
        if item["benchmark_id"] not in benchmark_ids:
            raise ContractError(f"{iid}: unknown benchmark")
        if (item["asset_type"] == "etf") != ("tracking_index" in item):
            raise ContractError(f"{iid}: tracking index must exist only for ETFs")
        if item["asset_type"] == "etf" and item["models"]["etf_look_through"]["status"] != "conditional":
            raise ContractError(f"{iid}: ETF look-through routing mismatch")
        claims = {claim for ref in item["evidence"] for claim in ref["claims"]}
        required = {"identity", "listing", "currency", "asset_type", "live_age", "liquidity", "themes", "selection_rationale"}
        if item["asset_type"] == "etf":
            required.add("tracking_index")
            if item["tracking_index"]["source_id"] not in source_ids:
                raise ContractError(f"{iid}: unknown tracking-index source")
        if not required <= claims:
            raise ContractError(f"{iid}: missing evidence claims {sorted(required - claims)}")
        _validate_evidence_refs(item["evidence"], source_ids, review["evidence_as_of"])
    for group in review["overlap_groups"]:
        if not set(group["members"]) <= set(universe_map):
            raise ContractError(f"{group['overlap_id']}: unknown member")
        _validate_evidence_refs(group["evidence"], source_ids, review["evidence_as_of"])
    for concentration in review["issuer_concentration"]:
        _validate_evidence_refs(concentration["evidence"], source_ids, review["evidence_as_of"])


def validate_signal_contract(
    signal: dict[str, Any], approvals: dict[str, Any]
) -> None:
    instruments = signal["instruments"]
    summary = signal["summary"]
    if summary["tracked_count"] != len(instruments):
        raise ContractError("summary tracked_count does not match instruments")
    if set(item["country"] for item in instruments) != {"TW", "JP", "US"}:
        raise ContractError("signals must cover TW, JP, and US")
    if not approvals["production_signal_enabled"]:
        for item in instruments:
            if item["status"] != "proposed" or item["enabled"]:
                raise ContractError(f"{item['instrument_id']}: escaped approval gate")
            for horizon in item["horizons"]:
                if (
                    horizon["stance"] != "NO_SIGNAL"
                    or horizon["score"] is not None
                    or horizon["confidence"] != 0
                ):
                    raise ContractError(
                        f"{item['instrument_id']}: research-only horizon must be NO_SIGNAL"
                    )
    for item in instruments:
        horizon_names = [entry["horizon"] for entry in item["horizons"]]
        if horizon_names != ["1W", "1M", "3M", "12M"]:
            raise ContractError(f"{item['instrument_id']}: horizon order mismatch")
