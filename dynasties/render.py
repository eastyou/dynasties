"""HTML / SVG 渲染：可打印的朝代时间轴、测验、排序与配对练习。"""

from __future__ import annotations

import html
from typing import Dict, List, Sequence, Tuple

from .model import Dynasty, all_dynasties, format_years

__all__ = [
    "match_html",
    "ordering_html",
    "quiz_html",
    "timeline_html",
    "timeline_svg",
]

_PALETTE: Sequence[str] = (
    "#8b5e34",
    "#9c6644",
    "#7f5539",
    "#a47148",
    "#6c584c",
    "#7d6b5d",
    "#8a7a68",
    "#9d8420",
    "#6b705c",
    "#5c6b73",
    "#4f5d75",
    "#546a7b",
    "#3d5a80",
    "#476b6b",
    "#5f7161",
    "#6d6875",
    "#7c6a5a",
    "#806d5b",
    "#6b5b53",
    "#5b5f63",
)

_BASE_CSS = """
:root { color-scheme: light; }
* { box-sizing: border-box; }
body {
  margin: 0 auto;
  padding: 28px 22px 48px;
  max-width: 960px;
  background: #fbf9f5;
  color: #2f2a24;
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "Source Han Sans SC", sans-serif;
  line-height: 1.65;
}
h1 { font-size: 1.7rem; margin: 0 0 6px; letter-spacing: 0.04em; }
h2 { font-size: 1.15rem; margin: 28px 0 10px; }
p { margin: 6px 0; }
.subtitle { color: #7a6f63; font-size: 0.9rem; }
.meta { color: #7a6f63; font-size: 0.85rem; margin-top: 18px; }
table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
th, td { border-bottom: 1px solid #e5ded2; padding: 7px 8px; text-align: left; vertical-align: top; }
th { background: #f0e9dd; font-weight: 600; white-space: nowrap; }
td.num { white-space: nowrap; color: #5c5348; }
.timeline { margin: 18px 0 8px; }
.row { display: grid; grid-template-columns: 190px 1fr; gap: 10px; align-items: center; margin: 7px 0; }
.label { display: flex; flex-direction: column; line-height: 1.25; }
.label .name { font-weight: 600; }
.label .years { color: #7a6f63; font-size: 0.78rem; }
.track { position: relative; height: 16px; background: #f0e9dd; border-radius: 8px; }
.bar { position: absolute; top: 0; height: 16px; border-radius: 8px; }
.card { background: #fff; border: 1px solid #e7dfd2; border-radius: 10px; padding: 16px 18px; margin: 14px 0; }
.question { font-weight: 600; margin: 0 0 8px; }
ol.options { list-style: none; margin: 0; padding: 0; }
ol.options li { padding: 4px 0; }
.key { display: inline-block; min-width: 1.6em; font-weight: 600; color: #8b5e34; }
.answer { margin-top: 10px; padding: 8px 10px; background: #f6f1e7; border-left: 3px solid #8b5e34; font-size: 0.9rem; }
.answer strong { color: #7f4f24; }
.blank { margin-top: 10px; color: #a59a8c; font-size: 0.85rem; letter-spacing: 0.1em; }
.tags { display: flex; flex-wrap: wrap; gap: 8px; margin: 8px 0 0; padding: 0; list-style: none; }
.tags li { border: 1px solid #ddd2c1; background: #fff; border-radius: 999px; padding: 2px 12px; font-size: 0.9rem; }
.columns { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-top: 8px; }
.columns ol { margin: 4px 0; padding-left: 1.4em; }
.columns ul { margin: 4px 0; padding-left: 0; list-style: none; }
.columns li { padding: 3px 0; }
@page { size: A4; margin: 14mm; }
@media print {
  body { background: #fff; max-width: none; padding: 0; font-size: 10.5pt; }
  .no-print { display: none !important; }
  .card, .row, tr { break-inside: avoid; page-break-inside: avoid; }
  a { color: inherit; text-decoration: none; }
}
"""


