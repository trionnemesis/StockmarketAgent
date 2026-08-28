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


def _parse_aware_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ContractError(f"{label}: expected a date-time string")
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except ValueError as exc:
        raise ContractError(f"{label}: invalid date-time") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{label}: timezone is required")
    return parsed


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
        if source["license_status"] in {"contract_required", "not_usable"} and source["pages_policy"] != "not_allowed":
            raise ContractError(f"{source['source_id']}: restricted source cannot publish to Pages")
        if source["license_status"] == "metadata_only" and source["pages_policy"] not in {"metadata_only", "not_allowed"}:
            raise ContractError(f"{source['source_id']}: metadata-only license mismatch")


def validate_observed_facts_contract(
    observation: dict[str, Any], sources: dict[str, Any]
) -> None:
    if observation["used_in_signal"] or observation["automated_refresh_enabled"]:
        raise ContractError("official observation must remain outside signals and schedules")
    if observation["collection_policy"]["html_scraping"]:
        raise ContractError("official observation cannot use generic HTML scraping")
    if observation["collection_policy"]["minimum_interval_seconds"] < 2:
        raise ContractError("TWSE OpenAPI collection interval must be at least two seconds")

    fetched_at = _parse_aware_datetime(observation["fetched_at"], "observation fetched_at")
    as_of = date.fromisoformat(observation["as_of"])
    if as_of > fetched_at.date():
        raise ContractError("observation as_of cannot be after fetched_at")

    source_map = {item["source_id"]: item for item in sources["sources"]}
    expected_bindings = {
        "eod_prices": "TWSE_OGL_EOD",
        "valuation": "TWSE_OGL_EOD",
        "monthly_revenue": "TWSE_OGL_FINANCIALS",
        "quarterly_income": "TWSE_OGL_FINANCIALS",
        "balance_sheet": "TWSE_OGL_FINANCIALS",
    }
    resource_map = {item["resource_id"]: item for item in observation["resources"]}
    if len(resource_map) != len(observation["resources"]):
        raise ContractError("official observation resource_id values must be unique")
    if set(resource_map) != set(expected_bindings):
        raise ContractError("official observation resource set is incomplete")
    for resource_id, expected_source_id in expected_bindings.items():
        resource = resource_map[resource_id]
        if resource["source_id"] != expected_source_id:
            raise ContractError(f"{resource_id}: source binding mismatch")
        source = source_map.get(expected_source_id)
        if source is None:
            raise ContractError(f"{resource_id}: source is missing from source policy")
        if source["license_status"] != "open_with_attribution":
            raise ContractError(f"{resource_id}: source is not open with attribution")
        if source["pages_policy"] != "raw_with_attribution_allowed":
            raise ContractError(f"{resource_id}: source cannot be published to Pages")
        if date.fromisoformat(resource["observed_at"]) > as_of:
            raise ContractError(f"{resource_id}: resource observation is after as_of")
        if resource["raw_retained"]:
            raise ContractError(f"{resource_id}: full-market raw payload cannot be retained")

    facts = observation["facts"]
    for fact_name, fact in facts.items():
        resource_id = fact["source_resource_id"]
        if resource_id not in resource_map:
            raise ContractError(f"{fact_name}: fact references an unknown resource")
        fact_date = fact.get("date", fact.get("published_date"))
        if date.fromisoformat(fact_date) > as_of:
            raise ContractError(f"{fact_name}: fact date is after as_of")

    market = facts["market_session"]
    if not (
        market["low"] <= market["open"] <= market["high"]
        and market["low"] <= market["close"] <= market["high"]
    ):
        raise ContractError("market OHLC values are inconsistent")
    if facts["valuation"]["date"] != market["date"]:
        raise ContractError("valuation and EOD snapshots must use the same session")
    if facts["quarterly_income"]["period"] != facts["balance_sheet"]["period"]:
        raise ContractError("income statement and balance sheet periods disagree")
    if facts["monthly_revenue"]["period"] > observation["as_of"][:7]:
        raise ContractError("monthly revenue period is after observation month")
    if "政府資料開放授權條款" not in observation["attribution"]["statement"]:
        raise ContractError("official observation lacks visible OGL attribution")


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


