"""命令行入口：朝代查询、年代定位、题目生成与时间轴导出。"""

from __future__ import annotations

import argparse
import os
import sys
from typing import Dict, Optional, Sequence, Tuple

from . import __version__
from .model import (
    Dynasty,
    all_dynasties,
    at_year,
    find_dynasty,
    format_year,
    format_years,
    match_items,
    ordering_items,
    quiz_items,
)
from .model import span as dynasty_span
from .render import (
    match_html,
    ordering_html,
    quiz_html,
    timeline_html,
    timeline_svg,
)

__all__ = ["main"]


def _ensure_utf8_console() -> None:
    """尽力把标准输出与标准错误切换为 UTF-8，失败时静默跳过。"""
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass


def _int_arg(text: str) -> int:
    """把命令行文本解析为整数，失败时抛出中文参数错误。"""
    try:
        return int(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是整数：%s" % text) from exc


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dynasties",
        description="中国朝代：起止年代、都城、开国君主与可打印的时间轴、练习题。",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="dynasties %s" % __version__,
    )
    subparsers = parser.add_subparsers(dest="command", metavar="命令")

    info_parser = subparsers.add_parser("info", help="查看朝代详情")
    info_parser.add_argument("name", help="朝代名称或别名")

    year_parser = subparsers.add_parser("year", help="查询某年所处的朝代")
    year_parser.add_argument("year", type=_int_arg, help="年份，公元前用负数")

    span_parser = subparsers.add_parser("span", help="查看朝代持续年数")
    span_parser.add_argument("name", help="朝代名称或别名")

    subparsers.add_parser("list", help="按时间顺序列出全部朝代")

    quiz_parser = subparsers.add_parser("quiz", help="生成四选一测验")
    quiz_parser.add_argument("--count", type=_int_arg, default=10, help="题目数量（1-40）")
    quiz_parser.add_argument("--seed", type=_int_arg, default=None, help="随机种子")
    quiz_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    ordering_parser = subparsers.add_parser("ordering", help="生成朝代排序练习")
    ordering_parser.add_argument("--count", type=_int_arg, default=5, help="题目数量（1-40）")
    ordering_parser.add_argument("--seed", type=_int_arg, default=None, help="随机种子")
    ordering_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    match_parser = subparsers.add_parser("match", help="生成朝代配对练习")
    match_parser.add_argument("--count", type=_int_arg, default=6, help="配对数量（1-18）")
    match_parser.add_argument("--seed", type=_int_arg, default=None, help="随机种子")
    match_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    timeline_parser = subparsers.add_parser("timeline", help="查看或导出朝代时间轴")
    timeline_parser.add_argument("-o", "--output", default=None, help="输出 HTML 文件")

    return parser


def _write_output(path: str, content: str) -> None:
    """以 UTF-8 写入文件，失败时转换为中文 ValueError。"""
    if not isinstance(path, str):
        raise TypeError("输出路径必须是字符串")
    target = path.strip()
    if not target:
        raise ValueError("输出路径不能为空")
    directory = os.path.dirname(os.path.abspath(target))
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except OSError as exc:
        detail = exc.strerror or str(exc)
        raise ValueError("无法写入文件 %s：%s" % (target, detail)) from exc
    print("已生成：%s" % target)


def _print_info(dynasty: Dynasty) -> None:
    print("名称：%s" % dynasty.name)
    print("别名：%s" % ("、".join(dynasty.aliases) if dynasty.aliases else "无"))
    print("起止：%s" % format_years(dynasty.start, dynasty.end))
    print("持续时间：%d 年（含首尾年份）" % dynasty_span(dynasty.name))
    print("都城：%s" % dynasty.capital)
    print("开国君主：%s" % dynasty.founder)
    print("代表成就：%s" % dynasty.achievement)


