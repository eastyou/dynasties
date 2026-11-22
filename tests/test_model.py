"""数据模型测试：目录、查询、年份定位、年代格式与题目生成。"""

from __future__ import annotations

import dataclasses
import unittest
from typing import Dict, List, Set

from dynasties.model import (
    Dynasty,
    all_dynasties,
    at_year,
    find_dynasty,
    format_year,
    format_years,
    match_items,
    ordering_items,
    quiz_items,
    span,
)


class CatalogTest(unittest.TestCase):
    """内置朝代目录的完整性与自洽性。"""

    def test_returns_list(self) -> None:
        self.assertIsInstance(all_dynasties(), list)

    def test_has_nineteen_entries(self) -> None:
        self.assertEqual(len(all_dynasties()), 19)

    def test_returns_a_copy(self) -> None:
        items = all_dynasties()
        items.pop()
        self.assertEqual(len(all_dynasties()), 19)

    def test_ordered_by_start_year(self) -> None:
        years = [item.start for item in all_dynasties()]
        self.assertEqual(years, sorted(years))

    def test_intervals_do_not_overlap(self) -> None:
        items = all_dynasties()
        for previous, current in zip(items, items[1:]):
            self.assertLessEqual(previous.end, current.start)

    def test_start_is_not_after_end(self) -> None:
        for item in all_dynasties():
            self.assertLessEqual(item.start, item.end, item.name)

    def test_names_are_unique(self) -> None:
        names = [item.name for item in all_dynasties()]
        self.assertEqual(len(names), len(set(names)))

    def test_required_names_present(self) -> None:
        names = [item.name for item in all_dynasties()]
        required = [
            "夏",
            "商",
            "西周",
            "东周",
            "秦",
            "西汉",
            "东汉",
            "三国",
            "西晋",
            "东晋",
            "南北朝",
            "隋",
            "唐",
            "五代十国",
            "北宋",
            "南宋",
            "元",
            "明",
            "清",
        ]
        for name in required:
            self.assertIn(name, names)

    def test_fields_are_non_empty(self) -> None:
        for item in all_dynasties():
            self.assertTrue(item.name.strip())
            self.assertTrue(item.capital.strip())
            self.assertTrue(item.founder.strip())
            self.assertTrue(item.achievement.strip())

    def test_aliases_are_string_tuples(self) -> None:
        for item in all_dynasties():
            self.assertIsInstance(item.aliases, tuple)
            for alias in item.aliases:
                self.assertIsInstance(alias, str)
                self.assertTrue(alias.strip())

    def test_dynasty_is_frozen(self) -> None:
        item = all_dynasties()[0]
        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.name = "篡改"  # type: ignore[misc]

    def test_first_and_last(self) -> None:
        items = all_dynasties()
        self.assertEqual(items[0].name, "夏")
        self.assertEqual(items[-1].name, "清")


class DynastyValidationTest(unittest.TestCase):
    """Dynasty 构造参数校验。"""

    def _make(self, **overrides: object) -> Dynasty:
        values: Dict[str, object] = {
            "name": "测试",
            "start": 1,
            "end": 2,
            "capital": "某地",
            "founder": "某人",
            "achievement": "测试用。",
            "aliases": ("测试朝",),
        }
        values.update(overrides)
        return Dynasty(**values)  # type: ignore[arg-type]

    def test_reversed_years_raise(self) -> None:
        with self.assertRaises(ValueError):
            self._make(start=100, end=50)

    def test_equal_years_allowed(self) -> None:
        item = self._make(start=5, end=5)
        self.assertEqual(item.start, item.end)

    def test_bool_start_raises(self) -> None:
        with self.assertRaises(TypeError):
            self._make(start=True)

    def test_float_end_raises(self) -> None:
        with self.assertRaises(TypeError):
            self._make(end=2.5)

    def test_empty_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            self._make(name="   ")

    def test_empty_capital_raises(self) -> None:
        with self.assertRaises(ValueError):
            self._make(capital="")

    def test_non_tuple_aliases_raise(self) -> None:
        with self.assertRaises(TypeError):
            self._make(aliases="测试朝")

    def test_non_string_alias_raises(self) -> None:
        with self.assertRaises(TypeError):
            self._make(aliases=("测试朝", 1))

    def test_empty_alias_raises(self) -> None:
        with self.assertRaises(ValueError):
            self._make(aliases=("  ",))

    def test_alias_equal_to_name_raises(self) -> None:
        with self.assertRaises(ValueError):
            self._make(aliases=("测试",))

    def test_empty_aliases_allowed(self) -> None:
        item = self._make(aliases=())
        self.assertEqual(item.aliases, ())