def _expected_research_stance(
    score: int | float | None,
    confidence: int,
    thresholds: dict[str, Any],
    gate_reasons: set[str],
) -> str:
    if score is None:
        raise ContractError("research fixture horizon must include a score")
    if gate_reasons:
        return "NO_SIGNAL"
    if confidence < thresholds["confidence_no_signal_below"]:
        return "NO_SIGNAL"
    if (
        score >= thresholds["buy_min"]
        and confidence >= thresholds["directional_confidence_min"]
    ):
        return "BUY"
    if (
        score <= thresholds["sell_max"]
        and confidence >= thresholds["directional_confidence_min"]
    ):
        return "SELL"
    return "HOLD"


def validate_signal_contract(
    signal: dict[str, Any],
    approvals: dict[str, Any],
    action_thresholds: dict[str, Any],
) -> None:
    validate_action_thresholds_contract(action_thresholds)
    instruments = signal["instruments"]
    summary = signal["summary"]
    run = signal["run"]
    try:
        run_as_of = date.fromisoformat(run["as_of"])
    except (TypeError, ValueError) as exc:
        raise ContractError("signal as_of is invalid") from exc
    generated_at = _parse_aware_datetime(run["generated_at"], "signal generated_at")
    if generated_at.date() != run_as_of:
        raise ContractError("signal generated_at must fall on as_of")
    if approvals["production_signal_enabled"]:
        raise ContractError("this contract does not permit production signals")
    if run["mode"] != "research_only":
        raise ContractError("signal mode must remain research_only")
    if run["data_kind"] not in {"fixture", "research_fixture"}:
        raise ContractError("unsupported research data kind")
    if run["data_kind"] == "fixture":
        if signal["schema_version"] != "1.0.0":
            raise ContractError("baseline fixture signals must use signal schema 1.0.0")
    else:
        if signal["schema_version"] != "1.1.0":
            raise ContractError("research analysis signals must use signal schema 1.1.0")
        if re.fullmatch(r"[a-f0-9]{40}", run["git_sha"]) is None:
            raise ContractError("research analysis signal must identify a full Git source revision")
    if len(instruments) != 30:
        raise ContractError("research signal must contain exactly 30 instruments")
    if summary["tracked_count"] != len(instruments):
        raise ContractError("summary tracked_count does not match instruments")
    proposed_count = sum(item["status"] == "proposed" for item in instruments)
    approved_enabled_count = sum(
        item["status"] == "approved" and item["enabled"] for item in instruments
    )
    if summary["proposed_count"] != proposed_count:
        raise ContractError("summary proposed_count does not match instruments")
    if summary["approved_enabled_count"] != approved_enabled_count:
        raise ContractError("summary approved_enabled_count does not match instruments")
    three_month_stances: list[str] = []
    for item in instruments:
        horizon_names = [entry["horizon"] for entry in item["horizons"]]
        if horizon_names != ["1W", "1M", "3M", "12M"]:
            raise ContractError(f"{item['instrument_id']}: horizon order mismatch")
        three_month_stances.append(item["horizons"][2]["stance"])
    stance_counts = Counter(three_month_stances)
    expected_stances = {
        stance: stance_counts.get(stance, 0)
        for stance in ("BUY", "HOLD", "SELL", "NO_SIGNAL")
    }
    if summary["stances"] != expected_stances:
        raise ContractError("summary stances must match each instrument's 3M horizon")
    expected_market_counts = Counter(
        {
            ("TW", "stock"): 5,
            ("TW", "etf"): 5,
            ("JP", "stock"): 5,
            ("JP", "etf"): 5,
            ("US", "stock"): 5,
            ("US", "etf"): 5,
        }
    )
    market_counts = Counter(
        (item["country"], item["asset_type"]) for item in instruments
    )
    if market_counts != expected_market_counts:
        raise ContractError("signal country/asset counts must match the 30-item universe")
    instrument_ids = [item["instrument_id"] for item in instruments]
    if len(instrument_ids) != len(set(instrument_ids)):
        raise ContractError("signal instrument_id values must be unique")
    instrument_id_set = set(instrument_ids)
    slugs = [item["slug"] for item in instruments]
    if len(slugs) != len(set(slugs)):
        raise ContractError("signal slug values must be unique")
    market_symbols = [(item["market"], item["symbol"]) for item in instruments]
    if len(market_symbols) != len(set(market_symbols)):
        raise ContractError("signal market + symbol values must be unique")
    market_summaries = {item["country"]: item for item in signal["markets"]}
    if len(market_summaries) != 3 or set(market_summaries) != {"TW", "JP", "US"}:
        raise ContractError("market summaries must cover TW, JP, and US exactly once")
    for country, market in market_summaries.items():
        count = sum(item["country"] == country for item in instruments)
        if market["instrument_count"] != count:
            raise ContractError(f"{country}: market instrument_count mismatch")
    event_ids = [event["event_id"] for event in signal["events"]]
    if len(event_ids) != len(set(event_ids)):
        raise ContractError("signal event_id values must be unique")
    for event in signal["events"]:
        references = event["instrument_ids"]
        if len(references) != len(set(references)):
            raise ContractError(f"{event['event_id']}: instrument references must be unique")
        unknown_references = set(references) - instrument_id_set
        if unknown_references:
            raise ContractError(
                f"{event['event_id']}: unknown instrument references {sorted(unknown_references)}"
            )
        published_at = _parse_aware_datetime(
            event["published_at"], f"{event['event_id']} published_at"
        )
        if published_at > generated_at:
            raise ContractError(f"{event['event_id']}: event is after the research run")

    critical_events = sum(
        event["materiality"] == "high" for event in signal["events"]
    )
    if summary["critical_events"] != critical_events:
        raise ContractError("summary critical_events does not match events")
    if run["data_kind"] == "research_fixture" and not approvals["research_analysis_enabled"]:
        raise ContractError("research fixture requires research_analysis_enabled")

    manifest = {item["source_id"]: item for item in signal["source_manifest"]}
    if len(manifest) != len(signal["source_manifest"]):
        raise ContractError("source manifest source_id values must be unique")

    for item in instruments:
        if item["status"] != "proposed" or item["enabled"]:
            raise ContractError(f"{item['instrument_id']}: escaped research approval gate")
        for component_name, component in item["components"].items():
            if component["status"] == "evaluated":
                if component["score"] is None or component["confidence"] <= 0:
                    raise ContractError(
                        f"{item['instrument_id']}/{component_name}: evaluated component needs a score and confidence"
                    )
            elif component["score"] is not None or component["confidence"] != 0:
                raise ContractError(
                    f"{item['instrument_id']}/{component_name}: unevaluated component cannot claim a score"
                )

        if run["data_kind"] == "fixture":
            if item["data_status"]["status"] != "fixture":
                raise ContractError(f"{item['instrument_id']}: fixture data status mismatch")
        elif item["data_status"]["status"] not in {"research_fixture", "stale"}:
            raise ContractError(f"{item['instrument_id']}: research fixture data status mismatch")

        gate_reasons: set[str] = set()
        if run["data_kind"] == "research_fixture":
            gate_reasons = set(item["data_status"]["warnings"]).intersection(
                {"CRITICAL_MISSING", "STALE_DATA", "SOURCE_CONTRADICTION"}
            )
            if item["data_status"]["critical_missing"]:
                if "CRITICAL_MISSING" not in gate_reasons:
                    raise ContractError(
                        f"{item['instrument_id']}: critical missing data lacks Risk Gate reason"
                    )
                gate_reasons.add("CRITICAL_MISSING")
            if item["data_status"]["status"] == "stale":
                gate_reasons.add("STALE_DATA")
            if not item["model_applicability"]["applicable"]:
                gate_reasons.add("MODEL_NOT_APPLICABLE")

        for horizon in item["horizons"]:
            if horizon["calibration_status"] == "calibrated":
                raise ContractError(
                    f"{item['instrument_id']}/{horizon['horizon']}: calibration is unavailable in this research slice"
                )
            if run["data_kind"] == "fixture":
                if (
                    horizon["stance"] != "NO_SIGNAL"
                    or horizon["score"] is not None
                    or horizon["confidence"] != 0
                ):
                    raise ContractError(
                        f"{item['instrument_id']}: baseline fixture horizon must be NO_SIGNAL"
                    )
                continue
            if horizon["calibration_status"] != "uncalibrated":
                raise ContractError(
                    f"{item['instrument_id']}/{horizon['horizon']}: research fixture horizon must be uncalibrated"
                )
            horizon_gate_reasons = set(horizon["risk_flags"]).intersection(
                {
                    "CRITICAL_MISSING",
                    "STALE_DATA",
                    "SOURCE_CONTRADICTION",
                    "MODEL_NOT_APPLICABLE",
                }
            )
            if horizon_gate_reasons != gate_reasons:
                raise ContractError(
                    f"{item['instrument_id']}/{horizon['horizon']}: horizon and data Risk Gate reasons disagree"
                )
            required_flags = {
                "RESEARCH_FIXTURE",
                "MODEL_UNCALIBRATED",
                *gate_reasons,
            }
            missing_flags = required_flags - set(horizon["risk_flags"])
            if missing_flags:
                raise ContractError(
                    f"{item['instrument_id']}/{horizon['horizon']}: missing research risk flags {sorted(missing_flags)}"
                )
            expected_stance = _expected_research_stance(
                horizon["score"],
                horizon["confidence"],
                action_thresholds,
                gate_reasons,
            )
            if horizon["stance"] != expected_stance:
                raise ContractError(
                    f"{item['instrument_id']}/{horizon['horizon']}: stance {horizon['stance']} "
                    f"does not match configured threshold result {expected_stance}"
                )

        for provenance in item["provenance"]:
            manifest_entry = manifest.get(provenance["source_id"])
            if manifest_entry is None:
                raise ContractError(f"{item['instrument_id']}: provenance source is not in manifest")
            if manifest_entry["content_hash"] != provenance["content_hash"]:
                raise ContractError(f"{item['instrument_id']}: provenance hash mismatch")
            observed_at = _parse_aware_datetime(
                provenance["observed_at"],
                f"{item['instrument_id']} provenance observed_at",
            )
            fetched_at = _parse_aware_datetime(
                provenance["fetched_at"],
                f"{item['instrument_id']} provenance fetched_at",
            )
            if observed_at > fetched_at:
                raise ContractError(
                    f"{item['instrument_id']}: provenance observed_at is after fetched_at"
                )
            if fetched_at > generated_at:
                raise ContractError(
                    f"{item['instrument_id']}: provenance is after the research run"
                )
            if provenance["published_at"] is not None:
                published_at = _parse_aware_datetime(
                    provenance["published_at"],
                    f"{item['instrument_id']} provenance published_at",
                )
                if published_at > observed_at or published_at > generated_at:
                    raise ContractError(
                        f"{item['instrument_id']}: provenance published_at exceeds the observation boundary"
                    )
            if provenance["market_session_date"] is not None:
                try:
                    market_session_date = date.fromisoformat(
                        provenance["market_session_date"]
                    )
                except (TypeError, ValueError) as exc:
                    raise ContractError(
                        f"{item['instrument_id']}: provenance market_session_date is invalid"
                    ) from exc
                if market_session_date > run_as_of:
                    raise ContractError(
                        f"{item['instrument_id']}: provenance market session is after as_of"
                    )
            if run["data_kind"] == "fixture" and provenance["source_type"] != "fixture":
                raise ContractError(f"{item['instrument_id']}: baseline fixture provenance mismatch")
            if (
                run["data_kind"] == "research_fixture"
                and provenance["source_type"] != "synthetic_research_fixture"
            ):
                raise ContractError(f"{item['instrument_id']}: research fixture provenance mismatch")
            if provenance["license_class"] != "project_fixture" or provenance["raw_retained"]:
                raise ContractError(f"{item['instrument_id']}: fixture publication boundary mismatch")
            if (
                run["data_kind"] == "research_fixture"
                and provenance.get("disclaimer")
                != "Synthetic research fixture inputs; not market facts or live market data."
            ):
                raise ContractError(f"{item['instrument_id']}: research fixture disclaimer mismatch")

    expected_manifest_kind = (
        "research_fixture" if run["data_kind"] == "research_fixture" else "fixture"
    )
    if any(item["kind"] != expected_manifest_kind for item in signal["source_manifest"]):
        raise ContractError("source manifest kind does not match run data_kind")


