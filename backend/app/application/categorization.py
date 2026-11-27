"""用例层共享的分类解析：显式指定优先，否则跑规则引擎。

返回值同时携带「分类来源」（USER / RULE / BUILTIN / None），
对应前端 Transaction.categorySource 字段。
"""

from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums import CategorySource, CategoryType, Direction
from app.domain.errors import NotFoundError, ValidationError
from app.domain.ports.repositories import UnitOfWork
from app.domain.services.categorization import MatchRule, match_rule

_TYPE_LABELS = {CategoryType.EXPENSE: "支出", CategoryType.INCOME: "收入"}


@dataclass(frozen=True)
class CategoryDecision:
    category_id: int | None
    source: CategorySource | None


def auto_categorize(uow: UnitOfWork, merchant: str, direction: Direction) -> CategoryDecision:
    if direction is Direction.TRANSFER:
        return CategoryDecision(None, None)
    categories = {category.id: category for category in uow.categories.list() if category.id}
    rules = [
        MatchRule(
            keyword=rule.keyword,
            category_id=rule.category_id,
            is_builtin=rule.is_builtin,
            priority=rule.priority,
        )
        for rule in uow.rules.list()
        if categories.get(rule.category_id) is not None
        and categories[rule.category_id].type.value == direction.value
    ]
    matched = match_rule(merchant, rules)
    if matched is None:
        return CategoryDecision(None, None)
    source = CategorySource.BUILTIN if matched.is_builtin else CategorySource.RULE
    return CategoryDecision(matched.category_id, source)


def resolve_category(
    uow: UnitOfWork,
    merchant: str,
    category_id: int | None,
    direction: Direction,
) -> CategoryDecision:
    if category_id is None:
        return auto_categorize(uow, merchant, direction)

    category = uow.categories.get(category_id)
    if category is None:
        raise NotFoundError(f"分类 {category_id} 不存在")
    if direction is Direction.TRANSFER:
        raise ValidationError("转账不参与收支分类，不能指定分类")
    if category.type.value != direction.value:
        raise ValidationError(
            f"分类「{category.name}」属于{_TYPE_LABELS.get(category.type, category.type.value)}类，"
            f"与当前收支方向（{_TYPE_LABELS.get(CategoryType(direction.value), direction.value)}）不一致"
        )
    return CategoryDecision(category_id, CategorySource.USER)
