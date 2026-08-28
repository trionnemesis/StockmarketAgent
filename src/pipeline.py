from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.analysis import AnalysisInputError, build_research_analysis
from src.render.markdown import render_report, render_source_feasibility as render_source_feasibility_md, render_universe_review as render_universe_review_md
from src.render.site import (
    SITE_URL,
    render_history,
    render_home,
    render_instrument,
    render_market,
    render_methodology,
    render_not_found,
    render_status,
    render_source_feasibility,
    render_universe_review,
)
from src.validation.contracts import (
    ContractError,
    canonical_json,
    content_hash,
    load_json_strict,
    validate_document,
    validate_agent_run_contract,
    validate_action_thresholds_contract,
    validate_approvals_contract,
    validate_model_weights_contract,
    validate_observed_facts_contract,
    validate_schedules_contract,
    validate_signal_contract,
    validate_source_contract,
    validate_theme_contract,
    validate_review_contract,
    validate_universe_contract,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config"
SCHEMAS = ROOT / "schemas"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "research_snapshot.json"
ANALYSIS_FIXTURE_PATH = ROOT / "tests" / "fixtures" / "research_analysis_snapshot.json"
ASSET_DIR = ROOT / "src" / "render" / "assets"
SOCIAL_PREVIEW_PATH = ROOT / "docs" / "assets" / "og.png"
TSMC_OBSERVATION_PATH = ROOT / "data" / "observations" / "twse" / "2330.json"
SOURCE_REVISION_PATHS = (
    "config",
    "data/observations",
    "schemas",
    "src",
    "tests/fixtures",
)
LEGACY_GLOBAL_AGENT_RUN_IDS = {"20260827T120000Z-fixture-f7c1c115"}


def _pretty_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def _parse_aware_datetime(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(
            value[:-1] + "+00:00" if value.endswith("Z") else value
        )
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{label}: invalid date-time") from exc
    if parsed.tzinfo is None:
        raise ContractError(f"{label}: timezone is required")
    return parsed


def _validate_fixture_alignment(
    fixture: dict[str, Any],
    analysis_fixture: dict[str, Any],
    model: dict[str, Any],
) -> None:
    for field in ("as_of", "generated_at", "model_version"):
        if fixture.get(field) != analysis_fixture.get(field):
            raise ContractError(f"research fixtures disagree on {field}")
    if fixture.get("model_version") != model.get("model_version"):
        raise ContractError("research fixtures and model config disagree on model_version")

    try:
        as_of = date.fromisoformat(analysis_fixture["as_of"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ContractError("analysis fixture as_of is invalid") from exc
    generated_at = _parse_aware_datetime(
        analysis_fixture["generated_at"], "analysis fixture generated_at"
    )
    if generated_at.date() != as_of:
        raise ContractError("analysis fixture generated_at must fall on as_of")

    for event in fixture.get("events", []):
        published_at = _parse_aware_datetime(
            event.get("published_at"),
            f"event {event.get('event_id', '<unknown>')} published_at",
        )
        if published_at > generated_at or published_at.date() > as_of:
            raise ContractError(
                f"event {event.get('event_id', '<unknown>')} is after the research run"
            )

    for timestamp_name in ("published_at", "observed_at", "fetched_at"):
        timestamp = fixture.get("source", {}).get(timestamp_name)
        if timestamp is None:
            continue
        if _parse_aware_datetime(timestamp, f"base fixture source {timestamp_name}") > generated_at:
            raise ContractError(f"base fixture source {timestamp_name} is after the research run")


def source_revision() -> str:
    """Return the latest committed revision that changed executable build inputs."""

    override = os.environ.get("STOCKMARKETAGENT_SOURCE_REVISION")
    if override is not None:
        revision = override.strip().lower()
    else:
        try:
            completed = subprocess.run(
                [
                    "git",
                    "log",
                    "-1",
                    "--format=%H",
                    "--",
                    *SOURCE_REVISION_PATHS,
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ContractError(
                "cannot resolve source revision; provide STOCKMARKETAGENT_SOURCE_REVISION"
            ) from exc
        revision = completed.stdout.strip().lower()
    if re.fullmatch(r"[a-f0-9]{40}", revision) is None:
        raise ContractError("source revision must be a full 40-character Git commit SHA")
    try:
        subprocess.run(
            ["git", "cat-file", "-e", f"{revision}^{{commit}}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractError("source revision is not a resolvable Git commit") from exc
    try:
        subprocess.run(
            ["git", "diff", "--quiet", revision, "--", *SOURCE_REVISION_PATHS],
            cwd=ROOT,
            check=True,
            capture_output=True,
        )
        status = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "--untracked-files=all",
                "--",
                *SOURCE_REVISION_PATHS,
            ],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractError("source revision does not match current build inputs") from exc
    if status.stdout.strip():
        raise ContractError("source revision does not include all current build inputs")
    return revision


def build_signal(
    universe: dict[str, Any],
    approvals: dict[str, Any],
    model: dict[str, Any],
    fixture: dict[str, Any],
    themes: dict[str, Any] | None = None,
    benchmarks: dict[str, Any] | None = None,
    sources: dict[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    analysis_fixture: dict[str, Any] | None = None,
    thresholds: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not approvals["research_analysis_enabled"]:
        raise ContractError("research analysis is disabled")
    analysis_fixture = analysis_fixture or load_json_strict(ANALYSIS_FIXTURE_PATH)
    thresholds = thresholds or load_json_strict(CONFIG / "action_thresholds.json")
    _validate_fixture_alignment(fixture, analysis_fixture, model)
    revision = source_revision()
    try:
        analysis = build_research_analysis(
            universe, model, thresholds, analysis_fixture
        )
    except AnalysisInputError as exc:
        raise ContractError(f"research analysis input: {exc}") from exc
    validate_document(analysis, SCHEMAS / "research-analysis.schema.json")

    support_inputs = {"themes": themes, "benchmarks": benchmarks, "sources": sources, "review": review}
    input_hash = content_hash(
        {
            "universe": universe,
            "approvals": approvals,
            "model": model,
            "thresholds": thresholds,
            "fixture": fixture,
            "analysis_fixture": analysis_fixture,
            "source_revision": revision,
            **support_inputs,
            "build_fingerprint": build_fingerprint(),
        }
    )
    timestamp = analysis["run"]["generated_at"].replace("-", "").replace(":", "")
    run_id = f"{timestamp}-research-{input_hash[:8]}"
    fixture_hash = content_hash(fixture)
    analysis_hash = content_hash(analysis_fixture)
    analysis_by_id = {
        item["instrument_id"]: item for item in analysis["instruments"]
    }
    instruments = []
    for candidate in universe["instruments"]:
        result = analysis_by_id[candidate["instrument_id"]]
        data_status = result["data_status"]
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
                "selection_rationale": candidate["selection_rationale"],
                "data_status": {
                    "status": (
                        "stale"
                        if data_status["freshness"] == "stale"
                        else "research_fixture"
                    ),
                    "last_market_session": None,
                    "critical_missing": list(data_status["critical_missing"]),
                    "warnings": [
                        "SYNTHETIC_RESEARCH_FIXTURE",
                        "MODEL_UNCALIBRATED",
                        *data_status["risk_gate_reasons"],
                    ],
                },
                "horizons": result["horizons"],
                "components": result["components"],
                "relative_performance": {
                    "period": "3M",
                    "value": None,
                    "benchmark_id": candidate["benchmark_id"],
                    "status": "not_available",
                },
                "model_applicability": {
                    "applicable": True,
                    "reason": (
                        "僅適用於 deterministic synthetic scenario 的工程驗證；"
                        "production routing、live 資料與回測校準仍未核准。"
                    ),
                },
                "provenance": result["provenance"],
            }
        )

    events = sorted(
        fixture["events"],
        key=lambda event: (-event["priority"], event["event_id"]),
    )
    stance_counts = {stance: 0 for stance in ("BUY", "HOLD", "SELL", "NO_SIGNAL")}
    for item in instruments:
        three_month = next(
            horizon for horizon in item["horizons"] if horizon["horizon"] == "3M"
        )
        stance_counts[three_month["stance"]] += 1
    markets = [
        {
            **market,
            "status": "research_fixture",
            "last_market_session": None,
            "notice": (
                "Synthetic scenario fixture；不含 live 行情或當前市場日期，"
                "研究態度尚未校準。"
            ),
        }
        for market in fixture["market_context"]
    ]
    return {
        "schema_version": "1.1.0",
        "run": {
            "run_id": run_id,
            "as_of": analysis["run"]["as_of"],
            "generated_at": analysis["run"]["generated_at"],
            "git_sha": revision,
            "input_hash": input_hash,
            "model_version": analysis["run"]["model_version"],
            "mode": "research_only",
            "data_kind": "research_fixture",
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
            "stances": stance_counts,
            "critical_events": sum(
                1 for event in events if event["materiality"] == "high"
            ),
        },
        "markets": markets,
        "instruments": instruments,
        "events": events,
        "source_manifest": [
            {
                "source_id": analysis["provenance"]["source_id"],
                "path": analysis["provenance"]["source_url"],
                "content_hash": analysis_hash,
                "kind": "research_fixture",
            },
            {
                "source_id": fixture["source"]["source_id"],
                "path": fixture["source"]["source_url"],
                "content_hash": fixture_hash,
                "kind": "research_fixture",
            },
        ],
    }


def build_fingerprint() -> str:
    files = sorted((ROOT / "src").rglob("*.py")) + sorted(SCHEMAS.glob("*.json")) + sorted(ASSET_DIR.rglob("*"))
    manifest = {str(path.relative_to(ROOT)): content_hash(path.read_text(encoding="utf-8")) for path in files if path.is_file()}
    return content_hash(manifest)


def build_run_record(signal: dict[str, Any], outputs: list[str]) -> dict[str, Any]:
    run = signal["run"]
    return {
        "run_id": run["run_id"],
        "run_type": "research_analysis_build",
        "as_of_date": run["as_of"],
        "started_at": run["generated_at"],
        "completed_at": run["generated_at"],
        "git_sha": run["git_sha"],
        "input_hash": run["input_hash"],
        "source_manifest_hash": content_hash(signal["source_manifest"]),
        "schema_versions": {
            "universe": "1.0.0",
            "signal": "1.1.0",
            "event": "1.0.0",
            "agent_run": "1.1.0",
            "research_analysis": "1.0.0",
            "approvals": "1.0.0",
            "model_weights": "1.0.0",
            "action_thresholds": "1.0.0",
            "schedules": "1.0.0",
        },
        "model_version": run["model_version"],
        "status": "success",
        "outputs": outputs,
        "warnings": [
            "SYNTHETIC_RESEARCH_FIXTURE",
            "MODEL_UNCALIBRATED",
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
        "universe-review.html",
        "source-feasibility.html",
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
        if path.name == f"{current['run']['as_of']}.json":
            continue
        archived = load_json_strict(path)
        validate_document(archived, SCHEMAS / "signal.schema.json")
        by_date[archived["run"]["as_of"]] = archived
    by_date[current["run"]["as_of"]] = current
    return [by_date[key] for key in sorted(by_date, reverse=True)]


def load_tsmc_observation(sources: dict[str, Any]) -> dict[str, Any]:
    observation = load_json_strict(TSMC_OBSERVATION_PATH)
    validate_document(observation, SCHEMAS / "observed-facts.schema.json")
    validate_observed_facts_contract(observation, sources)
    return observation


def build_outputs(
    signal: dict[str, Any],
    sources: dict[str, Any],
    review: dict[str, Any],
    observation: dict[str, Any] | None = None,
) -> tuple[dict[Path, bytes], dict[str, Any]]:
    observation = observation or load_tsmc_observation(sources)
    as_of = signal["run"]["as_of"]
    run_id = signal["run"]["run_id"]
    year, month, _ = as_of.split("-")
    signal_json = _pretty_json(signal).encode("utf-8")
    report = (render_report(signal) + "\n").encode("utf-8")
    review_md = (render_universe_review_md(review) + "\n").encode("utf-8")
    sources_md = (render_source_feasibility_md(sources) + "\n").encode("utf-8")
    history = load_history(signal)

    outputs: dict[Path, bytes] = {
        ROOT / "signals" / "latest.json": signal_json,
        ROOT / "signals" / "archive" / f"{as_of}.json": signal_json,
        ROOT / "signals" / "runs" / f"{run_id}.json": signal_json,
        ROOT / "reports" / "latest.md": report,
        ROOT / "reports" / "archive" / f"{as_of}.md": report,
        ROOT / "reports" / "runs" / f"{run_id}.md": report,
        ROOT / "docs" / "universe-review.md": review_md,
        ROOT / "docs" / "source-feasibility.md": sources_md,
        ROOT / "docs" / "universe-review.html": render_universe_review(review).encode("utf-8"),
        ROOT / "docs" / "source-feasibility.html": render_source_feasibility(sources).encode("utf-8"),
        ROOT / "docs" / "index.html": render_home(signal, review, sources).encode("utf-8"),
        ROOT / "docs" / "methodology.html": render_methodology(signal).encode("utf-8"),
        ROOT / "docs" / "status.html": render_status(signal).encode("utf-8"),
        ROOT / "docs" / "history.html": render_history(history).encode("utf-8"),
        ROOT / "docs" / "404.html": render_not_found().encode("utf-8"),
        ROOT / "docs" / ".nojekyll": b"",
        ROOT / "docs" / "data" / "latest.json": signal_json,
        ROOT / "docs" / "data" / "runs" / f"{run_id}.json": signal_json,
        ROOT / "docs" / "data" / "universe-review.json": _pretty_json(review).encode("utf-8"),
        ROOT / "docs" / "data" / "sources.json": _pretty_json(sources).encode("utf-8"),
        ROOT / "docs" / "data" / "observations" / "tsmc.json": _pretty_json(
            observation
        ).encode("utf-8"),
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
        item_observation = (
            observation if item["instrument_id"] == observation["instrument_id"] else None
        )
        outputs[ROOT / "docs" / "instruments" / f"{item['slug']}.html"] = (
            render_instrument(
                signal,
                item,
                next(
                    review_item
                    for review_item in review["instruments"]
                    if review_item["instrument_id"] == item["instrument_id"]
                ),
                item_observation,
            ).encode("utf-8")
        )
    for schema_path in sorted(SCHEMAS.glob("*.schema.json")):
        outputs[ROOT / "docs" / "schemas" / schema_path.name] = schema_path.read_bytes()

    run_record_path = (
        ROOT / "agent-runs" / year / month / f"{run_id}.json"
    )
    immutable_outputs = [
        f"signals/runs/{run_id}.json",
        f"reports/runs/{run_id}.md",
        f"docs/data/runs/{run_id}.json",
        str(run_record_path.relative_to(ROOT)),
    ]
    run_record = build_run_record(signal, immutable_outputs)
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


def load_inputs() -> tuple[dict[str, Any], ...]:
    universe = load_json_strict(CONFIG / "universe.json")
    approvals = load_json_strict(CONFIG / "approvals.json")
    model = load_json_strict(CONFIG / "model_weights.json")
    thresholds = load_json_strict(CONFIG / "action_thresholds.json")
    schedules = load_json_strict(CONFIG / "schedules.json")
    fixture = load_json_strict(FIXTURE_PATH)
    themes = load_json_strict(CONFIG / "themes.json")
    benchmarks = load_json_strict(CONFIG / "benchmarks.json")
    sources = load_json_strict(CONFIG / "sources.json")
    review = load_json_strict(CONFIG / "universe-review.json")
    validate_document(universe, SCHEMAS / "universe.schema.json")
    validate_document(approvals, SCHEMAS / "approvals.schema.json")
    validate_document(model, SCHEMAS / "model_weights.schema.json")
    validate_document(thresholds, SCHEMAS / "action_thresholds.schema.json")
    validate_document(schedules, SCHEMAS / "schedules.schema.json")
    validate_document(themes, SCHEMAS / "themes.schema.json")
    validate_document(benchmarks, SCHEMAS / "benchmarks.schema.json")
    validate_document(sources, SCHEMAS / "sources.schema.json")
    validate_document(review, SCHEMAS / "universe-review.schema.json")
    validate_universe_contract(universe, approvals)
    validate_approvals_contract(approvals)
    validate_model_weights_contract(model)
    validate_action_thresholds_contract(thresholds)
    validate_schedules_contract(schedules)
    validate_theme_contract(universe, themes)
    validate_source_contract(sources)
    validate_review_contract(universe, benchmarks, sources, review)
    return universe, approvals, model, fixture, themes, benchmarks, sources, review


def command_build() -> dict[str, Any]:
    universe, approvals, model, fixture, themes, benchmarks, sources, review = load_inputs()
    signal = build_signal(universe, approvals, model, fixture, themes, benchmarks, sources, review)
    validate_document(signal, SCHEMAS / "signal.schema.json")
    thresholds = load_json_strict(CONFIG / "action_thresholds.json")
    validate_signal_contract(signal, approvals, thresholds)
    observation = load_tsmc_observation(sources)
    outputs, run_record = build_outputs(signal, sources, review, observation)
    validate_document(run_record, SCHEMAS / "agent-run.schema.json")
    validate_agent_run_contract(run_record)
    publish_atomically(outputs)
    validate_existing()
    return {
        "status": "success",
        "run_id": signal["run"]["run_id"],
        "outputs": len(outputs),
        "instruments": len(signal["instruments"]),
        "mode": signal["run"]["mode"],
    }


def _load_json_at_revision(revision: str, repository_path: str) -> dict[str, Any]:
    if re.fullmatch(r"[a-f0-9]{40}", revision) is None:
        raise ContractError("historical config revision is not a full Git SHA")
    try:
        completed = subprocess.run(
            ["git", "show", f"{revision}:{repository_path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractError(
            f"cannot load historical config {repository_path} at {revision}"
        ) from exc
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8") as handle:
        handle.write(completed.stdout)
        handle.flush()
        value = load_json_strict(Path(handle.name))
    if not isinstance(value, dict):
        raise ContractError(f"historical config {repository_path} must be an object")
    return value


def _validate_run_bindings(
    signal: dict[str, Any], run_record: dict[str, Any], label: str
) -> None:
    expected = {
        "run_id": signal["run"]["run_id"],
        "as_of_date": signal["run"]["as_of"],
        "started_at": signal["run"]["generated_at"],
        "completed_at": signal["run"]["generated_at"],
        "git_sha": signal["run"]["git_sha"],
        "input_hash": signal["run"]["input_hash"],
        "model_version": signal["run"]["model_version"],
        "source_manifest_hash": content_hash(signal["source_manifest"]),
    }
    for field, expected_value in expected.items():
        if run_record[field] != expected_value:
            raise ContractError(f"{label}: Agent Run {field} does not match signal")


def _validate_immutable_run_history(
    current_thresholds: dict[str, Any],
) -> None:
    signal_paths = sorted((ROOT / "signals" / "runs").glob("*.json"))
    run_ids = {path.stem for path in signal_paths}
    docs_run_ids = {
        path.stem for path in (ROOT / "docs" / "data" / "runs").glob("*.json")
    }
    report_run_ids = {
        path.stem for path in (ROOT / "reports" / "runs").glob("*.md")
    }
    if docs_run_ids != run_ids:
        raise ContractError("Pages immutable signal mirror membership mismatch")
    if report_run_ids != run_ids:
        raise ContractError("immutable report membership mismatch")

    paired_agent_paths: set[Path] = set()
    for signal_path in signal_paths:
        historical_signal = load_json_strict(signal_path)
        validate_document(historical_signal, SCHEMAS / "signal.schema.json")
        run = historical_signal["run"]
        run_id = run["run_id"]
        if signal_path.stem != run_id:
            raise ContractError(f"{signal_path}: filename does not match run_id")

        docs_path = ROOT / "docs" / "data" / "runs" / f"{run_id}.json"
        report_path = ROOT / "reports" / "runs" / f"{run_id}.md"
        docs_signal = load_json_strict(docs_path)
        if canonical_json(docs_signal) != canonical_json(historical_signal):
            raise ContractError(f"{run_id}: Pages immutable signal mirror diverges")
        if not report_path.is_file() or report_path.stat().st_size == 0:
            raise ContractError(f"{run_id}: immutable report is missing or empty")

        year, month, _ = run["as_of"].split("-")
        agent_path = ROOT / "agent-runs" / year / month / f"{run_id}.json"
        if not agent_path.is_file():
            raise ContractError(f"{run_id}: Agent Run record is missing")
        run_record = load_json_strict(agent_path)
        validate_document(run_record, SCHEMAS / "agent-run.schema.json")
        validate_agent_run_contract(run_record)
        _validate_run_bindings(historical_signal, run_record, run_id)
        paired_agent_paths.add(agent_path.resolve())

        expected_outputs = {
            str(signal_path.relative_to(ROOT)),
            str(report_path.relative_to(ROOT)),
            str(docs_path.relative_to(ROOT)),
            str(agent_path.relative_to(ROOT)),
        }
        if len(run_record["outputs"]) != len(set(run_record["outputs"])):
            raise ContractError(f"{run_id}: Agent Run outputs must be unique")
        if set(run_record["outputs"]) != expected_outputs:
            raise ContractError(f"{run_id}: Agent Run immutable outputs mismatch")

        if historical_signal["schema_version"] == "1.1.0":
            revision = run["git_sha"]
            historical_approvals = _load_json_at_revision(
                revision, "config/approvals.json"
            )
            historical_thresholds = _load_json_at_revision(
                revision, "config/action_thresholds.json"
            )
            validate_document(
                historical_approvals, SCHEMAS / "approvals.schema.json"
            )
            validate_document(
                historical_thresholds, SCHEMAS / "action_thresholds.schema.json"
            )
            validate_approvals_contract(historical_approvals)
            validate_action_thresholds_contract(historical_thresholds)
            validate_signal_contract(
                historical_signal, historical_approvals, historical_thresholds
            )
        else:
            legacy_approvals = {
                "production_signal_enabled": False,
                "research_analysis_enabled": False,
            }
            validate_signal_contract(
                historical_signal, legacy_approvals, current_thresholds
            )

    for agent_path in sorted((ROOT / "agent-runs").glob("**/*.json")):
        historical_run = load_json_strict(agent_path)
        validate_document(historical_run, SCHEMAS / "agent-run.schema.json")
        validate_agent_run_contract(historical_run)
        if agent_path.resolve() in paired_agent_paths:
            continue
        if historical_run["run_id"] not in LEGACY_GLOBAL_AGENT_RUN_IDS:
            raise ContractError(
                f"{historical_run['run_id']}: Agent Run has no immutable signal"
            )
        for output in historical_run["outputs"]:
            relative = Path(output)
            if relative.is_absolute() or ".." in relative.parts:
                raise ContractError("legacy Agent Run contains an unsafe output path")
            if not (ROOT / relative).exists():
                raise ContractError(
                    f"{historical_run['run_id']}: legacy output is missing: {output}"
                )


def validate_existing() -> None:
    _, approvals, _, _, _, _, sources, _ = load_inputs()
    observation = load_tsmc_observation(sources)
    signal = load_json_strict(ROOT / "signals" / "latest.json")
    validate_document(signal, SCHEMAS / "signal.schema.json")
    thresholds = load_json_strict(CONFIG / "action_thresholds.json")
    validate_signal_contract(signal, approvals, thresholds)
    docs_signal = load_json_strict(ROOT / "docs" / "data" / "latest.json")
    archive_signal = load_json_strict(
        ROOT / "signals" / "archive" / f"{signal['run']['as_of']}.json"
    )
    if canonical_json(signal) != canonical_json(docs_signal):
        raise ContractError("docs/data/latest.json diverges from signals/latest.json")
    if canonical_json(signal) != canonical_json(archive_signal):
        raise ContractError("archive signal diverges from latest signal")
    docs_observation = load_json_strict(
        ROOT / "docs" / "data" / "observations" / "tsmc.json"
    )
    validate_document(docs_observation, SCHEMAS / "observed-facts.schema.json")
    validate_observed_facts_contract(docs_observation, sources)
    if canonical_json(observation) != canonical_json(docs_observation):
        raise ContractError("TSMC Pages observation diverges from source snapshot")
    run_id = signal["run"]["run_id"]
    year, month, _ = signal["run"]["as_of"].split("-")
    run_record = load_json_strict(
        ROOT / "agent-runs" / year / month / f"{run_id}.json"
    )
    validate_document(run_record, SCHEMAS / "agent-run.schema.json")
    validate_agent_run_contract(run_record)
    _validate_run_bindings(signal, run_record, "latest")

    immutable_signal = load_json_strict(
        ROOT / "signals" / "runs" / f"{run_id}.json"
    )
    docs_immutable_signal = load_json_strict(
        ROOT / "docs" / "data" / "runs" / f"{run_id}.json"
    )
    if canonical_json(immutable_signal) != canonical_json(signal):
        raise ContractError("immutable run signal diverges from latest signal")
    if canonical_json(docs_immutable_signal) != canonical_json(signal):
        raise ContractError("Pages immutable run signal diverges from latest signal")

    _validate_immutable_run_history(thresholds)


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
