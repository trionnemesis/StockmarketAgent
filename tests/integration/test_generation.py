from __future__ import annotations

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from src.pipeline import ROOT, build_outputs, build_signal, load_inputs
from src.render.markdown import render_report
from src.render.site import render_history


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
        home = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        for item in self.signal["instruments"]:
            self.assertIn(item["symbol"], report)
            self.assertIn(item["symbol"], home)
        self.assertIn("NO_SIGNAL | 30", report)
        self.assertIn("30 個候選標的", home)

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
        self.assertIn("href=\"universe-review.html\"", home)
        self.assertIn("href=\"source-feasibility.html\"", home)
        self.assertIn(self.review["evidence_as_of"], review)
        self.assertIn(self.review["instruments"][0]["selection_rationale"], review)
        self.assertIn(self.sources["sources"][0]["source_id"], sources)

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