def _print_list(items: Sequence[Dynasty]) -> None:
    print("中国朝代列表（共 %d 个朝代 / 时期）" % len(items))
    for index, item in enumerate(items, start=1):
        print(
            "%2d. %s　%s　都城：%s"
            % (index, item.name, format_years(item.start, item.end), item.capital)
        )


def _print_quiz_items(items: Sequence[Dict[str, object]]) -> None:
    letters = "ABCDEFGH"
    for item in items:
        print("%s. %s" % (item["index"], item["question"]))
        options = item["options"]
        if isinstance(options, (list, tuple)):
            for position, option in enumerate(options):
                marker = letters[position] if position < len(letters) else str(position + 1)
                print("   %s. %s" % (marker, option))
        print("")
    print("参考答案与解析")
    for item in items:
        answer_index = int(item["answer_index"])
        marker = letters[answer_index] if answer_index < len(letters) else str(answer_index + 1)
        print("%s. %s. %s" % (item["index"], marker, item["answer"]))
        print("   解析：%s" % item["explanation"])


def _print_ordering(items: Sequence[Dict[str, object]]) -> None:
    for item in items:
        print("%s. %s" % (item["index"], item["question"]))
        shuffled = item["shuffled"]
        if isinstance(shuffled, (list, tuple)):
            print("   %s" % "　".join(str(name) for name in shuffled))
        print("")
    print("参考答案与解析")
    for item in items:
        answer = item["answer"]
        if isinstance(answer, (list, tuple)):
            print("%s. %s" % (item["index"], " → ".join(str(name) for name in answer)))
        print("   解析：%s" % item["explanation"])


def _print_match(pairs: Sequence[Tuple[str, str]]) -> None:
    print("朝代配对练习（共 %d 组）" % len(pairs))
    for index, (name, _) in enumerate(pairs, start=1):
        print("%d. %s —— ____________" % (index, name))
    print("参考答案与解析")
    for index, (name, value) in enumerate(pairs, start=1):
        print("%d. %s — %s" % (index, name, value))


def _run(args: argparse.Namespace) -> int:
    command = args.command
    if command == "info":
        _print_info(find_dynasty(args.name))
        return 0
    if command == "year":
        year_value = int(args.year)
        dynasty = at_year(year_value)
        print(
            "%s：%s（%s），都城：%s，开国君主：%s。"
            % (
                format_year(year_value),
                dynasty.name,
                format_years(dynasty.start, dynasty.end),
                dynasty.capital,
                dynasty.founder,
            )
        )
        return 0
    if command == "span":
        dynasty = find_dynasty(args.name)
        print(
            "%s：%s，共 %d 年（含首尾年份）。"
            % (
                dynasty.name,
                format_years(dynasty.start, dynasty.end),
                dynasty_span(dynasty.name),
            )
        )
        return 0
    if command == "list":
        _print_list(all_dynasties())
        return 0
    if command == "quiz":
        items = quiz_items(int(args.count), args.seed)
        if args.output is not None:
            _write_output(
                args.output,
                quiz_html(items, "中国朝代知识测验", with_answers=True),
            )
        else:
            _print_quiz_items(items)
        return 0
    if command == "ordering":
        items = ordering_items(int(args.count), args.seed)
        if args.output is not None:
            _write_output(
                args.output,
                ordering_html(items, "中国朝代排序练习", with_answers=True),
            )
        else:
            _print_ordering(items)
        return 0
    if command == "match":
        pairs = match_items(int(args.count), args.seed)
        if args.output is not None:
            _write_output(args.output, match_html(pairs, "中国朝代配对练习"))
        else:
            _print_match(pairs)
        return 0
    if command == "timeline":
        items = all_dynasties()
        if args.output is not None:
            _write_output(args.output, timeline_html(items, "中国朝代时间轴"))
        else:
            print(timeline_svg())
        return 0
    if command is None:
        _build_parser().print_help()
        return 2
    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，返回进程退出码。"""
    _ensure_utf8_console()
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        return _run(args)
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 0 if code is None else 2
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