def validate_agent_run_contract(record: dict[str, Any]) -> None:
    run_type = record["run_type"]
    agent_run_version = record["schema_versions"].get("agent_run")
    if run_type == "fixture_build":
        if agent_run_version != "1.0.0":
            raise ContractError("fixture Agent Run must retain agent_run schema 1.0.0")
        return
    if run_type != "research_analysis_build":
        raise ContractError(f"unsupported Agent Run type: {run_type}")
    if agent_run_version != "1.1.0":
        raise ContractError("research analysis Agent Run must use agent_run schema 1.1.0")
    if record["schema_versions"].get("signal") != "1.1.0":
        raise ContractError("research analysis Agent Run must bind signal schema 1.1.0")
    if re.fullmatch(r"[a-f0-9]{40}", record["git_sha"]) is None:
        raise ContractError("research analysis Agent Run must identify a full Git source revision")
    started_at = _parse_aware_datetime(record["started_at"], "Agent Run started_at")
    completed_at = _parse_aware_datetime(
        record["completed_at"], "Agent Run completed_at"
    )
    if started_at > completed_at:
        raise ContractError("Agent Run started_at cannot be after completed_at")


def validate_model_weights_contract(model: dict[str, Any]) -> None:
    if model["status"] != "uncalibrated_research":
        raise ContractError("research model weights must remain uncalibrated")
    expected_horizons = {"week_1", "month_1", "month_3", "month_12"}
    if set(model["horizons"]) != expected_horizons:
        raise ContractError("model weights must define the four required horizons")
    expected_components = {
        "technical", "events", "macro", "fundamental", "valuation", "cycle"
    }
    for horizon_name, weights in model["horizons"].items():
        if set(weights) != expected_components:
            raise ContractError(f"{horizon_name}: model component set mismatch")
        if not math.isclose(sum(weights.values()), 1.0, rel_tol=0.0, abs_tol=1e-9):
            raise ContractError(f"{horizon_name}: model weights must sum to 1.0")


