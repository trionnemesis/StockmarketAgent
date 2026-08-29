from __future__ import annotations

import unittest

from src.pipeline import ROOT


class HumanReadableUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = (ROOT / "src" / "render" / "assets" / "app.js").read_text(
            encoding="utf-8"
        )

    def test_human_summary_answers_user_questions(self) -> None:
        for phrase in (
            "白話分析摘要",
            "目前沒有可用的即時買賣訊號",
            "約 3 個月的模擬看法",
            "官方資料日期",
            "資料狀態",
            "官方資料是否已納入模型",
            "模擬情境中較正面的因素",
            "較需要留意的因素",
        ):
            self.assertIn(phrase, self.app)

    def test_engineering_labels_have_plain_language_mappings(self) -> None:
        required_mappings = {
            "BUY": "模擬情境偏多",
            "HOLD": "模擬情境中性",
            "SELL": "模擬情境偏空",
            "NO_SIGNAL": "目前沒有可用的即時買賣訊號",
            "RESEARCH ONLY": "研究預覽",
            "research_fixture": "模擬研究資料",
            "uncalibrated": "尚未完成回測校準",
            "Risk Gate": "安全檢查",
            "official_observation": "官方市場資料",
        }
        for raw, human in required_mappings.items():
            self.assertIn(raw, self.app)
            self.assertIn(human, self.app)

    def test_model_components_are_explained_in_plain_chinese(self) -> None:
        for label in (
            "總體環境",
            "公司基本面",
            "估值合理性",
            "價格趨勢",
            "產業循環",
            "事件影響",
        ):
            self.assertIn(label, self.app)
        for label in ("偏正面", "中性", "偏負面"):
            self.assertIn(label, self.app)

    def test_raw_values_remain_available_for_maintainers(self) -> None:
        self.assertIn("data-technical-raw", self.app)
        self.assertIn("查看維護者用的原始技術值", self.app)
        self.assertIn("data-*", self.app)
        self.assertIn("dataset.score", self.app)
        self.assertIn("dataset.confidence", self.app)

    def test_existing_filter_interaction_is_preserved(self) -> None:
        for marker in (
            "[data-filter-form]",
            "[data-instrument]",
            "data-result-count",
            'form.addEventListener("input", applyFilters)',
            'form.addEventListener("change", applyFilters)',
        ):
            self.assertIn(marker, self.app)


if __name__ == "__main__":
    unittest.main()