class FindDynastyTest(unittest.TestCase):
    """按名称与别名查找。"""

    def test_find_by_name(self) -> None:
        self.assertEqual(find_dynasty("唐").founder, "李渊")

    def test_find_by_alias(self) -> None:
        self.assertEqual(find_dynasty("大唐").name, "唐")
        self.assertEqual(find_dynasty("前汉").name, "西汉")

    def test_strips_spaces(self) -> None:
        self.assertEqual(find_dynasty("  唐  ").name, "唐")
        self.assertEqual(find_dynasty("五 代").name, "五代十国")

    def test_unknown_raises(self) -> None:
        with self.assertRaises(ValueError) as context:
            find_dynasty("玛雅")
        self.assertIn("未知朝代", str(context.exception))

    def test_empty_raises(self) -> None:
        with self.assertRaises(ValueError):
            find_dynasty("   ")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            find_dynasty(None)  # type: ignore[arg-type]

    def test_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            find_dynasty(True)  # type: ignore[arg-type]


class AtYearTest(unittest.TestCase):
    """年份定位。"""

    def test_tang_at_618(self) -> None:
        self.assertEqual(at_year(618).name, "唐")

    def test_northern_song_at_1000(self) -> None:
        self.assertEqual(at_year(1000).name, "北宋")

    def test_qin_at_negative_year(self) -> None:
        self.assertEqual(at_year(-221).name, "秦")

    def test_western_zhou_at_negative_year(self) -> None:
        self.assertEqual(at_year(-1000).name, "西周")

    def test_southern_and_northern_at_500(self) -> None:
        self.assertEqual(at_year(500).name, "南北朝")

    def test_qing_at_1911(self) -> None:
        self.assertEqual(at_year(1911).name, "清")

    def test_transition_year_takes_new_dynasty(self) -> None:
        self.assertEqual(at_year(220).name, "三国")
        self.assertEqual(at_year(280).name, "西晋")
        self.assertEqual(at_year(907).name, "五代十国")
        self.assertEqual(at_year(960).name, "北宋")

    def test_gap_year_raises(self) -> None:
        with self.assertRaises(ValueError):
            at_year(-230)
        with self.assertRaises(ValueError):
            at_year(15)

    def test_before_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            at_year(-2001)

    def test_after_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            at_year(2101)

    def test_non_int_raises(self) -> None:
        with self.assertRaises(TypeError):
            at_year("1000")  # type: ignore[arg-type]

    def test_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            at_year(False)  # type: ignore[arg-type]


class SpanTest(unittest.TestCase):
    """持续时间。"""

    def test_tang_span(self) -> None:
        self.assertEqual(span("唐"), 290)

    def test_qin_span(self) -> None:
        self.assertEqual(span("秦"), 15)

    def test_xia_span(self) -> None:
        self.assertEqual(span("夏"), 471)

    def test_qing_span(self) -> None:
        self.assertEqual(span("清"), 269)

    def test_alias_works(self) -> None:
        self.assertEqual(span("大唐"), 290)

    def test_unknown_raises(self) -> None:
        with self.assertRaises(ValueError):
            span("不存在的朝代")

    def test_non_string_raises(self) -> None:
        with self.assertRaises(TypeError):
            span([])  # type: ignore[arg-type]


