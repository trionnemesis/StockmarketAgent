from __future__ import annotations

import copy
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from src.pipeline import ROOT, build_outputs, build_signal, load_inputs, load_tw_observations
from src.validation.contracts import canonical_json, load_json_strict
from src.render.markdown import render_report
from src.render.site import render_history, render_home


class LinkCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        values = dict(attrs)
        if tag in {"a", "link"} and values.get("href"):
            self.links.append(values["href"] or "")
        if tag == "script" and values.get("src"):
            self.links.append(values["src"] or "")


class GeneratedArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        universe, approvals, model, fixture, themes, benchmarks, sources, review = load_inputs()
        cls.review = review
        cls.sources = sources
        cls.observations = load_tw_observations(universe, sources)
        cls.signal = build_signal(universe, approvals, model, fixture, themes, benchmarks, sources, review)
        cls.outputs, cls.run_record = build_outputs(cls.signal, sources, review)

    def test_committed_generated_files_are_current(self) -> None:
        stale = [
            str(path.relative_to(ROOT))
            for path, expected in self.outputs.items()
            if not path.exists() or path.read_bytes() != expected
        ]
        self.assertEqual(stale, [])

    def test_markdown_and_html_derive_from_same_instruments(self) -> None:
        report = render_report(self.signal)
        home = self.outputs[ROOT / "docs" / "index.html"].decode("utf-8")
        for item in self.signal["instruments"]:
            self.assertIn(item["symbol"], report)
            self.assertIn(item["symbol"], home)
        for stance, count in self.signal["summary"]["stances"].items():
            self.assertIn(f"| {stance} | {count} |", report)
            self.assertIn(
                f'data-summary-horizon="3M" data-stance="{stance}" data-count="{count}"',
                home,
            )
        self.assertIn(
            f"{self.signal['summary']['tracked_count']} 個候選標的", home
        )

    def test_three_month_stance_summary_matches_instrument_json(self) -> None:
        expected = {stance: 0 for stance in ("BUY", "HOLD", "SELL", "NO_SIGNAL")}
        for item in self.signal["instruments"]:
            horizon = next(
                entry for entry in item["horizons"] if entry["horizon"] == "3M"
            )
            expected[horizon["stance"]] += 1
        self.assertEqual(self.signal["summary"]["stances"], expected)

        for country in ("TW", "JP", "US"):
            market_page = self.outputs[
                ROOT / "docs" / "markets" / f"{country.lower()}.html"
            ].decode("utf-8")
            market_counts = {stance: 0 for stance in expected}
            for item in self.signal["instruments"]:
                if item["country"] != country:
                    continue
                horizon = next(
                    entry
                    for entry in item["horizons"]
                    if entry["horizon"] == "3M"
                )
                market_counts[horizon["stance"]] += 1
            for stance, count in market_counts.items():
                self.assertIn(
                    f'data-market-horizon="3M" data-stance="{stance}" data-count="{count}"',
                    market_page,
                )

    def test_instrument_html_and_markdown_expose_all_research_values(self) -> None:
        report = render_report(self.signal)
        component_labels = {
            "macro": "總體",
            "fundamental": "基本面",
            "valuation": "估值",
            "technical": "技術",
            "cycle": "循環",
            "events": "事件",
        }
        for item in self.signal["instruments"]:
            page = self.outputs[
                ROOT / "docs" / "instruments" / f"{item['slug']}.html"
            ].decode("utf-8")
            for horizon in item["horizons"]:
                score = self._display_score(horizon["score"])
                self.assertIn(
                    f'data-horizon="{horizon["horizon"]}" data-score="{score}" '
                    f'data-stance="{horizon["stance"]}" data-confidence="{horizon["confidence"]}" '
                    f'data-calibration="{horizon["calibration_status"]}"',
                    page,
                )
                self.assertIn(
                    f"{horizon['stance']} / score {score} / confidence "
                    f"{horizon['confidence']} / {horizon['calibration_status']}",
                    report,
                )
                for field in (
                    "supporting_evidence",
                    "contrary_evidence",
                    "invalidation_conditions",
                ):
                    for statement in horizon[field]:
                        self.assertIn(statement, page)
                        self.assertIn(statement, report)
            for component_name, component in item["components"].items():
                score = self._display_score(component["score"])
                self.assertIn(
                    f'data-component="{component_name}" data-score="{score}" '
                    f'data-confidence="{component["confidence"]}" data-status="{component["status"]}"',
                    page,
                )
                self.assertIn(
                    f"| {item['symbol']} | {component_labels[component_name]} | "
                    f"{score} | {component['confidence']} | {component['status']} |",
                    report,
                )
            for required_flag in ("RESEARCH_FIXTURE", "MODEL_UNCALIBRATED"):
                self.assertTrue(
                    any(
                        required_flag in horizon["risk_flags"]
                        for horizon in item["horizons"]
                    )
                )
                self.assertIn(required_flag, page)
                self.assertIn(required_flag, report)

    @staticmethod
    def _display_score(value: object) -> str:
        if value is None:
            return "—"
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def test_synthetic_research_warning_is_visible_site_wide(self) -> None:
        html_outputs = {
            path: payload.decode("utf-8")
            for path, payload in self.outputs.items()
            if path.suffix == ".html"
        }
        self.assertGreater(len(html_outputs), 30)
        for page, html in html_outputs.items():
            self.assertIn("研究模擬資料", html, str(page.relative_to(ROOT)))
            self.assertIn("另行標示的官方觀測事實不會進入訊號", html, str(page.relative_to(ROOT)))
        report = render_report(self.signal)
        self.assertIn("研究模擬資料", report)
        self.assertIn("未校準研究態度", report)

    def test_all_taiwan_pages_expose_official_evidence_without_changing_signal(self) -> None:
        for instrument_id, observation in self.observations.items():
            page = self.outputs[
                ROOT / "docs" / "instruments" / f"{observation['slug']}.html"
            ].decode("utf-8")
            self.assertIn(
                f'data-observed-snapshot="{observation["as_of"]}"', page
            )
            for fact_name in ("close", "volume"):
                self.assertIn(f'data-observed-fact="{fact_name}"', page)
            for evidence_name in (
                "supporting_evidence",
                "contrary_evidence",
                "invalidation_conditions",
            ):
                self.assertIn(f'data-official-evidence="{evidence_name}"', page)
                for statement in observation["evidence_assessment"][evidence_name]:
                    self.assertIn(statement, page)
            if observation["asset_type"] == "stock":
                self.assertIn('data-observed-fact="valuation"', page)
                self.assertIn('data-observed-fact="monthly-revenue"', page)
                self.assertNotIn('data-observed-fact="tracking-index"', page)
            else:
                self.assertIn('data-observed-fact="tracking-index"', page)
                self.assertNotIn('data-observed-fact="valuation"', page)
                self.assertIn("不適用；未以個股基本面硬比", page)
            self.assertIn("not used in signal", page)
            self.assertIn("HTML scraping：false", page)
            docs_observation = load_json_strict(
                ROOT
                / "docs"
                / "data"
                / "observations"
                / f"{observation['slug']}.json"
            )
            self.assertEqual(
                canonical_json(docs_observation), canonical_json(observation)
            )
            signal_item = next(
                item for item in self.signal["instruments"]
                if item["instrument_id"] == instrument_id
            )
            self.assertTrue(
                all(
                    provenance["source_type"] == "synthetic_research_fixture"
                    for provenance in signal_item["provenance"]
                )
            )

        tw_market = self.outputs[ROOT / "docs" / "markets" / "tw.html"].decode(
            "utf-8"
        )
        self.assertIn('data-tw-observation-matrix="10"', tw_market)
        self.assertEqual(tw_market.count('data-observation-matrix="'), 10)
        for observation in self.observations.values():
            self.assertIn(
                f'data-observation-matrix="{observation["symbol"]}"', tw_market
            )
        self.assertIn("支持證據", tw_market)
        self.assertIn("反向證據", tw_market)
        self.assertIn("失效條件", tw_market)

        alphabet = self.outputs[
            ROOT / "docs" / "instruments" / "alphabet.html"
        ].decode("utf-8")
        self.assertNotIn("data-observed-snapshot", alphabet)

    def test_all_internal_site_links_resolve(self) -> None:
        docs_root = (ROOT / "docs").resolve()
        broken: list[str] = []
        for page in sorted(docs_root.rglob("*.html")):
            parser = LinkCollector()
            parser.feed(page.read_text(encoding="utf-8"))
            for link in parser.links:
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or link.startswith(("#", "mailto:")):
                    continue
                relative = unquote(parsed.path)
                if not relative:
                    continue
                target = (page.parent / relative).resolve()
                if docs_root not in target.parents and target != docs_root:
                    broken.append(f"{page.relative_to(docs_root)} -> outside:{link}")
                elif not target.exists():
                    broken.append(f"{page.relative_to(docs_root)} -> {link}")
        self.assertEqual(broken, [])

    def test_social_metadata_is_record_aware(self) -> None:
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        detail = next((ROOT / "docs" / "instruments").glob("*.html")).read_text(
            encoding="utf-8"
        )
        self.assertIn('property="og:image"', home)
        self.assertIn("assets/og.png", home)
        self.assertNotIn('property="og:image"', detail)
        self.assertIn('name="twitter:card" content="summary"', detail)

    def test_static_site_has_accessibility_and_mobile_contracts(self) -> None:
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "docs" / "assets" / "css" / "site.css").read_text(
            encoding="utf-8"
        )
        self.assertIn('aria-live="polite"', home)
        self.assertIn("<noscript>", home)
        self.assertIn(":focus-visible", css)
        self.assertIn("@media (max-width: 680px)", css)
        self.assertIn("overflow-x: auto", css)

    def test_generated_html_has_no_embedded_base64_images(self) -> None:
        offenders = [
            str(path.relative_to(ROOT))
            for path in (ROOT / "docs").rglob("*.html")
            if "data:image/" in path.read_text(encoding="utf-8").lower()
        ]
        self.assertEqual(offenders, [])

    def test_no_secret_shaped_values_in_repository_text(self) -> None:
        patterns = [
            re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
            re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
            re.compile(r"glpat-[A-Za-z0-9_-]{20,}"),
            re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
            re.compile(r"AKIA[0-9A-Z]{16}"),
            re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
            re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
            re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
        ]
        suffixes = {
            ".html",
            ".js",
            ".css",
            ".json",
            ".xml",
            ".txt",
            ".py",
            ".md",
            ".yml",
            ".yaml",
            ".toml",
        }
        findings: list[str] = []
        for path in ROOT.rglob("*"):
            if ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.is_file() and path.suffix in suffixes:
                text = path.read_text(encoding="utf-8")
                if any(pattern.search(text) for pattern in patterns):
                    findings.append(str(path.relative_to(ROOT)))
        self.assertEqual(findings, [])

    def test_archive_and_latest_are_both_present(self) -> None:
        as_of = self.signal["run"]["as_of"]
        self.assertTrue((ROOT / "signals" / "latest.json").exists())
        self.assertTrue((ROOT / "signals" / "archive" / f"{as_of}.json").exists())
        self.assertTrue((ROOT / "reports" / "latest.md").exists())
        self.assertTrue((ROOT / "reports" / "archive" / f"{as_of}.md").exists())
        run_id = self.signal["run"]["run_id"]
        self.assertTrue((ROOT / "signals" / "runs" / f"{run_id}.json").exists())
        self.assertTrue((ROOT / "reports" / "runs" / f"{run_id}.md").exists())

    def test_run_record_claims_only_immutable_outputs(self) -> None:
        self.assertTrue(all("/runs/" in path or path.startswith("agent-runs/") for path in self.run_record["outputs"]))

    def test_workflows_reject_untracked_generated_outputs(self) -> None:
        for workflow in ("quality.yml", "deploy-pages.yml"):
            content = (ROOT / ".github" / "workflows" / workflow).read_text(
                encoding="utf-8"
            )
            self.assertIn("git diff --exit-code", content)
            self.assertIn("git status --porcelain --untracked-files=all", content)

    def test_review_and_source_pages_are_human_visible(self) -> None:
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        review = (ROOT / "docs" / "universe-review.html").read_text(encoding="utf-8")
        sources = (ROOT / "docs" / "source-feasibility.html").read_text(encoding="utf-8")
        self.assertIn("部署版本可閱讀的查證資料", home)
        self.assertIn(
            f">{len(self.review['instruments'])}</strong><small>全部維持 proposed",
            home,
        )
        self.assertIn(
            f">{len(self.sources['sources'])}</strong><small>含授權與 Pages policy",
            home,
        )
        limited_symbols = "、".join(
            item["symbol"]
            for item in self.review["instruments"]
            if item["history"]["live_age_status"] == "limited"
        ) or "無"
        self.assertIn(f"<small>{limited_symbols}</small>", home)
        self.assertIn("href=\"universe-review.html\"", home)
        self.assertIn("href=\"source-feasibility.html\"", home)
        self.assertIn(self.review["evidence_as_of"], review)
        self.assertIn(self.review["instruments"][0]["selection_rationale"], review)
        self.assertIn(self.sources["sources"][0]["source_id"], sources)

    def test_home_handles_zero_limited_history_instruments(self) -> None:
        review = copy.deepcopy(self.review)
        for item in review["instruments"]:
            item["history"]["live_age_status"] = "sufficient"
        home = render_home(self.signal, review, self.sources)
        self.assertIn(
            "<span>短 live history</span><strong>0</strong><small>無</small>",
            home,
        )

    def test_history_renderer_enumerates_dated_archives(self) -> None:
        older = {
            **self.signal,
            "run": {
                **self.signal["run"],
                "as_of": "2026-08-26",
                "run_id": "20260826T120000Z-fixture-history",
            },
        }
        page = render_history([self.signal, older])
        self.assertIn("data/archive/2026-08-27.json", page)
        self.assertIn("data/archive/2026-08-26.json", page)
        self.assertEqual(page.count("<tbody>"), 1)
