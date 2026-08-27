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
