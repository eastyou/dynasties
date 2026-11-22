"""HTML / SVG 渲染测试：结构、转义、打印样式与非法输入。"""

from __future__ import annotations

import unittest
from typing import Dict, List, Tuple

from dynasties.model import all_dynasties
from dynasties.render import (
    match_html,
    ordering_html,
    quiz_html,
    timeline_html,
    timeline_svg,
)


def _quiz_item(**overrides: object) -> Dict[str, object]:
    item: Dict[str, object] = {
        "index": 1,
        "type": "era",
        "question": "「商」的起止年代是？",
        "options": ["公元前 1600 年 — 公元前 1046 年", "618 年 — 907 年", "960 年 — 1127 年", "1368 年 — 1644 年"],
        "answer_index": 0,
        "answer": "公元前 1600 年 — 公元前 1046 年",
        "explanation": "商起于公元前 1600 年，止于公元前 1046 年。",
    }
    item.update(overrides)
    return item


def _ordering_item(**overrides: object) -> Dict[str, object]:
    item: Dict[str, object] = {
        "index": 1,
        "question": "请按时间先后排列以下 5 个朝代：",
        "shuffled": ["秦", "夏", "唐", "商", "明"],
        "answer": ["夏", "商", "秦", "唐", "明"],
        "explanation": "正确顺序：夏 → 商 → 秦 → 唐 → 明",
    }
    item.update(overrides)
    return item


def _pairs() -> List[Tuple[str, str]]:
    return [
        ("唐", "贞观之治与开元盛世"),
        ("秦", "统一文字与度量衡"),
        ("北宋", "活字印刷与纸币交子"),
    ]


class TimelineSvgTest(unittest.TestCase):
    """SVG 时间轴。"""

    def test_returns_svg_document(self) -> None:
        content = timeline_svg()
        self.assertIn("<svg", content)
        self.assertIn("</svg>", content)
        self.assertIn("viewBox=", content)

    def test_contains_all_dynasties(self) -> None:
        content = timeline_svg()
        for name in ("夏", "商", "唐", "北宋", "清"):
            self.assertIn(">%s<" % name, content)

    def test_one_block_per_dynasty(self) -> None:
        content = timeline_svg()
        self.assertEqual(content.count('rx="4"'), 19)

    def test_range_subset(self) -> None:
        content = timeline_svg(600, 1000)
        self.assertIn(">唐<", content)
        self.assertIn(">北宋<", content)
        self.assertNotIn(">夏<", content)

    def test_contains_axis_ticks(self) -> None:
        content = timeline_svg()
        self.assertIn("前2000", content)
        self.assertIn("1500", content)

    def test_no_dynasty_in_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            timeline_svg(2000, 2100)

    def test_reversed_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            timeline_svg(1912, -2100)

    def test_equal_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            timeline_svg(1000, 1000)

    def test_non_int_raises(self) -> None:
        with self.assertRaises(TypeError):
            timeline_svg("600", 1000)  # type: ignore[arg-type]

    def test_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            timeline_svg(False, 1000)