class FormatYearTest(unittest.TestCase):
    """单个年份与年代区间格式化。"""

    def test_bc_year(self) -> None:
        self.assertEqual(format_year(-2070), "公元前 2070 年")

    def test_ad_year(self) -> None:
        self.assertEqual(format_year(618), "公元 618 年")

    def test_bool_raises(self) -> None:
        with self.assertRaises(TypeError):
            format_year(True)  # type: ignore[arg-type]

    def test_float_raises(self) -> None:
        with self.assertRaises(TypeError):
            format_year(1.5)  # type: ignore[arg-type]

    def test_bc_range(self) -> None:
        self.assertEqual(
            format_years(-221, -207),
            "公元前 221 年 — 公元前 207 年",
        )

    def test_ad_range(self) -> None:
        self.assertEqual(format_years(618, 907), "618 年 — 907 年")

    def test_crossing_range(self) -> None:
        self.assertEqual(
            format_years(-202, 8),
            "公元前 202 年 — 公元 8 年",
        )

    def test_single_year_range(self) -> None:
        self.assertEqual(format_years(618, 618), "618 年 — 618 年")

    def test_reversed_range_raises(self) -> None:
        with self.assertRaises(ValueError):
            format_years(907, 618)

    def test_bool_range_raises(self) -> None:
        with self.assertRaises(TypeError):
            format_years(False, 10)  # type: ignore[arg-type]


class QuizTest(unittest.TestCase):
    """四选一测验生成。"""

    def test_count_matches(self) -> None:
        self.assertEqual(len(quiz_items(10, seed=5)), 10)

    def test_minimum_count(self) -> None:
        self.assertEqual(len(quiz_items(1)), 1)

    def test_maximum_count(self) -> None:
        self.assertEqual(len(quiz_items(40, seed=1)), 40)

    def test_zero_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            quiz_items(0)

    def test_too_large_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            quiz_items(41)

    def test_bool_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(True)  # type: ignore[arg-type]

    def test_float_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(3.0)  # type: ignore[arg-type]

    def test_string_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items("3")  # type: ignore[arg-type]

    def test_bool_seed_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(2, seed=True)

    def test_float_seed_raises(self) -> None:
        with self.assertRaises(TypeError):
            quiz_items(2, seed=1.5)

    def test_deterministic_with_seed(self) -> None:
        self.assertEqual(quiz_items(8, seed=7), quiz_items(8, seed=7))

    def test_options_are_four_unique_strings(self) -> None:
        for item in quiz_items(20, seed=11):
            options = item["options"]
            self.assertIsInstance(options, list)
            assert isinstance(options, list)
            self.assertEqual(len(options), 4)
            self.assertEqual(len(set(str(option) for option in options)), 4)

    def test_answer_index_matches_answer(self) -> None:
        for item in quiz_items(20, seed=13):
            options = item["options"]
            index = item["answer_index"]
            self.assertIsInstance(index, int)
            assert isinstance(options, list)
            assert isinstance(index, int)
            self.assertGreaterEqual(index, 0)
            self.assertLess(index, len(options))
            self.assertEqual(item["answer"], options[index])

    def test_covers_all_question_types(self) -> None:
        types = {item["type"] for item in quiz_items(40, seed=2026)}
        self.assertEqual(types, {"capital", "founder", "era"})

    def test_explanations_non_empty(self) -> None:
        for item in quiz_items(12, seed=17):
            self.assertIsInstance(item["explanation"], str)
            self.assertTrue(str(item["explanation"]).strip())

    def test_indexes_are_sequential(self) -> None:
        items = quiz_items(6, seed=29)
        self.assertEqual([item["index"] for item in items], [1, 2, 3, 4, 5, 6])


