from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from src.render.markdown import render_report
from src.render.site import (
    SITE_URL,
    render_history,
    render_home,
    render_instrument,
    render_market,
    render_methodology,
    render_not_found,
    render_status,
)
from src.validation.contracts import (
    ContractError,
    canonical_json,
    content_hash,
    load_json_strict,
    validate_document,
    validate_signal_contract,
    validate_universe_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
SCHEMAS = ROOT / "schemas"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "research_snapshot.json"
ASSET_DIR = ROOT / "src" / "render" / "assets"
SOCIAL_PREVIEW_PATH = ROOT / "docs" / "assets" / "og.png"


def _pretty_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _component() -> dict[str, Any]:
    return {"score": None, "confidence": 0, "status": "not_evaluated"}


def _horizon(name: str) -> dict[str, Any]:
    return {
        "horizon": name,
        "score": None,
        "stance": "NO_SIGNAL",
        "confidence": 0,
        "calibration_status": "not_available",
        "supporting_evidence": [],
        "contrary_evidence": [],
        "risk_flags": [
            "UNAPPROVED_UNIVERSE",
            "LIVE_DATA_MISSING",
            "MODEL_UNCALIBRATED",
        ],
        "invalidation_conditions": [
            "Owner approves a versioned universe and model after required validation."
        ],
    }


def build_signal(
    universe: dict[str, Any],
    approvals: dict[str, Any],
    model: dict[str, Any],
    fixture: dict[str, Any],
) -> dict[str, Any]:
    input_hash = content_hash(
        {
            "universe": universe,
            "approvals": approvals,
            "model": model,
            "fixture": fixture,
        }
    )
    timestamp = fixture["generated_at"].replace("-", "").replace(":", "")
    run_id = f"{timestamp}-fixture-{input_hash[:8]}"
    fixture_hash = content_hash(fixture)
    source = {
        **fixture["source"],
        "content_hash": fixture_hash,
    }
    instruments = []
    for candidate in universe["instruments"]:
        instruments.append(
            {
                "instrument_id": candidate["instrument_id"],
                "symbol": candidate["symbol"],
                "slug": candidate["slug"],
                "name_zh": candidate["name_zh"],
                "name_en": candidate["name_en"],
                "country": candidate["country"],
                "market": candidate["market"],
                "asset_type": candidate["asset_type"],
                "currency": candidate["currency"],
                "status": candidate["status"],
                "enabled": candidate["enabled"],
                "themes": candidate["themes"],
                "benchmark_id": candidate["benchmark_id"],
                "data_status": {
                    "status": "fixture",
                    "last_market_session": None,
                    "critical_missing": list(fixture["required_missing"]),
                    "warnings": list(fixture["warnings"]),
                },
                "horizons": [_horizon(name) for name in ("1W", "1M", "3M", "12M")],
                "components": {
                    key: _component()
                    for key in (
                        "macro",
                        "fundamental",
                        "valuation",
                        "technical",
                        "cycle",
                        "events",
                    )
                },
                "relative_performance": {
                    "period": "3M",
                    "value": None,
                    "benchmark_id": candidate["benchmark_id"],
                    "status": "not_available",
                },
                "model_applicability": {
                    "applicable": False,
                    "reason": "Universe 尚未核准，且 live 資料與模型校準尚未完成。",
                },
                "provenance": [source],
            }
        )

    events = sorted(
        fixture["events"],
        key=lambda event: (-event["priority"], event["event_id"]),
    )
    return {
        "schema_version": "1.0.0",
        "run": {
            "run_id": run_id,
            "as_of": fixture["as_of"],
            "generated_at": fixture["generated_at"],
            "git_sha": fixture["git_sha"],
            "input_hash": input_hash,
            "model_version": fixture["model_version"],
            "mode": "research_only",
            "data_kind": "fixture",
        },
        "summary": {
            "tracked_count": len(instruments),
            "proposed_count": sum(
                1 for item in instruments if item["status"] == "proposed"
            ),
            "approved_enabled_count": sum(
                1
                for item in instruments
                if item["status"] == "approved" and item["enabled"]
            ),
            "stances": {"BUY": 0, "HOLD": 0, "SELL": 0, "NO_SIGNAL": len(instruments)},
            "critical_events": sum(
                1 for event in events if event["materiality"] == "high"
            ),
        },
        "markets": fixture["market_context"],
        "instruments": instruments,
        "events": events,
        "source_manifest": [
            {
                "source_id": fixture["source"]["source_id"],
                "path": fixture["source"]["source_url"],
                "content_hash": fixture_hash,
                "kind": "fixture",
            }
        ],
    }


def build_run_record(signal: dict[str, Any], outputs: list[str]) -> dict[str, Any]:
    run = signal["run"]
    return {
        "run_id": run["run_id"],
        "run_type": "fixture_build",
        "as_of_date": run["as_of"],
        "started_at": run["generated_at"],
        "completed_at": run["generated_at"],
        "git_sha": run["git_sha"],
        "input_hash": run["input_hash"],
        "source_manifest_hash": content_hash(signal["source_manifest"]),
        "schema_versions": {
            "universe": "1.0.0",
            "signal": "1.0.0",
            "event": "1.0.0",
            "agent_run": "1.0.0",
        },
        "model_version": run["model_version"],
        "status": "success",
        "outputs": outputs,
        "warnings": [
            "FIXTURE_DATA_ONLY",
            "UNIVERSE_OWNER_APPROVAL_REQUIRED",
            "PRODUCTION_SIGNALS_DISABLED",
        ],
        "errors": [],
        "manual_review_required": True,
    }


def _sitemap(signal: dict[str, Any]) -> str:
    paths = [
        "",
        "methodology.html",
        "status.html",
        "history.html",
        "markets/tw.html",
        "markets/jp.html",
        "markets/us.html",
    ]
    paths.extend(f"instruments/{item['slug']}.html" for item in signal["instruments"])
    urls = "".join(f"<url><loc>{SITE_URL}{path}</loc></url>" for path in paths)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>\n"
    )


