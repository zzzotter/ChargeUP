"""分类与分类规则用例。"""

from __future__ import annotations

from collections.abc import Callable

from app.application.dto import CategorySuggestion, CategoryView, RuleTestResult
from app.domain.entities import Category, CategoryRule
from app.domain.enums import CategorySource, CategoryType
from app.domain.errors import ConflictError, DuplicateResourceError, NotFoundError
from app.domain.ports.repositories import UnitOfWork
from app.domain.services.categorization import MatchRule, match_rule


class CategoryService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    # ------------------------------------------------------------------ 分类

    def list(self) -> list[CategoryView]:
        """分类列表，附带规则条数与未删除交易数（前端 W09 左栏展示）。"""
        with self._uow_factory() as uow:
            categories = uow.categories.list()
            rule_counts = uow.rules.counts_by_category()
            transaction_counts = uow.transactions.counts_by_category()
        return [
            CategoryView(
                category=category,
                rule_count=rule_counts.get(category.id or 0, 0),
                transaction_count=transaction_counts.get(category.id or 0, 0),
            )
            for category in categories
        ]

    def create(self, name: str, category_type: CategoryType, color: str | None = None) -> Category:
        category = Category(name=name, type=category_type, is_system=False, color=color)
        with self._uow_factory() as uow:
            if uow.categories.find_by_name(category.name) is not None:
                raise DuplicateResourceError(f"分类「{category.name}」已存在")
            saved = uow.categories.add(category)
            uow.commit()
        return saved

    def update(
        self,
        category_id: int,
        *,
        name: str | None = None,
        color: str | None = None,
        update_color: bool = False,
        is_active: bool | None = None,
    ) -> Category:
        with self._uow_factory() as uow:
            category = uow.categories.get(category_id)
            if category is None:
                raise NotFoundError(f"分类 {category_id} 不存在")
            if name is not None:
                normalized = name.strip()
                if not normalized:
                    raise ConflictError("分类名称不能为空")
                existing = uow.categories.find_by_name(normalized)
                if existing is not None and existing.id != category_id:
                    raise DuplicateResourceError(f"分类「{normalized}」已存在")
                category.name = normalized
            if update_color:
                category.color = color
            if is_active is not None:
                category.is_active = bool(is_active)
            saved = uow.categories.update(category)
            uow.commit()
        return saved

    def delete(self, category_id: int) -> None:
        with self._uow_factory() as uow:
            category = uow.categories.get(category_id)
            if category is None:
                raise NotFoundError(f"分类 {category_id} 不存在")
            references = uow.transactions.count_by_category(category_id)
            if references > 0:
                raise ConflictError(
                    f"分类「{category.name}」仍被 {references} 条交易引用，请先迁移后再删除"
                )
            uow.categories.delete(category_id)
            uow.commit()

    # ------------------------------------------------------------------ 建议/干跑

    def suggest(self, name: str) -> CategorySuggestion:
        """快捷填写的实时分类建议：仅返回命中结果，不写库。"""
        with self._uow_factory() as uow:
            matched, _ = self._match(uow, name)
        if matched is None:
            return CategorySuggestion(category_id=None, matched_by=None, rule_keyword=None)
        source = CategorySource.BUILTIN if matched.is_builtin else CategorySource.RULE
        return CategorySuggestion(
            category_id=matched.category_id, matched_by=source, rule_keyword=matched.keyword
        )

    def test_rule(self, name: str) -> RuleTestResult:
        """规则测试器：干跑命中结果与命中规则来源，不写库。"""
        with self._uow_factory() as uow:
            matched, categories = self._match(uow, name)
        if matched is None:
            return RuleTestResult(matched=False)
        category = categories.get(matched.category_id)
        return RuleTestResult(
            matched=True,
            category_id=matched.category_id,
            category_name=category.name if category else None,
            rule_id=matched.id,
            rule_keyword=matched.keyword,
            rule_source=CategorySource.BUILTIN if matched.is_builtin else CategorySource.RULE,
        )

    def _match(self, uow: UnitOfWork, name: str):
        categories = {category.id: category for category in uow.categories.list() if category.id}
        entity_by_rule: dict[tuple[str, int, bool], CategoryRule] = {}
        rules: list[MatchRule] = []
        for rule in uow.rules.list():
            if rule.category_id not in categories:
                continue
            rules.append(
                MatchRule(
                    keyword=rule.keyword,
                    category_id=rule.category_id,
                    is_builtin=rule.is_builtin,
                    priority=rule.priority,
                )
            )
            entity_by_rule[(rule.keyword, rule.category_id, rule.is_builtin)] = rule
        matched = match_rule(name, rules)
        if matched is None:
            return None, categories
        entity = entity_by_rule.get(
            (matched.keyword, matched.category_id, matched.is_builtin)
        )
        return _MatchedRule(entity, matched), categories

    # ------------------------------------------------------------------ 规则

    def list_rules(self) -> list[CategoryRule]:
        with self._uow_factory() as uow:
            return uow.rules.list()

    def create_rule(self, keyword: str, category_id: int, priority: int = 0) -> CategoryRule:
        rule = CategoryRule(
            keyword=keyword, category_id=category_id, is_builtin=False, priority=priority
        )
        with self._uow_factory() as uow:
            if uow.categories.get(rule.category_id) is None:
                raise NotFoundError(f"分类 {rule.category_id} 不存在")
            if uow.rules.find_duplicate(rule.keyword, rule.category_id, is_builtin=False) is not None:
                raise DuplicateResourceError(f"规则「{rule.keyword}」已存在")
            saved = uow.rules.add(rule)
            uow.commit()
        return saved

    def delete_rule(self, rule_id: int) -> None:
        with self._uow_factory() as uow:
            rule = uow.rules.get(rule_id)
            if rule is None:
                raise NotFoundError(f"规则 {rule_id} 不存在")
            if rule.is_builtin:
                raise ConflictError("内置商户词库规则只读，不可删除")
            uow.rules.delete(rule_id)
            uow.commit()


class _MatchedRule:
    """把 MatchRule 与数据库规则实体合并，便于返回 ruleId。"""

    __slots__ = ("id", "keyword", "category_id", "is_builtin")

    def __init__(self, entity: CategoryRule | None, matched: MatchRule) -> None:
        self.id = entity.id if entity else None
        self.keyword = matched.keyword
        self.category_id = matched.category_id
        self.is_builtin = matched.is_builtin
