"""中国朝代数据模型：年代、都城、开国君主与练习题目生成。

年份统一使用整数表示，公元前用负数（例如秦朝起于 -221 年）。
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

__all__ = [
    "Dynasty",
    "all_dynasties",
    "at_year",
    "find_dynasty",
    "format_year",
    "format_years",
    "match_items",
    "ordering_items",
    "quiz_items",
    "span",
]

_MIN_YEAR = -2000
_MAX_YEAR = 2100
_QUIZ_TYPES: Tuple[str, ...] = ("capital", "founder", "era")


def _require_int(value: object, label: str) -> int:
    """校验整数输入，显式排除 bool。"""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s必须是整数，不能是 %s" % (label, type(value).__name__))
    return value


def _require_optional_int(value: Optional[int], label: str) -> Optional[int]:
    """校验可为空的整数（随机种子）。"""
    if value is None:
        return None
    return _require_int(value, label)


def _require_text(value: object, label: str) -> str:
    """校验非空字符串输入。"""
    if not isinstance(value, str):
        raise TypeError("%s必须是字符串，不能是 %s" % (label, type(value).__name__))
    text = value.strip()
    if not text:
        raise ValueError("%s不能为空" % label)
    return text


def _year_label(year: int) -> str:
    """把单个年份格式化为「公元前 221 年」或「618 年」。"""
    if year < 0:
        return "公元前 %d 年" % (-year)
    return "公元 %d 年" % year


def format_year(year: int) -> str:
    """格式化单个年份。"""
    return _year_label(_require_int(year, "年份"))


def format_years(start: int, end: int) -> str:
    """格式化年代区间，自动处理公元前后的跨越。"""
    start_value = _require_int(start, "起始年")
    end_value = _require_int(end, "结束年")
    if start_value > end_value:
        raise ValueError("起始年不能晚于结束年：%d — %d" % (start_value, end_value))
    if start_value < 0 <= end_value:
        return "公元前 %d 年 — 公元 %d 年" % (-start_value, end_value)
    if start_value < 0 and end_value < 0:
        return "公元前 %d 年 — 公元前 %d 年" % (-start_value, -end_value)
    return "%d 年 — %d 年" % (start_value, end_value)


@dataclass(frozen=True)
class Dynasty:
    """一个朝代（或时期）的不可变记录。"""

    name: str
    start: int
    end: int
    capital: str
    founder: str
    achievement: str
    aliases: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        name = _require_text(self.name, "朝代名称")
        _require_text(self.capital, "都城")
        _require_text(self.founder, "开国君主")
        _require_text(self.achievement, "代表成就")
        start = _require_int(self.start, "起始年")
        end = _require_int(self.end, "结束年")
        if start > end:
            raise ValueError("起始年必须不晚于结束年：%s（%d—%d）" % (name, start, end))
        if not isinstance(self.aliases, tuple):
            raise TypeError("别名必须是字符串元组")
        for alias in self.aliases:
            _require_text(alias, "别名")
        if name in self.aliases:
            raise ValueError("别名不能与朝代名称相同：%s" % name)


def _d(
    name: str,
    start: int,
    end: int,
    capital: str,
    founder: str,
    achievement: str,
    aliases: Tuple[str, ...] = (),
) -> Dynasty:
    """构造一条朝代记录。"""
    return Dynasty(
        name=name,
        start=start,
        end=end,
        capital=capital,
        founder=founder,
        achievement=achievement,
        aliases=aliases,
    )


_CATALOG: Tuple[Dynasty, ...] = (
    _d(
        "夏",
        -2070,
        -1600,
        "阳城（今河南登封）",
        "禹",
        "建立世袭制，开启「家天下」传统。",
        ("夏朝", "夏后氏"),
    ),
    _d(
        "商",
        -1600,
        -1046,
        "殷（今河南安阳）",
        "汤",
        "甲骨文与青铜文明高度发达。",
        ("商朝", "殷商", "殷"),
    ),
    _d(
        "西周",
        -1046,
        -771,
        "镐京（今陕西西安）",
        "周武王姬发",
        "推行分封制与宗法制，奠定礼乐文明。",
        ("西周王朝", "宗周"),
    ),
    _d(
        "东周",
        -770,
        -256,
        "洛邑（今河南洛阳）",
        "周平王姬宜臼",
        "春秋战国诸侯争霸，诸子百家争鸣。",
        ("东周王朝", "春秋战国"),
    ),
    _d(
        "秦",
        -221,
        -207,
        "咸阳（今陕西咸阳）",
        "秦始皇嬴政",
        "首次统一中国，统一文字、度量衡并推行郡县制。",
        ("秦朝", "大秦"),
    ),
    _d(
        "西汉",
        -202,
        8,
        "长安（今陕西西安）",
        "刘邦",
        "开通丝绸之路，独尊儒术，国力长期强盛。",
        ("前汉", "西汉王朝"),
    ),
    _d(
        "东汉",
        25,
        220,
        "洛阳（今河南洛阳）",
        "刘秀",
        "蔡伦改进造纸术，佛教开始传入中原。",
        ("后汉", "东汉王朝"),
    ),
    _d(
        "三国",
        220,
        280,
        "洛阳、成都、建业",
        "曹丕",
        "魏、蜀、吴鼎立，是中国著名的分裂割据时期。",
        ("三国时期", "魏蜀吴"),
    ),
    _d(
        "西晋",
        280,
        316,
        "洛阳（今河南洛阳）",
        "司马炎",
        "灭吴统一全国，八王之乱后迅速衰亡。",
        ("西晋王朝", "司马晋"),
    ),
    _d(
        "东晋",
        317,
        420,
        "建康（今江苏南京）",
        "司马睿",
        "衣冠南渡，与北方十六国长期对峙。",
        ("东晋王朝", "江左晋"),
    ),
    _d(
        "南北朝",
        420,
        589,
        "建康、洛阳",
        "刘裕",
        "南北政权并立，民族融合与佛教艺术兴盛。",
        ("南北朝时期", "南朝北朝"),
    ),
    _d(
        "隋",
        589,
        618,
        "大兴（今陕西西安）",
        "杨坚",
        "开凿大运河，创立科举制，重建统一帝国。",
        ("隋朝", "大隋"),
    ),
    _d(
        "唐",
        618,
        907,
        "长安（今陕西西安）",
        "李渊",
        "贞观之治与开元盛世，文化开放、商贸繁荣。",
        ("唐朝", "大唐"),
    ),
    _d(
        "五代十国",
        907,
        960,
        "开封、洛阳",
        "朱温",
        "北方五代更替、南方十国并立。",
        ("五代", "五代十国时期"),
    ),
    _d(
        "北宋",
        960,
        1127,
        "东京开封府（今河南开封）",
        "赵匡胤",
        "经济文化繁荣，活字印刷与纸币交子出现。",
        ("北宋王朝", "赵宋"),
    ),
    _d(
        "南宋",
        1127,
        1279,
        "临安（今浙江杭州）",
        "赵构",
        "偏安江南，海外贸易与理学兴盛。",
        ("南宋王朝", "南渡宋"),
    ),
    _d(
        "元",
        1279,
        1368,
        "大都（今北京）",
        "忽必烈",
        "疆域辽阔，行省制影响深远。",
        ("元朝", "大元"),
    ),
    _d(
        "明",
        1368,
        1644,
        "应天（今江苏南京）、北京",
        "朱元璋",
        "郑和下西洋，营建北京城并修筑明长城。",
        ("明朝", "大明"),
    ),
    _d(
        "清",
        1644,
        1912,
        "北京",
        "爱新觉罗·福临",
        "康乾盛世，奠定近代中国的疆域基础。",
        ("清朝", "大清"),
    ),
)


def _validate_catalog(items: Sequence[Dynasty]) -> None:
    """校验目录：名称唯一、顺序单调、年代区间不重叠。"""
    if not items:
        raise ValueError("朝代目录不能为空")
    seen: Dict[str, str] = {}
    previous: Optional[Dynasty] = None
    for item in items:
        if not isinstance(item, Dynasty):
            raise TypeError("朝代目录只能包含 Dynasty 对象")
        if item.name in seen:
            raise ValueError("朝代名称重复：%s" % item.name)
        seen[item.name] = item.name
        for alias in item.aliases:
            if alias in seen:
                raise ValueError("朝代名称或别名重复：%s" % alias)
            seen[alias] = item.name
        if previous is not None:
            if item.start < previous.start:
                raise ValueError(
                    "朝代顺序错误：%s 的起始年早于 %s" % (item.name, previous.name)
                )
            if item.start < previous.end:
                raise ValueError(
                    "朝代年代区间重叠：%s 与 %s" % (previous.name, item.name)
                )
        previous = item


_validate_catalog(_CATALOG)

_NAME_INDEX: Dict[str, int] = {
    item.name: index for index, item in enumerate(_CATALOG)
}


def all_dynasties() -> List[Dynasty]:
    """按时间顺序返回全部朝代。"""
    return list(_CATALOG)


def find_dynasty(query: str) -> Dynasty:
    """按名称或别名查找朝代，未知时抛出 ValueError。"""
    text = _require_text(query, "朝代查询")
    compact = text.replace(" ", "").replace("\u3000", "")
    for item in _CATALOG:
        if compact == item.name:
            return item
    for item in _CATALOG:
        if compact in item.aliases:
            return item
    raise ValueError("未知朝代：%s" % text)


def at_year(year: int) -> Dynasty:
    """返回指定年份所处的朝代，过渡年取新年号所属朝代。"""
    value = _require_int(year, "年份")
    if value < _MIN_YEAR or value > _MAX_YEAR:
        raise ValueError(
            "年份必须在公元前 2000 年到公元 2100 年之间，当前为 %d" % value
        )
    matched: Optional[Dynasty] = None
    for item in _CATALOG:
        if item.start <= value <= item.end:
            matched = item
    if matched is None:
        raise ValueError("%s没有对应的朝代" % _year_label(value))
    return matched


def span(query: str) -> int:
    """返回朝代持续年数（含首尾年份）。"""
    dynasty = find_dynasty(query)
    duration = dynasty.end - dynasty.start + 1
    if duration <= 0:
        raise ValueError("朝代持续时间必须为正：%s" % dynasty.name)
    return duration


def _unique_strings(values: Iterable[str]) -> List[str]:
    """按出现顺序去重，保持候选项唯一。"""
    seen: Set[str] = set()
    result: List[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _four_options(
    rng: random.Random, correct: str, pool: Sequence[str]
) -> Tuple[List[str], int]:
    """从候选池中挑出三个干扰项，与正确答案组成唯一四选一。"""
    candidates = [value for value in _unique_strings(pool) if value != correct]
    if len(candidates) < 3:
        raise ValueError("候选项不足，无法生成四选一题目")
    rng.shuffle(candidates)
    options = candidates[:3]
    options.append(correct)
    rng.shuffle(options)
    return options, options.index(correct)


def quiz_items(count: int, seed: Optional[int] = None) -> List[Dict[str, object]]:
    """生成四选一测验，覆盖都城、开国君主与起止年代。"""
    total = _require_int(count, "题目数量")
    if total < 1 or total > 40:
        raise ValueError("题目数量必须在 1 到 40 之间，当前为 %d" % total)
    seed_value = _require_optional_int(seed, "随机种子")
    rng = random.Random(seed_value)

    specs: List[Tuple[str, Dynasty]] = []
    for kind in _QUIZ_TYPES:
        for dynasty in _CATALOG:
            specs.append((kind, dynasty))
    rng.shuffle(specs)
    if total > len(specs):
        raise ValueError("可用题目不足，请减小题目数量")

    pools: Dict[str, List[str]] = {
        "capital": [item.capital for item in _CATALOG],
        "founder": [item.founder for item in _CATALOG],
        "era": [format_years(item.start, item.end) for item in _CATALOG],
    }

    items: List[Dict[str, object]] = []
    for index, (kind, dynasty) in enumerate(specs[:total], start=1):
        if kind == "capital":
            question = "「%s」的都城是？" % dynasty.name
            correct = dynasty.capital
            explanation = "%s定都%s。" % (dynasty.name, dynasty.capital)
        elif kind == "founder":
            question = "「%s」的开国君主是？" % dynasty.name
            correct = dynasty.founder
            explanation = "%s由%s建立。" % (dynasty.name, dynasty.founder)
        else:
            question = "「%s」的起止年代是？" % dynasty.name
            correct = format_years(dynasty.start, dynasty.end)
            explanation = "%s起于%s，止于%s，共 %d 年。" % (
                dynasty.name,
                format_year(dynasty.start),
                format_year(dynasty.end),
                dynasty.end - dynasty.start + 1,
            )
        options, answer_index = _four_options(rng, correct, pools[kind])
        items.append(
            {
                "index": index,
                "type": kind,
                "question": question,
                "options": options,
                "answer_index": answer_index,
                "answer": correct,
                "explanation": explanation,
            }
        )
    return items


def ordering_items(count: int, seed: Optional[int] = None) -> List[Dict[str, object]]:
    """生成朝代排序题，每题给出 4 至 5 个朝代名。"""
    total = _require_int(count, "题目数量")
    if total < 1 or total > 40:
        raise ValueError("题目数量必须在 1 到 40 之间，当前为 %d" % total)
    seed_value = _require_optional_int(seed, "随机种子")
    rng = random.Random(seed_value)

    items: List[Dict[str, object]] = []
    for number in range(1, total + 1):
        size = 5 if number % 2 == 1 else 4
        chosen = rng.sample(list(_CATALOG), size)
        ordered = sorted(chosen, key=lambda item: item.start)
        answer = [item.name for item in ordered]
        shuffled = [item.name for item in chosen]
        rng.shuffle(shuffled)
        if shuffled == answer:
            shuffled = shuffled[1:] + shuffled[:1]
        explanation = "正确顺序：" + " → ".join(
            "%s（%s）" % (item.name, format_years(item.start, item.end))
            for item in ordered
        )
        items.append(
            {
                "index": number,
                "question": "请按时间先后排列以下 %d 个朝代：" % size,
                "shuffled": shuffled,
                "answer": answer,
                "explanation": explanation,
            }
        )
    return items


def match_items(
    count: int, seed: Optional[int] = None
) -> List[Tuple[str, str]]:
    """生成朝代与成就（或都城）的配对题，返回不可重复的二元组。"""
    total = _require_int(count, "配对数量")
    if total < 1 or total > 18:
        raise ValueError("配对数量必须在 1 到 18 之间，当前为 %d" % total)
    seed_value = _require_optional_int(seed, "随机种子")
    rng = random.Random(seed_value)

    chosen = rng.sample(list(_CATALOG), total)
    used: Set[str] = set()
    pairs: List[Tuple[str, str]] = []
    for index, dynasty in enumerate(chosen):
        value = dynasty.achievement if index % 2 == 0 else dynasty.capital
        if value in used:
            value = dynasty.achievement
        used.add(value)
        pairs.append((dynasty.name, value))
    return pairs