def load_history(current: dict[str, Any]) -> list[dict[str, Any]]:
    by_date: dict[str, dict[str, Any]] = {}
    archive_dir = ROOT / "signals" / "archive"
    for path in sorted(archive_dir.glob("*.json")):
        archived = load_json_strict(path)
        validate_document(archived, SCHEMAS / "signal.schema.json")
        by_date[archived["run"]["as_of"]] = archived
    by_date[current["run"]["as_of"]] = current
    return [by_date[key] for key in sorted(by_date, reverse=True)]


def build_outputs(signal: dict[str, Any]) -> tuple[dict[Path, bytes], dict[str, Any]]:
    as_of = signal["run"]["as_of"]
    run_id = signal["run"]["run_id"]
    year, month, _ = as_of.split("-")
    signal_json = _pretty_json(signal).encode("utf-8")
    report = (render_report(signal) + "\n").encode("utf-8")
    history = load_history(signal)

    outputs: dict[Path, bytes] = {
        ROOT / "signals" / "latest.json": signal_json,
        ROOT / "signals" / "archive" / f"{as_of}.json": signal_json,
        ROOT / "reports" / "latest.md": report,
        ROOT / "reports" / "archive" / f"{as_of}.md": report,
        ROOT / "docs" / "index.html": render_home(signal).encode("utf-8"),
        ROOT / "docs" / "methodology.html": render_methodology(signal).encode("utf-8"),
        ROOT / "docs" / "status.html": render_status(signal).encode("utf-8"),
        ROOT / "docs" / "history.html": render_history(history).encode("utf-8"),
        ROOT / "docs" / "404.html": render_not_found().encode("utf-8"),
        ROOT / "docs" / ".nojekyll": b"",
        ROOT / "docs" / "data" / "latest.json": signal_json,
        ROOT / "docs" / "data" / "archive" / f"{as_of}.json": signal_json,
        ROOT / "docs" / "assets" / "css" / "site.css": (
            ASSET_DIR / "site.css"
        ).read_bytes(),
        ROOT / "docs" / "assets" / "js" / "app.js": (
            ASSET_DIR / "app.js"
        ).read_bytes(),
        ROOT / "docs" / "assets" / "og.png": SOCIAL_PREVIEW_PATH.read_bytes(),
        ROOT / "docs" / "robots.txt": (
            f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}sitemap.xml\n"
        ).encode("utf-8"),
        ROOT / "docs" / "sitemap.xml": _sitemap(signal).encode("utf-8"),
    }
    for archived in history:
        archive_date = archived["run"]["as_of"]
        outputs[ROOT / "docs" / "data" / "archive" / f"{archive_date}.json"] = (
            _pretty_json(archived).encode("utf-8")
        )
    for country in ("TW", "JP", "US"):
        outputs[ROOT / "docs" / "markets" / f"{country.lower()}.html"] = (
            render_market(signal, country).encode("utf-8")
        )
    for item in signal["instruments"]:
        outputs[ROOT / "docs" / "instruments" / f"{item['slug']}.html"] = (
            render_instrument(signal, item).encode("utf-8")
        )
    for schema_path in sorted(SCHEMAS.glob("*.schema.json")):
        outputs[ROOT / "docs" / "schemas" / schema_path.name] = schema_path.read_bytes()

    relative_outputs = sorted(str(path.relative_to(ROOT)) for path in outputs)
    run_record_path = (
        ROOT / "agent-runs" / year / month / f"{run_id}.json"
    )
    relative_outputs.append(str(run_record_path.relative_to(ROOT)))
    run_record = build_run_record(signal, relative_outputs)
    outputs[run_record_path] = _pretty_json(run_record).encode("utf-8")
    return outputs, run_record


