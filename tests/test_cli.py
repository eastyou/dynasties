"""命令行测试：子命令输出、退出码、文件导出与错误处理。"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import List, Tuple

from dynasties.cli import main


def _invoke(argv: List[str]) -> Tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(argv)
    return code, out.getvalue(), err.getvalue()


class BasicCommandTest(unittest.TestCase):
    """帮助、版本与基础查询命令。"""

    def test_help_returns_zero(self) -> None:
        code, out, _ = _invoke(["--help"])
        self.assertEqual(code, 0)
        self.assertIn("usage: dynasties", out)
        self.assertIn("timeline", out)

    def test_version_returns_zero(self) -> None:
        code, out, _ = _invoke(["--version"])
        self.assertEqual(code, 0)
        self.assertIn("dynasties 0.1.0", out)

    def test_no_command_shows_help_and_returns_two(self) -> None:
        code, out, _ = _invoke([])
        self.assertEqual(code, 2)
        self.assertIn("usage: dynasties", out)

    def test_info_returns_details(self) -> None:
        code, out, _ = _invoke(["info", "唐"])
        self.assertEqual(code, 0)
        self.assertIn("名称：唐", out)
        self.assertIn("起止：618 年 — 907 年", out)
        self.assertIn("都城：长安（今陕西西安）", out)
        self.assertIn("开国君主：李渊", out)
        self.assertIn("持续时间：290 年", out)

    def test_info_accepts_alias(self) -> None:
        code, out, _ = _invoke(["info", "大唐"])
        self.assertEqual(code, 0)
        self.assertIn("名称：唐", out)

    def test_year_command(self) -> None:
        code, out, _ = _invoke(["year", "1000"])
        self.assertEqual(code, 0)
        self.assertIn("公元 1000 年：北宋", out)
        self.assertIn("东京开封府", out)

    def test_year_negative(self) -> None:
        code, out, _ = _invoke(["year", "-221"])
        self.assertEqual(code, 0)
        self.assertIn("公元前 221 年：秦", out)

    def test_span_command(self) -> None:
        code, out, _ = _invoke(["span", "唐"])
        self.assertEqual(code, 0)
        self.assertIn("唐：618 年 — 907 年", out)
        self.assertIn("共 290 年", out)

    def test_list_command(self) -> None:
        code, out, _ = _invoke(["list"])
        self.assertEqual(code, 0)
        self.assertIn("共 19 个朝代", out)
        self.assertIn("夏", out)
        self.assertIn("清", out)

    def test_list_has_header_plus_nineteen_lines(self) -> None:
        code, out, _ = _invoke(["list"])
        self.assertEqual(code, 0)
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertEqual(len(lines), 20)


class CliErrorTest(unittest.TestCase):
    """错误路径：未知朝代、越界年份与非法输出路径。"""

    def test_unknown_dynasty_returns_two(self) -> None:
        code, _, err = _invoke(["info", "玛雅"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)
        self.assertIn("未知朝代", err)

    def test_span_unknown_returns_two(self) -> None:
        code, _, err = _invoke(["span", "不存在的朝代"])
        self.assertEqual(code, 2)
        self.assertIn("未知朝代", err)

    def test_year_gap_returns_two(self) -> None:
        code, _, err = _invoke(["year", "-230"])
        self.assertEqual(code, 2)
        self.assertIn("没有对应的朝代", err)

    def test_year_before_range_returns_two(self) -> None:
        code, _, err = _invoke(["year", "-2001"])
        self.assertEqual(code, 2)
        self.assertIn("年份必须在", err)

    def test_year_after_range_returns_two(self) -> None:
        code, _, err = _invoke(["year", "2101"])
        self.assertEqual(code, 2)
        self.assertIn("年份必须在", err)

    def test_year_non_numeric_returns_two(self) -> None:
        code, _, _ = _invoke(["year", "abc"])
        self.assertEqual(code, 2)

    def test_quiz_count_zero_returns_two(self) -> None:
        code, _, err = _invoke(["quiz", "--count", "0"])
        self.assertEqual(code, 2)
        self.assertIn("题目数量必须在 1 到 40 之间", err)

    def test_quiz_count_too_large_returns_two(self) -> None:
        code, _, err = _invoke(["quiz", "--count", "41"])
        self.assertEqual(code, 2)
        self.assertIn("错误：", err)

    def test_ordering_count_too_large_returns_two(self) -> None:
        code, _, err = _invoke(["ordering", "--count", "41"])
        self.assertEqual(code, 2)
        self.assertIn("题目数量必须在 1 到 40 之间", err)

    def test_match_count_too_large_returns_two(self) -> None:
        code, _, err = _invoke(["match", "--count", "19"])
        self.assertEqual(code, 2)
        self.assertIn("配对数量必须在 1 到 18 之间", err)

    def test_empty_output_path_returns_two(self) -> None:
        code, _, err = _invoke(["timeline", "-o", ""])
        self.assertEqual(code, 2)
        self.assertIn("输出路径不能为空", err)

    def test_unwritable_output_path_returns_two(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            blocker = os.path.join(folder, "blocker")
            with open(blocker, "w", encoding="utf-8") as handle:
                handle.write("x")
            target = os.path.join(blocker, "out.html")
            code, _, err = _invoke(["timeline", "-o", target])
        self.assertEqual(code, 2)
        self.assertIn("无法写入文件", err)


class ExportCommandTest(unittest.TestCase):
    """文件导出命令与生成内容。"""

    def test_quiz_stdout_contains_answers(self) -> None:
        code, out, _ = _invoke(["quiz", "--count", "3", "--seed", "5"])
        self.assertEqual(code, 0)
        self.assertIn("参考答案与解析", out)
        self.assertIn("1.", out)

    def test_quiz_writes_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "quiz.html")
            code, out, _ = _invoke(
                ["quiz", "--count", "5", "--seed", "5", "-o", target]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % target, out)
            with open(target, encoding="utf-8") as handle:
                content = handle.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("中国朝代知识测验", content)
        self.assertIn("答案：", content)
        self.assertEqual(content.count('class="card"'), 5)

    def test_quiz_creates_missing_directory(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "nested", "quiz.html")
            code, out, _ = _invoke(["quiz", "--count", "2", "-o", target])
            self.assertEqual(code, 0)
            self.assertTrue(os.path.exists(target))
            self.assertIn("已生成：", out)

    def test_quiz_seed_reproducible_via_cli(self) -> None:
        _, first, _ = _invoke(["quiz", "--count", "6", "--seed", "42"])
        _, second, _ = _invoke(["quiz", "--count", "6", "--seed", "42"])
        self.assertEqual(first, second)

    def test_ordering_stdout_contains_answers(self) -> None:
        code, out, _ = _invoke(["ordering", "--count", "2", "--seed", "2"])
        self.assertEqual(code, 0)
        self.assertIn("参考答案与解析", out)
        self.assertIn("正确顺序", out)

    def test_ordering_writes_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "ordering.html")
            code, out, _ = _invoke(
                ["ordering", "--count", "4", "--seed", "2", "-o", target]
            )
            self.assertEqual(code, 0)
            self.assertIn("已生成：", out)
            with open(target, encoding="utf-8") as handle:
                content = handle.read()
        self.assertIn("中国朝代排序练习", content)
        self.assertEqual(content.count('class="card"'), 4)

    def test_match_stdout(self) -> None:
        code, out, _ = _invoke(["match", "--count", "4", "--seed", "2"])
        self.assertEqual(code, 0)
        self.assertIn("朝代配对练习（共 4 组）", out)
        self.assertIn("参考答案与解析", out)

    def test_match_writes_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "match.html")
            code, out, _ = _invoke(["match", "--count", "4", "--seed", "2", "-o", target])
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % target, out)
            with open(target, encoding="utf-8") as handle:
                content = handle.read()
        self.assertIn("中国朝代配对练习", content)
        self.assertIn("参考答案", content)

    def test_timeline_stdout(self) -> None:
        code, out, _ = _invoke(["timeline"])
        self.assertEqual(code, 0)
        self.assertIn("<svg", out)
        self.assertIn("</svg>", out)

    def test_timeline_writes_html_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = os.path.join(folder, "timeline.html")
            code, out, _ = _invoke(["timeline", "-o", target])
            self.assertEqual(code, 0)
            self.assertIn("已生成：%s" % target, out)
            with open(target, encoding="utf-8") as handle:
                content = handle.read()
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("A4", content)
        self.assertEqual(content.count('class="row"'), 19)


if __name__ == "__main__":
    unittest.main()
