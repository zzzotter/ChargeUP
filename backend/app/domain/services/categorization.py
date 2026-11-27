"""自定义分类引擎。

优先级（SRS F-P0-04）：用户自定义关键词规则 > 内置商户词库 > 未分类（null）。
未命中必须为 None，并进入「待分类收件箱」。
"""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass


def normalize_text(value: str | None) -> str:
    """NFKC 归一（全角转半角）+ 去空白 + 小写，用于稳健匹配。"""
    if not value:
        return ""
    text = unicodedata.normalize("NFKC", str(value)).lower()
    return "".join(text.split())


@dataclass(frozen=True)
class MatchRule:
    keyword: str
    category_id: int
    is_builtin: bool = False
    priority: int = 0

    @property
    def weight(self) -> tuple[int, int, int]:
        """排序键：用户规则优先 -> priority 降序 -> 关键词更长者优先。"""
        return (1 if self.is_builtin else 0, -self.priority, -len(normalize_text(self.keyword)))


def match_category(merchant: str | None, rules: Sequence[MatchRule]) -> int | None:
    """返回命中规则的分类 id；无命中返回 None（进入收件箱）。"""
    rule = match_rule(merchant, rules)
    return rule.category_id if rule is not None else None


def match_rule(merchant: str | None, rules: Sequence[MatchRule]) -> MatchRule | None:
    """返回命中的规则本身，供调用方记录分类来源（用户规则 / 内置词库）。"""
    text = normalize_text(merchant)
    if not text:
        return None
    for rule in sorted(rules, key=lambda item: item.weight):
        keyword = normalize_text(rule.keyword)
        if keyword and keyword in text:
            return rule
    return None