class TimelineHtmlTest(unittest.TestCase):
    """HTML 时间轴与明细表。"""

    def setUp(self) -> None:
        self.dynasties = all_dynasties()
        self.content = timeline_html(self.dynasties, "中国朝代时间轴")

    def test_contains_doctype_and_lang(self) -> None:
        self.assertIn("<!DOCTYPE html>", self.content)
        self.assertIn('lang="zh-CN"', self.content)

    def test_contains_print_styles(self) -> None:
        self.assertIn("@media print", self.content)
        self.assertIn("A4", self.content)
        self.assertIn("@page", self.content)

    def test_one_row_per_dynasty(self) -> None:
        self.assertEqual(self.content.count('class="row"'), 19)

    def test_table_has_all_rows(self) -> None:
        self.assertEqual(self.content.count("<tr>"), 20)

    def test_contains_dynasty_details(self) -> None:
        self.assertIn("长安（今陕西西安）", self.content)
        self.assertIn("李渊", self.content)
        self.assertIn("618 年 — 907 年", self.content)
        self.assertIn("公元前 221 年 — 公元前 207 年", self.content)

    def test_contains_aliases_and_achievement(self) -> None:
        self.assertIn("唐朝", self.content)
        self.assertIn("贞观之治与开元盛世", self.content)

    def test_escapes_title(self) -> None:
        content = timeline_html(self.dynasties, "<b>朝代</b>")
        self.assertIn("&lt;b&gt;朝代&lt;/b&gt;", content)
        self.assertNotIn("<b>朝代</b>", content)

    def test_accepts_tuple_input(self) -> None:
        content = timeline_html(tuple(self.dynasties[:3]), "小时间轴")
        self.assertIn("小时间轴", content)

    def test_empty_list_raises(self) -> None:
        with self.assertRaises(ValueError):
            timeline_html([], "标题")

    def test_non_sequence_raises(self) -> None:
        with self.assertRaises(TypeError):
            timeline_html("abc", "标题")  # type: ignore[arg-type]

    def test_invalid_element_raises(self) -> None:
        with self.assertRaises(TypeError):
            timeline_html([object()], "标题")  # type: ignore[list-item]

    def test_invalid_title_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            timeline_html(self.dynasties, 123)  # type: ignore[arg-type]

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            timeline_html(self.dynasties, "   ")


