"""dynasties：中国朝代的起止年代、都城、时间轴与练习题目。"""

from __future__ import annotations

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
    span,
)

__version__ = "0.1.0"

__all__ = [
    "Dynasty",
    "__version__",
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
