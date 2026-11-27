"""分类规则匹配与优先级（第 7 天，纯领域逻辑，不依赖框架）。

规则：
- 自定义规则（CUSTOM）优先于系统默认规则（SYSTEM）；
- 同类来源内按 priority 升序（数值小优先级高）；
- 在指定字段做大小写不敏感的关键词包含匹配；
- 全部未命中返回 None，对应“待分类收件箱”。
"""
from dataclasses import dataclass
from enum import Enum

from ..parser.models import RawTransaction


class RuleField(str, Enum):
    ITEM_NAME = "ITEM_NAME"
    COUNTERPARTY = "COUNTERPARTY"


class RuleSource(str, Enum):
    CUSTOM = "CUSTOM"   # 用户自定义，优先级更高
    SYSTEM = "SYSTEM"   # 系统默认


@dataclass(frozen=True)
class CategoryRule:
    rule_id: int
    category_id: int
    keyword: str
    field: RuleField = RuleField.ITEM_NAME
    priority: int = 100
    source: RuleSource = RuleSource.CUSTOM


def _sort_key(rule: CategoryRule):
    source_rank = 0 if rule.source == RuleSource.CUSTOM else 1
    return (source_rank, rule.priority, rule.rule_id)


def ordered_rules(rules: list[CategoryRule]) -> list[CategoryRule]:
    return sorted(rules, key=_sort_key)


def _target_text(tx: RawTransaction, field: RuleField) -> str:
    if field == RuleField.COUNTERPARTY:
        return tx.counterparty or ""
    return tx.item_name or ""


def match_category(tx: RawTransaction, rules: list[CategoryRule]) -> int | None:
    """返回命中的 category_id；未命中返回 None（进入待分类收件箱）。"""
    for rule in ordered_rules(rules):
        haystack = _target_text(tx, rule.field).lower()
        if rule.keyword.strip().lower() in haystack:
            return rule.category_id
    return None


def apply_classification(
    transactions: list[RawTransaction], rules: list[CategoryRule]
) -> tuple[list[RawTransaction], list[RawTransaction]]:
    """批量分类，返回 (已分类, 待分类收件箱)。"""
    classified: list[RawTransaction] = []
    inbox: list[RawTransaction] = []
    for tx in transactions:
        category_id = match_category(tx, rules)
        tx.category_id = category_id
        if category_id is None:
            inbox.append(tx)
        else:
            classified.append(tx)
    return classified, inbox