class QuizRenderTest(unittest.TestCase):
    """四选一测验页面。"""

    def test_default_hides_answers(self) -> None:
        content = quiz_html([_quiz_item()], "知识测验")
        self.assertIn("答案：____________", content)
        self.assertNotIn("商起于公元前 1600 年", content)

    def test_with_answers_shows_answer_and_explanation(self) -> None:
        content = quiz_html([_quiz_item()], "知识测验", with_answers=True)
        self.assertIn("答案：A.", content)
        self.assertIn("商起于公元前 1600 年", content)

    def test_renders_all_options(self) -> None:
        content = quiz_html([_quiz_item()], "知识测验")
        self.assertIn("618 年 — 907 年", content)
        self.assertIn("960 年 — 1127 年", content)

    def test_escapes_question_and_options(self) -> None:
        item = _quiz_item(
            question="<script>alert(1)</script>",
            options=["<i>甲</i>", "乙", "丙", "丁"],
            answer="<i>甲</i>",
        )
        content = quiz_html([item], "标题")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", content)
        self.assertIn("&lt;i&gt;甲&lt;/i&gt;", content)
        self.assertNotIn("<script>alert(1)</script>", content)

    def test_has_print_styles(self) -> None:
        content = quiz_html([_quiz_item()], "标题")
        self.assertIn("@media print", content)
        self.assertIn("A4", content)

    def test_empty_items_raises(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([], "标题")

    def test_non_sequence_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html("abc", "标题")  # type: ignore[arg-type]

    def test_non_dict_item_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html([1], "标题")  # type: ignore[list-item]

    def test_missing_field_raises(self) -> None:
        item = _quiz_item()
        del item["options"]
        with self.assertRaises(ValueError):
            quiz_html([item], "标题")

    def test_answer_index_out_of_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([_quiz_item(answer_index=9)], "标题")

    def test_answer_mismatch_raises(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([_quiz_item(answer="西周")], "标题")

    def test_with_answers_non_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_html([_quiz_item()], "标题", with_answers="yes")  # type: ignore[arg-type]

    def test_empty_explanation_raises(self) -> None:
        with self.assertRaises(ValueError):
            quiz_html([_quiz_item(explanation="  ")], "标题")

    def test_render_from_generator(self) -> None:
        from dynasties.model import quiz_items

        content = quiz_html(quiz_items(5, seed=3), "测验", with_answers=True)
        self.assertIn("参考答案", content)
        self.assertEqual(content.count('class="card"'), 5)


class OrderingRenderTest(unittest.TestCase):
    """排序练习页面。"""

    def test_default_hides_answer(self) -> None:
        content = ordering_html([_ordering_item()], "排序练习")
        self.assertIn("正确顺序：____________", content)
        self.assertNotIn("夏 → 商 → 秦 → 唐 → 明", content)

    def test_with_answers_shows_answer(self) -> None:
        content = ordering_html([_ordering_item()], "排序练习", with_answers=True)
        self.assertIn("正确顺序：夏 → 商 → 秦 → 唐 → 明", content)

    def test_renders_all_shuffled_names(self) -> None:
        content = ordering_html([_ordering_item()], "排序练习")
        for name in ("秦", "夏", "唐", "商", "明"):
            self.assertIn("<li>%s</li>" % name, content)

    def test_has_print_styles(self) -> None:
        content = ordering_html([_ordering_item()], "标题")
        self.assertIn("@media print", content)
        self.assertIn("A4", content)

    def test_empty_items_raises(self) -> None:
        with self.assertRaises(ValueError):
            ordering_html([], "标题")

    def test_missing_field_raises(self) -> None:
        item = _ordering_item()
        del item["answer"]
        with self.assertRaises(ValueError):
            ordering_html([item], "标题")

    def test_mismatched_lengths_raise(self) -> None:
        with self.assertRaises(ValueError):
            ordering_html([_ordering_item(answer=["夏", "商"])], "标题")

    def test_with_answers_non_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            ordering_html([_ordering_item()], "标题", with_answers=1)  # type: ignore[arg-type]

    def test_empty_shuffled_raises(self) -> None:
        with self.assertRaises(ValueError):
            ordering_html([_ordering_item(shuffled=[], answer=[])], "标题")

    def test_render_from_generator(self) -> None:
        from dynasties.model import ordering_items

        content = ordering_html(ordering_items(2, seed=3), "排序")
        self.assertEqual(content.count('class="card"'), 2)


class MatchRenderTest(unittest.TestCase):
    """配对练习页面。"""

    def test_renders_names_and_values(self) -> None:
        content = match_html(_pairs(), "配对练习")
        self.assertIn("唐", content)
        self.assertIn("贞观之治与开元盛世", content)
        self.assertIn("统一文字与度量衡", content)

    def test_contains_answer_key(self) -> None:
        content = match_html(_pairs(), "配对练习")
        self.assertIn("参考答案", content)
        self.assertIn("1. 唐 — ", content)

    def test_has_print_styles(self) -> None:
        content = match_html(_pairs(), "标题")
        self.assertIn("@media print", content)
        self.assertIn("A4", content)

    def test_escapes_text(self) -> None:
        content = match_html([("<b>唐</b>", "<i>成就</i>")], "标题")
        self.assertIn("&lt;b&gt;唐&lt;/b&gt;", content)
        self.assertIn("&lt;i&gt;成就&lt;/i&gt;", content)
        self.assertNotIn("<b>唐</b>", content)

    def test_empty_pairs_raises(self) -> None:
        with self.assertRaises(ValueError):
            match_html([], "标题")

    def test_non_sequence_raises(self) -> None:
        with self.assertRaises(TypeError):
            match_html("abc", "标题")  # type: ignore[arg-type]

    def test_invalid_pair_type_raises(self) -> None:
        with self.assertRaises(TypeError):
            match_html([["唐", "成就"]], "标题")  # type: ignore[list-item]

    def test_pair_length_raises(self) -> None:
        with self.assertRaises(TypeError):
            match_html([("唐",)], "标题")  # type: ignore[list-item]

    def test_duplicate_values_raise(self) -> None:
        with self.assertRaises(ValueError):
            match_html([("唐", "长安"), ("西汉", "长安")], "标题")

    def test_empty_title_raises(self) -> None:
        with self.assertRaises(ValueError):
            match_html(_pairs(), "  ")

    def test_render_from_generator(self) -> None:
        from dynasties.model import match_items

        content = match_html(match_items(4, seed=2), "配对")
        self.assertEqual(content.count("<li>"), 12)


if __name__ == "__main__":
    unittest.main()
