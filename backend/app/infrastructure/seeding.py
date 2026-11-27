"""默认分类与内置商户词库的幂等初始化。"""

from __future__ import annotations

import logging
from collections.abc import Callable

from app.domain.entities import Category, CategoryRule, UserSettings
from app.domain.ports.repositories import UnitOfWork
from app.domain.services.builtin_lexicon import BUILTIN_KEYWORDS, DEFAULT_CATEGORIES

LOGGER = logging.getLogger(__name__)


def seed_defaults(uow_factory: Callable[[], UnitOfWork]) -> None:
    with uow_factory() as uow:
        existing = {category.name: category for category in uow.categories.list()}
        created_categories = 0
        for name, category_type in DEFAULT_CATEGORIES:
            if name in existing:
                continue
            existing[name] = uow.categories.add(
                Category(name=name, type=category_type, is_system=True)
            )
            created_categories += 1

        existing_rules = {
            (rule.keyword, rule.category_id)
            for rule in uow.rules.list()
            if rule.is_builtin
        }
        created_rules = 0
        for keyword, category_name in BUILTIN_KEYWORDS:
            category = existing.get(category_name)
            if category is None or category.id is None:
                continue
            if (keyword, category.id) in existing_rules:
                continue
            uow.rules.add(
                CategoryRule(
                    keyword=keyword,
                    category_id=category.id,
                    is_builtin=True,
                    priority=0,
                )
            )
            created_rules += 1

        settings_created = False
        if uow.settings.get() is None:
            uow.settings.save(UserSettings())
            settings_created = True

        uow.commit()

    if created_categories or created_rules or settings_created:
        LOGGER.info(
            "初始化默认数据 categories=%d rules=%d settings=%s",
            created_categories,
            created_rules,
            settings_created,
        )