def validate_action_thresholds_contract(thresholds: dict[str, Any]) -> None:
    if thresholds["status"] != "engineering_defaults_uncalibrated":
        raise ContractError("action thresholds must remain uncalibrated")
    if thresholds["directional_confidence_min"] < 70:
        raise ContractError("directional confidence threshold must be at least 70")
    if thresholds["confidence_no_signal_below"] >= thresholds["directional_confidence_min"]:
        raise ContractError("NO_SIGNAL confidence threshold must be below directional confidence")
    if not (
        thresholds["sell_max"]
        < thresholds["hold_min"]
        <= thresholds["hold_max"]
        < thresholds["buy_min"]
    ):
        raise ContractError("SELL/HOLD/BUY score thresholds overlap or are out of order")


def validate_approvals_contract(approvals: dict[str, Any]) -> None:
    if approvals["production_signal_enabled"]:
        raise ContractError("production_signal_enabled must remain false")
    if not approvals["research_analysis_enabled"]:
        raise ContractError("research_analysis_enabled must be true for this research slice")
    approval_fields = (
        "approved_universe_version", "approved_model_version", "approved_by", "approved_at"
    )
    if any(approvals[field] is not None for field in approval_fields):
        raise ContractError("research-only configuration must not claim production approval")


def validate_schedules_contract(schedules: dict[str, Any]) -> None:
    if schedules["timezone"] != "Asia/Taipei":
        raise ContractError("research schedules must use Asia/Taipei")
    if schedules["automation_enabled"]:
        raise ContractError("scheduled refresh remains disabled in this research slice")
    ids = [item["id"] for item in schedules["schedules"]]
    if len(ids) != len(set(ids)):
        raise ContractError("duplicate schedule id")
    for schedule in schedules["schedules"]:
        if schedule["status"] != "proposal_only":
            raise ContractError(f"{schedule['id']}: schedule must remain proposal_only")
        if len(schedule["cron"].split()) != 5:
            raise ContractError(f"{schedule['id']}: cron expression must have five fields")
