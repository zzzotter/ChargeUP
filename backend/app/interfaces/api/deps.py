"""应用容器与 FastAPI 依赖。"""

from __future__ import annotations

import logging
from datetime import tzinfo

from fastapi import Request

from app.application.budgets import BudgetService
from app.application.categories import CategoryService
from app.application.imports import ImportService
from app.application.periods import resolve_timezone
from app.application.settings import SettingsService
from app.application.statistics import StatisticsService
from app.application.transactions import TransactionService
from app.config import Settings
from app.infrastructure.clock import SystemClock
from app.infrastructure.db import Database

LOGGER = logging.getLogger(__name__)


class Container:
    """按请求装配用例服务；仓储/会话由 UnitOfWork 管理生命周期。"""

    def __init__(self, settings: Settings, database: Database) -> None:
        self.settings = settings
        self.database = database
        self.tz: tzinfo = resolve_timezone(settings.timezone, LOGGER)
        self.tz_effective = str(self.tz)
        self.tz_fallback = self.tz_effective != settings.timezone
        self.clock = SystemClock()
        uow_factory = database.unit_of_work

        self.statistics = StatisticsService(
            uow_factory, self.tz, self.clock, settings.refund_window_days
        )
        self.budgets = BudgetService(
            uow_factory,
            self.clock,
            self.statistics,
            settings.warn_bps,
            settings.alert_bps,
        )
        self.transactions = TransactionService(
            uow_factory,
            self.clock,
            self.tz,
            on_change=(self.budgets.ensure_events,),
        )
        self.imports = ImportService(
            uow_factory,
            self.clock,
            self.tz,
            on_change=(self.budgets.ensure_events,),
            transactions=self.transactions,
        )
        self.categories = CategoryService(uow_factory)
        self.user_settings = SettingsService(uow_factory, self.clock)


def get_container(request: Request) -> Container:
    container = getattr(request.app.state, "container", None)
    if container is None:  # pragma: no cover - 装配错误
        raise RuntimeError("应用容器未初始化")
    return container