class OrderingTest(unittest.TestCase):
    """朝代排序题生成。"""

    def test_count_matches(self) -> None:
        self.assertEqual(len(ordering_items(5, seed=2)), 5)

    def test_minimum_count(self) -> None:
        self.assertEqual(len(ordering_items(1, seed=2)), 1)

    def test_maximum_count(self) -> None:
        self.assertEqual(len(ordering_items(40, seed=2)), 40)

    def test_zero_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            ordering_items(0)

    def test_too_large_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            ordering_items(41)

    def test_bool_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            ordering_items(False)  # type: ignore[arg-type]

    def test_float_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            ordering_items(2.5)  # type: ignore[arg-type]

    def test_seed_type_error(self) -> None:
        with self.assertRaises(TypeError):
            ordering_items(2, seed=1.5)

    def test_four_or_five_names(self) -> None:
        for item in ordering_items(4, seed=4):
            shuffled = item["shuffled"]
            answer = item["answer"]
            assert isinstance(shuffled, list)
            assert isinstance(answer, list)
            self.assertIn(len(shuffled), (4, 5))
            self.assertEqual(len(shuffled), len(answer))

    def test_answer_is_chronological(self) -> None:
        canonical = [dynasty.name for dynasty in all_dynasties()]
        for item in ordering_items(5, seed=6):
            answer = item["answer"]
            assert isinstance(answer, list)
            positions = [canonical.index(str(name)) for name in answer]
            self.assertEqual(positions, sorted(positions))

    def test_shuffled_matches_answer_set(self) -> None:
        for item in ordering_items(5, seed=8):
            shuffled = item["shuffled"]
            answer = item["answer"]
            assert isinstance(shuffled, list)
            assert isinstance(answer, list)
            self.assertEqual(sorted(map(str, shuffled)), sorted(map(str, answer)))

    def test_shuffled_is_not_answer(self) -> None:
        for item in ordering_items(10, seed=10):
            self.assertNotEqual(item["shuffled"], item["answer"])

    def test_deterministic_with_seed(self) -> None:
        self.assertEqual(ordering_items(3, seed=99), ordering_items(3, seed=99))

    def test_indexes_are_sequential(self) -> None:
        items = ordering_items(3, seed=12)
        self.assertEqual([item["index"] for item in items], [1, 2, 3])


class MatchTest(unittest.TestCase):
    """朝代—成就 / 都城配对题。"""

    def test_count_matches(self) -> None:
        self.assertEqual(len(match_items(6, seed=3)), 6)

    def test_minimum_count(self) -> None:
        self.assertEqual(len(match_items(1, seed=3)), 1)

    def test_maximum_count(self) -> None:
        self.assertEqual(len(match_items(18, seed=3)), 18)

    def test_zero_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            match_items(0)

    def test_too_large_count_raises(self) -> None:
        with self.assertRaises(ValueError):
            match_items(19)

    def test_bool_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            match_items(True)  # type: ignore[arg-type]

    def test_seed_type_error(self) -> None:
        with self.assertRaises(TypeError):
            match_items(2, seed="x")  # type: ignore[arg-type]

    def test_pairs_are_unique_tuples(self) -> None:
        pairs = match_items(10, seed=5)
        self.assertIsInstance(pairs, list)
        names: List[str] = []
        values: Set[str] = set()
        for pair in pairs:
            self.assertIsInstance(pair, tuple)
            self.assertEqual(len(pair), 2)
            name, value = pair
            self.assertIsInstance(name, str)
            self.assertIsInstance(value, str)
            self.assertTrue(name.strip())
            self.assertTrue(value.strip())
            names.append(name)
            values.add(value)
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(len(values), len(pairs))

    def test_names_are_known(self) -> None:
        known = {item.name for item in all_dynasties()}
        for name, _ in match_items(18, seed=9):
            self.assertIn(name, known)

    def test_deterministic_with_seed(self) -> None:
        self.assertEqual(match_items(5, seed=21), match_items(5, seed=21))


if __name__ == "__main__":
    unittest.main()
