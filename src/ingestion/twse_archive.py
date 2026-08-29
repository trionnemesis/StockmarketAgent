from __future__ import annotations

import argparse
import json
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from src.validation.contracts import (
    ContractError,
    canonical_json,
    content_hash,
    load_json_strict,
    validate_document,
    validate_observed_facts_contract,
)


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OBSERVATION_DIR = ROOT / "data" / "observations" / "twse"
DEFAULT_CALENDAR_PATH = ROOT / "config" / "twse_calendar.json"
SCHEMAS = ROOT / "schemas"
ARCHIVE_SCHEMA = SCHEMAS / "observation-archive-entry.schema.json"
CATALOG_SCHEMA = SCHEMAS / "observation-catalog.schema.json"
CALENDAR_SCHEMA = SCHEMAS / "twse-calendar.schema.json"


class ArchiveError(ContractError):
    """Raised when the append-only Taiwan observation store cannot be trusted."""


def _pretty_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _parse_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise ArchiveError(f"{label} must be an ISO date")
    try:
        result = date.fromisoformat(value)
    except ValueError as exc:
        raise ArchiveError(f"{label} must be an ISO date") from exc
    if result.isoformat() != value:
        raise ArchiveError(f"{label} must be an ISO date")
    return result


def _parse_datetime(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ArchiveError(f"{label} must be an ISO date-time")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        result = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ArchiveError(f"{label} must be an ISO date-time") from exc
    if result.tzinfo is None:
        raise ArchiveError(f"{label} must include a timezone")
    return result


def _load_calendar(path: Path = DEFAULT_CALENDAR_PATH) -> dict[str, Any]:
    calendar = load_json_strict(path)
    validate_document(calendar, CALENDAR_SCHEMA)
    return calendar


def _closed_dates(calendar: Mapping[str, Any]) -> dict[date, str]:
    return {
        _parse_date(item["date"], "closed date"): item["reason"]
        for item in calendar["closed_dates"]
    }


def _is_session(day: date, calendar: Mapping[str, Any]) -> bool:
    return day.weekday() not in set(calendar["weekend_days"]) and day not in _closed_dates(calendar)


def _previous_session(day: date, calendar: Mapping[str, Any], *, include_day: bool) -> date:
    candidate = day if include_day else day - timedelta(days=1)
    for _ in range(370):
        if _is_session(candidate, calendar):
            return candidate
        candidate -= timedelta(days=1)
    raise ArchiveError("cannot resolve a previous TWSE market session")


def _market_state(day: date, calendar: Mapping[str, Any]) -> tuple[str, str]:
    closed = _closed_dates(calendar)
    if day in closed:
        return "holiday", closed[day]
    if day.weekday() in set(calendar["weekend_days"]):
        return "weekend", "regular weekend closure"
    return "trading_day", "regular trading day"


def expected_latest_session(
    evaluated_at: str,
    calendar: Mapping[str, Any],
) -> tuple[date, str, str]:
    instant = _parse_datetime(evaluated_at, "evaluated_at")
    local = instant.astimezone(ZoneInfo(calendar["timezone"]))
    local_day = local.date()
    state, reason = _market_state(local_day, calendar)
    cutoff = time.fromisoformat(calendar["freshness_policy"]["same_day_expected_after"])
    if state == "trading_day" and local.timetz().replace(tzinfo=None) >= cutoff:
        expected = _previous_session(local_day, calendar, include_day=True)
    else:
        expected = _previous_session(local_day, calendar, include_day=False)
    return expected, state, reason


def _session_distance(
    observed: date,
    expected: date,
    calendar: Mapping[str, Any],
) -> int:
    if observed > expected:
        raise ArchiveError("observed market session is after the expected session")
    count = 0
    candidate = observed + timedelta(days=1)
    while candidate <= expected:
        if _is_session(candidate, calendar):
            count += 1
        candidate += timedelta(days=1)
    return count


def evaluate_freshness(
    observed_market_session: str | None,
    *,
    evaluated_at: str,
    calendar: Mapping[str, Any],
) -> dict[str, Any]:
    expected, market_state, market_reason = expected_latest_session(
        evaluated_at, calendar
    )
    if observed_market_session is None:
        return {
            "evaluated_at": evaluated_at,
            "market_state": market_state,
            "market_state_reason": market_reason,
            "expected_latest_session": expected.isoformat(),
            "observed_market_session": None,
            "freshness": "missing",
            "sessions_behind": None,
            "reason": "no validated official observation is available",
        }
    observed = _parse_date(observed_market_session, "observed_market_session")
    behind = _session_distance(observed, expected, calendar)
    freshness = "fresh" if behind == 0 else "stale"
    return {
        "evaluated_at": evaluated_at,
        "market_state": market_state,
        "market_state_reason": market_reason,
        "expected_latest_session": expected.isoformat(),
        "observed_market_session": observed.isoformat(),
        "freshness": freshness,
        "sessions_behind": behind,
        "reason": (
            "validated observation matches the expected latest market session"
            if freshness == "fresh"
            else f"validated observation is {behind} market session(s) behind"
        ),
    }


def _revision_payload(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    resources = [
        {
            "resource_id": item["resource_id"],
            "source_id": item["source_id"],
            "observed_at": item["observed_at"],
            "content_sha256": item["content_sha256"],
        }
        for item in snapshot["resources"]
    ]
    return {
        "instrument_id": snapshot["instrument_id"],
        "symbol": snapshot["symbol"],
        "asset_type": snapshot["asset_type"],
        "official_as_of": snapshot["as_of"],
        "facts": snapshot["facts"],
        "coverage": snapshot["coverage"],
        "resources": resources,
    }


def _revision_hash(snapshot: Mapping[str, Any]) -> str:
    return content_hash(_revision_payload(snapshot))


def _validate_snapshot(snapshot: dict[str, Any], sources: dict[str, Any]) -> None:
    validate_document(snapshot, SCHEMAS / "observed-facts.schema.json")
    validate_observed_facts_contract(snapshot, sources)


def _candidate_map(universe: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    candidates = [
        item for item in universe["instruments"] if item["country"] == "TW"
    ]
    result = {item["symbol"]: item for item in candidates}
    if len(candidates) != 10 or len(result) != 10:
        raise ArchiveError("Taiwan archive universe must contain exactly 10 symbols")
    return result


def _load_archive_entries(
    observation_dir: Path,
    sources: dict[str, Any],
) -> dict[Path, dict[str, Any]]:
    entries: dict[Path, dict[str, Any]] = {}
    archive_root = observation_dir / "archive"
    if not archive_root.exists():
        return entries
    for path in sorted(archive_root.glob("*/*/*.json")):
        entry = load_json_strict(path)
        validate_document(entry, ARCHIVE_SCHEMA)
        _validate_snapshot(entry["observation"], sources)
        relative = path.relative_to(observation_dir)
        if entry["archive_path"] != relative.as_posix():
            raise ArchiveError(f"{path}: archive_path does not match file location")
        if entry["content_sha256"] != _revision_hash(entry["observation"]):
            raise ArchiveError(f"{path}: observation revision hash mismatch")
        entries[path] = entry
    return entries


def _group_entries(
    entries: Mapping[Path, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for entry in entries.values():
        grouped[entry["symbol"]].append(entry)
    for symbol in grouped:
        grouped[symbol].sort(key=lambda item: item["revision"]["sequence"])
    return grouped


def _validate_chain(symbol: str, entries: list[dict[str, Any]]) -> None:
    seen_ids: set[str] = set()
    seen_hashes: set[str] = set()
    previous: dict[str, Any] | None = None
    for sequence, entry in enumerate(entries, start=1):
        revision = entry["revision"]
        if revision["sequence"] != sequence:
            raise ArchiveError(f"{symbol}: revision sequence is not contiguous")
        expected_previous = None if previous is None else previous["archive_id"]
        if revision["previous_archive_id"] != expected_previous:
            raise ArchiveError(f"{symbol}: previous archive lineage is broken")
        relation = revision["relation"]
        if sequence == 1 and relation != "initial":
            raise ArchiveError(f"{symbol}: first archive entry must be initial")
        if sequence > 1 and relation == "initial":
            raise ArchiveError(f"{symbol}: later archive entry cannot be initial")
        if relation == "correction":
            if previous is None or entry["market_session_date"] != previous["market_session_date"]:
                raise ArchiveError(f"{symbol}: correction must target the same market session")
            if revision["correction_of_archive_id"] != previous["archive_id"]:
                raise ArchiveError(f"{symbol}: correction_of_archive_id is invalid")
        elif revision["correction_of_archive_id"] is not None:
            raise ArchiveError(f"{symbol}: only corrections may set correction_of_archive_id")
        if entry["archive_id"] in seen_ids or entry["content_sha256"] in seen_hashes:
            raise ArchiveError(f"{symbol}: duplicate archive identity or revision hash")
        seen_ids.add(entry["archive_id"])
        seen_hashes.add(entry["content_sha256"])
        previous = entry


def _entry_for_snapshot(
    snapshot: dict[str, Any],
    entries: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any], str]:
    revision_hash = _revision_hash(snapshot)
    market_session_date = snapshot["facts"]["market_session"]["date"]
    if entries:
        latest = entries[-1]
        if revision_hash == latest["content_sha256"]:
            return None, latest, "duplicate"
        if any(item["content_sha256"] == revision_hash for item in entries[:-1]):
            raise ArchiveError(
                f"{snapshot['symbol']}: refusing rollback to an older archived revision"
            )
        previous_session = _parse_date(
            latest["market_session_date"], "previous market session"
        )
        current_session = _parse_date(market_session_date, "market session")
        if current_session < previous_session:
            raise ArchiveError(
                f"{snapshot['symbol']}: refusing observation older than last-known-good"
            )
        relation = "correction" if current_session == previous_session else "new_session"
        sequence = latest["revision"]["sequence"] + 1
        previous_id = latest["archive_id"]
        correction_of = latest["archive_id"] if relation == "correction" else None
    else:
        relation = "initial"
        sequence = 1
        previous_id = None
        correction_of = None
    archive_id = (
        f"{snapshot['instrument_id']}@{market_session_date}#"
        f"{revision_hash[:16]}"
    )
    archive_path = (
        Path("archive")
        / snapshot["symbol"]
        / market_session_date
        / f"{sequence:04d}-{revision_hash[:16]}.json"
    ).as_posix()
    entry = {
        "schema_version": "1.0.0",
        "archive_id": archive_id,
        "archive_path": archive_path,
        "instrument_id": snapshot["instrument_id"],
        "symbol": snapshot["symbol"],
        "slug": snapshot["slug"],
        "asset_type": snapshot["asset_type"],
        "source_kind": "official_observation",
        "official_as_of": snapshot["as_of"],
        "market_session_date": market_session_date,
        "fetched_at": snapshot["fetched_at"],
        "content_sha256": revision_hash,
        "revision": {
            "sequence": sequence,
            "relation": relation,
            "previous_archive_id": previous_id,
            "correction_of_archive_id": correction_of,
        },
        "observation": snapshot,
    }
    return entry, entry, relation


def _catalog_item(
    candidate: Mapping[str, Any],
    latest: Mapping[str, Any],
    history_count: int,
    evaluated_at: str,
    calendar: Mapping[str, Any],
) -> dict[str, Any]:
    observation = latest["observation"]
    available = list(observation["coverage"]["available_fact_groups"])
    return {
        "instrument_id": candidate["instrument_id"],
        "symbol": candidate["symbol"],
        "slug": candidate["slug"],
        "asset_type": candidate["asset_type"],
        "source_kind": "official_observation",
        "official_as_of": observation["as_of"],
        "last_checked_at": evaluated_at,
        "latest_archive_id": latest["archive_id"],
        "latest_archive_path": latest["archive_path"],
        "last_known_good_archive_id": latest["archive_id"],
        "last_known_good_archive_path": latest["archive_path"],
        "history_count": history_count,
        "freshness": evaluate_freshness(
            latest["market_session_date"],
            evaluated_at=evaluated_at,
            calendar=calendar,
        ),
        "model_input_coverage": {
            "available_fact_groups": available,
            "available_fact_group_count": len(available),
            "used_fact_groups": [],
            "used_fact_group_count": 0,
            "coverage_percent": 0,
            "used_in_signal": False,
            "status": "not_connected",
        },
    }


def _write_temp(target: Path, payload: bytes) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
        os.chmod(handle.name, 0o644)
        return Path(handle.name)


def _promote_fail_closed(
    replacements: Mapping[Path, bytes],
    append_only: Mapping[Path, bytes],
) -> None:
    staged = {target: _write_temp(target, payload) for target, payload in replacements.items()}
    backups = {
        target: target.read_bytes() if target.exists() else None
        for target in replacements
    }
    replaced: list[Path] = []
    created: list[Path] = []
    try:
        for target, payload in append_only.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                if target.read_bytes() != payload:
                    raise ArchiveError(f"append-only archive collision: {target}")
                continue
            with target.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            created.append(target)
        for target in sorted(staged, key=lambda path: str(path)):
            os.replace(staged[target], target)
            replaced.append(target)
    except Exception:
        for target in reversed(replaced):
            previous = backups[target]
            if previous is None:
                target.unlink(missing_ok=True)
            else:
                rollback = _write_temp(target, previous)
                os.replace(rollback, target)
        for target in reversed(created):
            target.unlink(missing_ok=True)
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def archive_and_publish(
    snapshots: Mapping[str, dict[str, Any]],
    *,
    observation_dir: Path = DEFAULT_OBSERVATION_DIR,
    evaluated_at: str,
    universe: dict[str, Any] | None = None,
    sources: dict[str, Any] | None = None,
    calendar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    universe = universe or load_json_strict(ROOT / "config" / "universe.json")
    sources = sources or load_json_strict(ROOT / "config" / "sources.json")
    calendar = calendar or _load_calendar()
    candidates = _candidate_map(universe)
    if set(snapshots) != set(candidates):
        raise ArchiveError("snapshot batch must exactly cover the 10 Taiwan candidates")
    _parse_datetime(evaluated_at, "evaluated_at")

    existing = _load_archive_entries(observation_dir, sources)
    grouped = _group_entries(existing)
    for symbol, entries in grouped.items():
        if symbol not in candidates:
            raise ArchiveError(f"unexpected archive symbol: {symbol}")
        _validate_chain(symbol, entries)

    new_entries: dict[Path, dict[str, Any]] = {}
    latest_by_symbol: dict[str, dict[str, Any]] = {}
    relations: dict[str, str] = {}
    replacement_snapshots: dict[str, dict[str, Any]] = {}
    for symbol, candidate in sorted(candidates.items()):
        snapshot = snapshots[symbol]
        _validate_snapshot(snapshot, sources)
        for field in ("instrument_id", "symbol", "slug", "asset_type"):
            if snapshot[field] != candidate[field]:
                raise ArchiveError(f"{symbol}: snapshot {field} mismatch")
        planned, latest, relation = _entry_for_snapshot(snapshot, grouped.get(symbol, []))
        relations[symbol] = relation
        latest_by_symbol[symbol] = latest
        if planned is not None:
            target = observation_dir / planned["archive_path"]
            validate_document(planned, ARCHIVE_SCHEMA)
            new_entries[target] = planned
            replacement_snapshots[symbol] = snapshot
        else:
            replacement_snapshots[symbol] = latest["observation"]

    catalog = {
        "schema_version": "1.0.0",
        "catalog_id": f"twse-official-observations@{evaluated_at}",
        "market": "TWSE",
        "source_kind": "official_observation",
        "calendar_id": calendar["calendar_id"],
        "evaluated_at": evaluated_at,
        "instruments": [
            _catalog_item(
                candidates[symbol],
                latest_by_symbol[symbol],
                len(grouped.get(symbol, [])) + (1 if symbol in {item["symbol"] for item in new_entries.values()} else 0),
                evaluated_at,
                calendar,
            )
            for symbol in sorted(candidates)
        ],
    }
    validate_document(catalog, CATALOG_SCHEMA)

    append_only = {
        path: _pretty_bytes(entry) for path, entry in new_entries.items()
    }
    replacements = {
        observation_dir / f"{symbol}.json": _pretty_bytes(snapshot)
        for symbol, snapshot in replacement_snapshots.items()
    }
    replacements[observation_dir / "status" / "catalog.json"] = _pretty_bytes(catalog)
    _promote_fail_closed(replacements, append_only)

    load_and_validate_store(
        universe,
        sources,
        observation_dir=observation_dir,
        calendar=calendar,
    )
    return {
        "status": "success",
        "new_archive_entries": len(new_entries),
        "duplicates": sum(1 for value in relations.values() if value == "duplicate"),
        "corrections": sum(1 for value in relations.values() if value == "correction"),
        "new_sessions": sum(1 for value in relations.values() if value == "new_session"),
        "initial": sum(1 for value in relations.values() if value == "initial"),
        "catalog": str(observation_dir / "status" / "catalog.json"),
    }


def load_and_validate_store(
    universe: Mapping[str, Any],
    sources: dict[str, Any],
    *,
    observation_dir: Path = DEFAULT_OBSERVATION_DIR,
    calendar: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[Path, dict[str, Any]]]:
    calendar = calendar or _load_calendar()
    candidates = _candidate_map(universe)
    catalog_path = observation_dir / "status" / "catalog.json"
    catalog = load_json_strict(catalog_path)
    validate_document(catalog, CATALOG_SCHEMA)
    if catalog["calendar_id"] != calendar["calendar_id"]:
        raise ArchiveError("catalog calendar_id does not match configured calendar")
    catalog_items = {item["symbol"]: item for item in catalog["instruments"]}
    if set(catalog_items) != set(candidates) or len(catalog["instruments"]) != 10:
        raise ArchiveError("catalog must exactly cover the 10 Taiwan candidates")

    entries = _load_archive_entries(observation_dir, sources)
    grouped = _group_entries(entries)
    if set(grouped) != set(candidates):
        raise ArchiveError("archive membership must exactly cover the 10 Taiwan candidates")
    for symbol, candidate in candidates.items():
        chain = grouped[symbol]
        _validate_chain(symbol, chain)
        latest = chain[-1]
        item = catalog_items[symbol]
        for field in ("instrument_id", "symbol", "slug", "asset_type"):
            if item[field] != candidate[field]:
                raise ArchiveError(f"{symbol}: catalog {field} mismatch")
        if item["history_count"] != len(chain):
            raise ArchiveError(f"{symbol}: catalog history_count mismatch")
        for prefix in ("latest", "last_known_good"):
            if item[f"{prefix}_archive_id"] != latest["archive_id"]:
                raise ArchiveError(f"{symbol}: {prefix} archive id mismatch")
            if item[f"{prefix}_archive_path"] != latest["archive_path"]:
                raise ArchiveError(f"{symbol}: {prefix} archive path mismatch")
        expected_status = evaluate_freshness(
            latest["market_session_date"],
            evaluated_at=catalog["evaluated_at"],
            calendar=calendar,
        )
        if canonical_json(item["freshness"]) != canonical_json(expected_status):
            raise ArchiveError(f"{symbol}: freshness status is not reproducible")
        latest_path = observation_dir / f"{symbol}.json"
        latest_snapshot = load_json_strict(latest_path)
        _validate_snapshot(latest_snapshot, sources)
        if canonical_json(latest_snapshot) != canonical_json(latest["observation"]):
            raise ArchiveError(f"{symbol}: latest snapshot diverges from last-known-good")
        if item["official_as_of"] != latest_snapshot["as_of"]:
            raise ArchiveError(f"{symbol}: official_as_of mismatch")
        coverage = item["model_input_coverage"]
        if coverage["used_fact_group_count"] != 0 or coverage["coverage_percent"] != 0:
            raise ArchiveError(f"{symbol}: official observations must remain outside model inputs")
        if coverage["used_fact_groups"] or coverage["used_in_signal"]:
            raise ArchiveError(f"{symbol}: model input isolation is broken")
    return catalog, entries


def _load_latest_snapshots(observation_dir: Path) -> dict[str, dict[str, Any]]:
    return {
        path.stem: load_json_strict(path)
        for path in sorted(observation_dir.glob("*.json"))
        if path.stem.isdigit()
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or validate the append-only Taiwan observation archive"
    )
    parser.add_argument("command", choices=("bootstrap", "validate"), nargs="?", default="validate")
    parser.add_argument("--observation-dir", type=Path, default=DEFAULT_OBSERVATION_DIR)
    parser.add_argument("--evaluated-at")
    args = parser.parse_args()
    try:
        universe = load_json_strict(ROOT / "config" / "universe.json")
        sources = load_json_strict(ROOT / "config" / "sources.json")
        if args.command == "bootstrap":
            snapshots = _load_latest_snapshots(args.observation_dir)
            evaluated_at = args.evaluated_at or max(
                snapshot["fetched_at"] for snapshot in snapshots.values()
            )
            result = archive_and_publish(
                snapshots,
                observation_dir=args.observation_dir,
                evaluated_at=evaluated_at,
                universe=universe,
                sources=sources,
            )
        else:
            catalog, entries = load_and_validate_store(
                universe, sources, observation_dir=args.observation_dir
            )
            result = {
                "status": "valid",
                "catalog_id": catalog["catalog_id"],
                "instruments": len(catalog["instruments"]),
                "archive_entries": len(entries),
            }
    except (ArchiveError, ContractError, ValueError) as exc:
        print(f"archive error: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