def _preflight(outputs: dict[Path, bytes]) -> None:
    if not outputs:
        raise ContractError("build produced no outputs")
    for path, payload in outputs.items():
        if path.suffix in {".html", ".css", ".js", ".json", ".md", ".xml", ".txt"}:
            text = payload.decode("utf-8")
            if path.suffix == ".html" and "</html>" not in text:
                raise ContractError(f"{path}: incomplete HTML")
            if path.suffix == ".json":
                json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(
                    ContractError(f"{path}: non-standard JSON constant {value}")
                ))
        if path.name == "og.png" and not payload.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ContractError("social preview is not a PNG")


def publish_atomically(outputs: dict[Path, bytes]) -> None:
    _preflight(outputs)
    staged: dict[Path, Path] = {}
    backups: dict[Path, bytes | None] = {}
    replaced: list[Path] = []
    try:
        for target, payload in outputs.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            backups[target] = target.read_bytes() if target.exists() else None
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
                staged[target] = Path(handle.name)
        for target in sorted(outputs, key=lambda path: str(path)):
            os.replace(staged[target], target)
            replaced.append(target)
    except Exception:
        for target in reversed(replaced):
            previous = backups[target]
            if previous is None:
                target.unlink(missing_ok=True)
                continue
            with tempfile.NamedTemporaryFile(
                dir=target.parent,
                prefix=f".{target.name}.rollback.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                handle.write(previous)
                handle.flush()
                os.fsync(handle.fileno())
                os.chmod(handle.name, 0o644)
                rollback_path = Path(handle.name)
            os.replace(rollback_path, target)
        raise
    finally:
        for path in staged.values():
            path.unlink(missing_ok=True)


def load_inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    universe = load_json_strict(CONFIG / "universe.json")
    approvals = load_json_strict(CONFIG / "approvals.json")
    model = load_json_strict(CONFIG / "model_weights.json")
    fixture = load_json_strict(FIXTURE_PATH)
    validate_document(universe, SCHEMAS / "universe.schema.json")
    validate_universe_contract(universe, approvals)
    return universe, approvals, model, fixture


def command_build() -> dict[str, Any]:
    universe, approvals, model, fixture = load_inputs()
    signal = build_signal(universe, approvals, model, fixture)
    validate_document(signal, SCHEMAS / "signal.schema.json")
    validate_signal_contract(signal, approvals)
    outputs, run_record = build_outputs(signal)
    validate_document(run_record, SCHEMAS / "agent-run.schema.json")
    publish_atomically(outputs)
    validate_existing()
    return {
        "status": "success",
        "run_id": signal["run"]["run_id"],
        "outputs": len(outputs),
        "instruments": len(signal["instruments"]),
        "mode": signal["run"]["mode"],
    }


def validate_existing() -> None:
    _, approvals, _, _ = load_inputs()
    signal = load_json_strict(ROOT / "signals" / "latest.json")
    validate_document(signal, SCHEMAS / "signal.schema.json")
    validate_signal_contract(signal, approvals)
    docs_signal = load_json_strict(ROOT / "docs" / "data" / "latest.json")
    archive_signal = load_json_strict(
        ROOT / "signals" / "archive" / f"{signal['run']['as_of']}.json"
    )
    if canonical_json(signal) != canonical_json(docs_signal):
        raise ContractError("docs/data/latest.json diverges from signals/latest.json")
    if canonical_json(signal) != canonical_json(archive_signal):
        raise ContractError("archive signal diverges from latest signal")
    run_id = signal["run"]["run_id"]
    year, month, _ = signal["run"]["as_of"].split("-")
    run_record = load_json_strict(
        ROOT / "agent-runs" / year / month / f"{run_id}.json"
    )
    validate_document(run_record, SCHEMAS / "agent-run.schema.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="StockmarketAgent deterministic pipeline")
    parser.add_argument(
        "command",
        nargs="?",
        choices=("build", "validate"),
        default="build",
    )
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = command_build()
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            validate_existing()
            print('{"status":"valid"}')
    except ContractError as exc:
        print(f"contract error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
