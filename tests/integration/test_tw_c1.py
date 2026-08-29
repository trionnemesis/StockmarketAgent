from __future__ import annotations

import re
import unittest

from src.ingestion.twse_archive import load_and_validate_store
from src.pipeline import ROOT, build_outputs, build_signal, load_inputs


class TaiwanC1PageBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        universe, approvals, model, fixture, themes, benchmarks, sources, review = load_inputs()
        cls.sources = sources
        cls.review = review
        cls.signal = build_signal(
            universe,
            approvals,
            model,
            fixture,
            themes,
            benchmarks,
            sources,
            review,
        )
        cls.catalog, cls.entries = load_and_validate_store(universe, sources)
        cls.outputs, _ = build_outputs(
            cls.signal,
            sources,
            review,
            catalog=cls.catalog,
            archive_entries=cls.entries,
        )

    def test_pages_publish_catalog_and_append_only_archive(self) -> None:
        catalog_path = ROOT / "docs" / "data" / "observations" / "catalog.json"
        self.assertIn(catalog_path, self.outputs)
        for source_path in self.entries:
            relative = source_path.relative_to(ROOT / "data" / "observations" / "twse")
            self.assertIn(
                ROOT / "docs" / "data" / "observations" / relative,
                self.outputs,
            )

    def test_taiwan_pages_expose_source_freshness_and_zero_model_coverage(self) -> None:
        tw_page = self.outputs[ROOT / "docs" / "markets" / "tw.html"].decode("utf-8")
        self.assertEqual(tw_page.count('data-source-kind="official_observation"'), 10)
        self.assertEqual(tw_page.count('data-model-input-coverage="0"'), 10)
        for status in self.catalog["instruments"]:
            page = self.outputs[
                ROOT / "docs" / "instruments" / f"{status['slug']}.html"
            ].decode("utf-8")
            self.assertIn('data-source-kind="official_observation"', page)
            self.assertIn(
                f'data-official-as-of="{status["official_as_of"]}"', page
            )
            self.assertIn(
                f'data-observation-freshness="{status["freshness"]["freshness"]}"',
                page,
            )
            self.assertIn('data-model-input-coverage="0"', page)
            self.assertIn("官方觀測納入模型：0", page)
            self.assertIn("NO LIVE SIGNAL", page)

    def test_pages_do_not_render_unqualified_directional_badges(self) -> None:
        pattern = re.compile(r">\s*(BUY|SELL)\s*</span>")
        for path, payload in self.outputs.items():
            if path.suffix != ".html":
                continue
            html = payload.decode("utf-8")
            self.assertIsNone(pattern.search(html), str(path.relative_to(ROOT)))
        tsmc = self.outputs[
            ROOT / "docs" / "instruments" / "tsmc.html"
        ].decode("utf-8")
        self.assertIn("SYNTHETIC BUY", tsmc)


if __name__ == "__main__":
    unittest.main()