def _require_int(value: object, label: str) -> int:
    """校验整数输入，显式排除 bool。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s必须是整数，不能是 %s" % (label, type(value).__name__))
    return value


def _require_title(title: str) -> str:
    if not isinstance(title, str):
        raise TypeError("标题必须是字符串，不能是 %s" % type(title).__name__)
    text = title.strip()
    if not text:
        raise ValueError("标题不能为空")
    return text


def _require_bool(value: bool, label: str) -> bool:
    if not isinstance(value, bool):
        raise TypeError("%s必须是布尔值" % label)
    return value


def _validate_dynasties(dynasties: Sequence[Dynasty]) -> List[Dynasty]:
    if isinstance(dynasties, (str, bytes)) or not isinstance(dynasties, Sequence):
        raise TypeError("朝代列表必须是 Dynasty 序列")
    items = list(dynasties)
    if not items:
        raise ValueError("朝代列表不能为空")
    for item in items:
        if not isinstance(item, Dynasty):
            raise TypeError("朝代列表只能包含 Dynasty 对象")
    return items


def _validate_quiz_items(
    items: Sequence[Dict[str, object]]
) -> List[Dict[str, object]]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise TypeError("题目列表必须是字典序列")
    collected = list(items)
    if not collected:
        raise ValueError("题目列表不能为空")
    for position, item in enumerate(collected, start=1):
        if not isinstance(item, dict):
            raise TypeError("第 %d 道题目必须是字典" % position)
        for field in (
            "index",
            "question",
            "options",
            "answer_index",
            "answer",
            "explanation",
        ):
            if field not in item:
                raise ValueError("第 %d 道题目缺少字段：%s" % (position, field))
        if not isinstance(item["question"], str) or not item["question"].strip():
            raise ValueError("第 %d 道题目的题干不能为空" % position)
        index_value = item["index"]
        if isinstance(index_value, bool) or not isinstance(index_value, int):
            raise TypeError("第 %d 道题目的序号必须是整数" % position)
        if index_value < 1:
            raise ValueError("第 %d 道题目的序号必须为正整数" % position)
        options = item["options"]
        if not isinstance(options, (list, tuple)) or len(options) < 2:
            raise ValueError("第 %d 道题目的选项至少需要两个" % position)
        answer_index = item["answer_index"]
        if isinstance(answer_index, bool) or not isinstance(answer_index, int):
            raise TypeError("第 %d 道题目的答案索引必须是整数" % position)
        if answer_index < 0 or answer_index >= len(options):
            raise ValueError("第 %d 道题目的答案索引越界" % position)
        if item["answer"] != options[answer_index]:
            raise ValueError("第 %d 道题目的答案与选项不一致" % position)
        if not isinstance(item["explanation"], str) or not item["explanation"].strip():
            raise ValueError("第 %d 道题目的解析不能为空" % position)
    return collected


def _validate_ordering_items(
    items: Sequence[Dict[str, object]]
) -> List[Dict[str, object]]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise TypeError("题目列表必须是字典序列")
    collected = list(items)
    if not collected:
        raise ValueError("题目列表不能为空")
    for position, item in enumerate(collected, start=1):
        if not isinstance(item, dict):
            raise TypeError("第 %d 道题目必须是字典" % position)
        for field in ("index", "question", "shuffled", "answer", "explanation"):
            if field not in item:
                raise ValueError("第 %d 道题目缺少字段：%s" % (position, field))
        if not isinstance(item["question"], str) or not item["question"].strip():
            raise ValueError("第 %d 道题目的题干不能为空" % position)
        index_value = item["index"]
        if isinstance(index_value, bool) or not isinstance(index_value, int):
            raise TypeError("第 %d 道题目的序号必须是整数" % position)
        if index_value < 1:
            raise ValueError("第 %d 道题目的序号必须为正整数" % position)
        shuffled = item["shuffled"]
        answer = item["answer"]
        if not isinstance(shuffled, (list, tuple)) or not shuffled:
            raise ValueError("第 %d 道题目的乱序选项不能为空" % position)
        if not isinstance(answer, (list, tuple)) or not answer:
            raise ValueError("第 %d 道题目的答案顺序不能为空" % position)
        if len(shuffled) != len(answer):
            raise ValueError("第 %d 道题目的选项与答案数量不一致" % position)
        for name in list(shuffled) + list(answer):
            if not isinstance(name, str) or not name.strip():
                raise ValueError("第 %d 道题目的朝代名称不合法" % position)
        if not isinstance(item["explanation"], str) or not item["explanation"].strip():
            raise ValueError("第 %d 道题目的解析不能为空" % position)
    return collected


def _validate_pairs(
    pairs: Sequence[Tuple[str, str]]
) -> List[Tuple[str, str]]:
    if isinstance(pairs, (str, bytes)) or not isinstance(pairs, Sequence):
        raise TypeError("配对列表必须是二元组序列")
    collected = list(pairs)
    if not collected:
        raise ValueError("配对列表不能为空")
    seen: List[str] = []
    for position, pair in enumerate(collected, start=1):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise TypeError("第 %d 个配对必须是长度为 2 的元组" % position)
        name, value = pair
        if not isinstance(name, str) or not name.strip():
            raise ValueError("第 %d 个配对的朝代名称不能为空" % position)
        if not isinstance(value, str) or not value.strip():
            raise ValueError("第 %d 个配对的内容不能为空" % position)
        if value in seen:
            raise ValueError("配对内容重复：%s" % value)
        seen.append(value)
    return collected


def _document(title: str, body: str, subtitle: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="zh-CN">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>%s</title>\n"
        "<style>%s</style>\n"
        "</head>\n<body>\n"
        "<h1>%s</h1>\n"
        '<p class="subtitle">%s</p>\n'
        "%s"
        '<p class="meta">由 dynasties 生成 · MIT License · eastyou</p>\n'
        "</body>\n</html>\n"
        % (html.escape(title), _BASE_CSS, html.escape(title), html.escape(subtitle), body)
    )


def _tick_label(year: int) -> str:
    if year < 0:
        return "前%d" % (-year)
    return "%d" % year


def timeline_svg(start_year: int = -2100, end_year: int = 1912) -> str:
    """渲染横向 SVG 时间轴，色块按真实年代比例定位，标签错行显示。"""
    start_value = _require_int(start_year, "起始年")
    end_value = _require_int(end_year, "结束年")
    if start_value >= end_value:
        raise ValueError("时间轴起始年必须早于结束年：%d — %d" % (start_value, end_value))

    selected = [
        item
        for item in all_dynasties()
        if item.end >= start_value and item.start <= end_value
    ]
    if not selected:
        raise ValueError(
            "指定时间范围（%d—%d）内没有朝代" % (start_value, end_value)
        )

    width = 1000
    margin_left = 26
    margin_right = 26
    chart_width = width - margin_left - margin_right
    top = 58
    lane_count = 6
    lane_height = 40
    height = top + lane_count * lane_height + 34
    year_span = end_value - start_value

    def scale(year: int) -> float:
        return margin_left + (year - start_value) / year_span * chart_width

    lane_rights: List[float] = [float(margin_left - 1000)] * lane_count
    blocks: List[str] = []
    for index, item in enumerate(selected):
        visible_start = max(item.start, start_value)
        visible_end = min(item.end, end_value)
        x1 = scale(visible_start)
        x2 = scale(visible_end)
        bar_width = max(x2 - x1, 2.0)
        centre = x1 + (x2 - x1) / 2.0
        label_width = len(item.name) * 14.0 + 14.0
        label_center = min(
            max(centre, margin_left + label_width / 2.0),
            width - margin_right - label_width / 2.0,
        )
        left = label_center - label_width / 2.0
        lane = lane_count - 1
        for candidate in range(lane_count):
            if left >= lane_rights[candidate] + 4.0:
                lane = candidate
                break
        lane_rights[lane] = label_center + label_width / 2.0
        y = top + lane * lane_height
        colour = _PALETTE[index % len(_PALETTE)]
        blocks.append(
            '<rect x="%.2f" y="%d" width="%.2f" height="14" rx="4" fill="%s">'
            "<title>%s</title></rect>"
            % (
                x1,
                y + 16,
                bar_width,
                colour,
                html.escape("%s %s" % (item.name, format_years(item.start, item.end))),
            )
        )
        blocks.append(
            '<text x="%.2f" y="%d" text-anchor="middle" font-size="12" fill="#4a3f34">'
            "%s</text>"
            % (label_center, y + 11, html.escape(item.name))
        )

    ticks: List[str] = []
    step = 500
    tick_year = int((start_value // step) * step)
    while tick_year <= end_value:
        if tick_year >= start_value:
            x = scale(tick_year)
            ticks.append(
                '<line x1="%.2f" y1="%d" x2="%.2f" y2="%d" stroke="#d8cec0" stroke-width="1"/>'
                '<text x="%.2f" y="%d" text-anchor="middle" font-size="10" fill="#8a7a68">%s</text>'
                % (x, top - 18, x, top - 6, x, top - 24, _tick_label(tick_year))
            )
        tick_year += step

    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="100%%" '
        'role="img" aria-labelledby="dynasties-timeline-title">\n'
        '<title id="dynasties-timeline-title">中国朝代时间轴（%s — %s）</title>\n'
        '<rect x="0" y="0" width="%d" height="%d" fill="#fbf9f5"/>\n'
        '<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#b9ac99" stroke-width="1.5"/>\n'
        "%s\n%s\n"
        "</svg>\n"
        % (
            width,
            height,
            html.escape(format_years(start_value, end_value)),
            html.escape(format_years(start_value, end_value)),
            width,
            height,
            margin_left,
            top - 12,
            width - margin_right,
            top - 12,
            "\n".join(ticks),
            "\n".join(blocks),
        )
    )
    return svg


def timeline_html(dynasties: Sequence[Dynasty], title: str) -> str:
    """渲染时间轴（按年代比例）与朝代明细表。"""
    items = _validate_dynasties(dynasties)
    safe_title = _require_title(title)
    ordered = sorted(items, key=lambda item: item.start)
    first_year = ordered[0].start
    last_year = max(item.end for item in ordered)
    total = max(last_year - first_year, 1)

    rows: List[str] = []
    for index, item in enumerate(ordered):
        left = (item.start - first_year) / total * 100.0
        width = max((item.end - item.start) / total * 100.0, 0.8)
        colour = _PALETTE[index % len(_PALETTE)]
        rows.append(
            '<div class="row">'
            '<div class="label"><span class="name">%s</span>'
            '<span class="years">%s</span></div>'
            '<div class="track">'
            '<span class="bar" style="left:%.2f%%;width:%.2f%%;background:%s" '
            'title="%s"></span>'
            "</div>"
            "</div>"
            % (
                html.escape(item.name),
                html.escape(format_years(item.start, item.end)),
                left,
                width,
                colour,
                html.escape("%s %s" % (item.name, format_years(item.start, item.end))),
            )
        )

    table_rows: List[str] = []
    for index, item in enumerate(ordered, start=1):
        aliases = "、".join(item.aliases) if item.aliases else "—"
        table_rows.append(
            "<tr>"
            "<td>%d</td><td>%s</td><td>%s</td><td class=\"num\">%s</td>"
            "<td>%s</td><td>%s</td><td>%s</td>"
            "</tr>"
            % (
                index,
                html.escape(item.name),
                html.escape(aliases),
                html.escape(format_years(item.start, item.end)),
                html.escape(item.capital),
                html.escape(item.founder),
                html.escape(item.achievement),
            )
        )

    body = (
        '<div class="timeline">\n%s\n</div>\n'
        '<h2>时间轴比例尺</h2>\n'
        '<p class="subtitle">起点：%s　终点：%s　跨度：%d 年</p>\n'
        "<h2>朝代明细</h2>\n"
        "<table>\n<thead><tr>"
        "<th>序号</th><th>朝代</th><th>别名</th><th>起止</th>"
        "<th>都城</th><th>开国君主</th><th>代表成就</th>"
        "</tr></thead>\n<tbody>\n%s\n</tbody>\n</table>\n"
        % (
            "\n".join(rows),
            html.escape(format_years(ordered[0].start, ordered[0].end)),
            html.escape(format_years(ordered[-1].start, ordered[-1].end)),
            total,
            "\n".join(table_rows),
        )
    )
    return _document(
        safe_title,
        body,
        "共 %d 个朝代 / 时期，跨度 %d 年。" % (len(ordered), total),
    )


def quiz_html(
    items: Sequence[Dict[str, object]], title: str, with_answers: bool = False
) -> str:
    """渲染四选一测验页面，可选显示答案与解析。"""
    collected = _validate_quiz_items(items)
    safe_title = _require_title(title)
    _require_bool(with_answers, "with_answers")
    letters = "ABCDEFGH"
    cards: List[str] = []
    for item in collected:
        options = list(item["options"])  # type: ignore[arg-type]
        answer_index = int(item["answer_index"])  # type: ignore[arg-type]
        option_lines: List[str] = []
        for position, option in enumerate(options):
            marker = letters[position] if position < len(letters) else str(position + 1)
            option_lines.append(
                '<li><span class="key">%s</span>%s</li>'
                % (marker, html.escape(str(option)))
            )
        if with_answers:
            footer = (
                '<div class="answer">答案：%s　解析：%s</div>'
                % (
                    html.escape("%s. %s" % (letters[answer_index], str(item["answer"]))),
                    html.escape(str(item["explanation"])),
                )
            )
        else:
            footer = '<div class="blank">答案：____________</div>'
        cards.append(
            '<section class="card">\n'
            '<p class="question">%d. %s</p>\n'
            '<ol class="options">\n%s\n</ol>\n'
            "%s\n</section>"
            % (
                int(item["index"]),  # type: ignore[arg-type]
                html.escape(str(item["question"])),
                "\n".join(option_lines),
                footer,
            )
        )
    body = "\n".join(cards) + "\n"
    hint = "含参考答案" if with_answers else "不含答案，适合课堂练习"
    return _document(safe_title, body, "共 %d 道题，%s。" % (len(collected), hint))


def ordering_html(
    items: Sequence[Dict[str, object]], title: str, with_answers: bool = False
) -> str:
    """渲染朝代排序练习页面，可选显示正确顺序。"""
    collected = _validate_ordering_items(items)
    safe_title = _require_title(title)
    _require_bool(with_answers, "with_answers")
    cards: List[str] = []
    for item in collected:
        shuffled = list(item["shuffled"])  # type: ignore[arg-type]
        tags = "".join("<li>%s</li>" % html.escape(str(name)) for name in shuffled)
        if with_answers:
            answer = list(item["answer"])  # type: ignore[arg-type]
            footer = (
                '<div class="answer">正确顺序：%s　解析：%s</div>'
                % (
                    html.escape(" → ".join(str(name) for name in answer)),
                    html.escape(str(item["explanation"])),
                )
            )
        else:
            footer = '<div class="blank">正确顺序：____________</div>'
        cards.append(
            '<section class="card">\n'
            '<p class="question">%d. %s</p>\n'
            '<ul class="tags">%s</ul>\n'
            "%s\n</section>"
            % (
                int(item["index"]),  # type: ignore[arg-type]
                html.escape(str(item["question"])),
                tags,
                footer,
            )
        )
    body = "\n".join(cards) + "\n"
    hint = "含参考答案" if with_answers else "不含答案，适合课堂练习"
    return _document(safe_title, body, "共 %d 道题，%s。" % (len(collected), hint))


def match_html(pairs: Sequence[Tuple[str, str]], title: str) -> str:
    """渲染朝代与成就 / 都城的配对练习，并附答案对照。"""
    collected = _validate_pairs(pairs)
    safe_title = _require_title(title)
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    left_lines: List[str] = []
    right_lines: List[str] = []
    for name, _ in collected:
        left_lines.append("<li>%s（　　）</li>" % html.escape(name))
    right_values = [value for _, value in collected]
    ordered_right = list(reversed(right_values))
    for position, value in enumerate(ordered_right):
        marker = letters[position] if position < len(letters) else str(position + 1)
        right_lines.append(
            "<li><span class=\"key\">%s</span>%s</li>"
            % (marker, html.escape(value))
        )
    answer_lines: List[str] = []
    for position, (name, value) in enumerate(collected, start=1):
        right_index = ordered_right.index(value)
        marker = letters[right_index] if right_index < len(letters) else str(right_index + 1)
        answer_lines.append(
            "<li>%d. %s — %s</li>" % (position, html.escape(name), marker)
        )
    body = (
        '<p class="subtitle">将左栏朝代与右栏成就 / 都城配对，把字母填在括号内。</p>\n'
        '<div class="columns">\n'
        "<div><h2>朝代</h2>\n<ol>%s</ol></div>\n"
        "<div><h2>成就 / 都城</h2>\n<ul>%s</ul></div>\n"
        "</div>\n"
        "<h2>参考答案</h2>\n"
        "<ol class=\"answers\">\n%s\n</ol>\n"
        % ("\n".join(left_lines), "\n".join(right_lines), "\n".join(answer_lines))
    )
    return _document(safe_title, body, "共 %d 组配对。" % len(collected))
