"""预算、阈值与预警事件用例（对齐前端 §7 /budget、/alerts）。"""

from __future__ import annotations

import logging
from collections.abc import Callable

from app.application.statistics import StatisticsService
from app.domain.entities import Budget, BudgetEvent
from app.domain.enums import AlertLevel
from app.domain.errors import NotFoundError, ValidationError
from app.domain.ports.clock import Clock
from app.domain.ports.repositories import UnitOfWork
from app.domain.services.budget import evaluate_budget

LOGGER = logging.getLogger(__name__)


def _ratio_to_bps(value: float, field: str) -> int:
    try:
        ratio = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{field} 必须为 0~1 之间的小数") from exc
    if not 0 < ratio <= 1:
        raise ValidationError(f"{field} 必须大于 0 且不超过 1")
    bps = round(ratio * 10000)
    if not 0 < bps <= 10000:
        raise ValidationError(f"{field} 超出允许范围")
    return int(bps)


class BudgetService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        statistics: StatisticsService,
        default_warn_bps: int = 8000,
        default_alert_bps: int = 10000,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._statistics = statistics
        self._default_warn_bps = default_warn_bps
        self._default_alert_bps = default_alert_bps

    def get(self, period: str) -> Budget:
        with self._uow_factory() as uow:
            budget = uow.budgets.get(period)
        if budget is None:
            raise NotFoundError(f"{period} 未设置预算")
        return budget

    def amount_for(self, period: str) -> int:
        """该账期预算金额（未设置返回 0），用于预警事件回填触发时的预算。"""
        with self._uow_factory() as uow:
            budget = uow.budgets.get(period)
        return budget.amount_cents if budget is not None else 0

    def upsert(
        self,
        period: str,
        amount_cents: int,
        warn_threshold: float | None = None,
        alert_threshold: float | None = None,
    ) -> Budget:
        with self._uow_factory() as uow:
            existing = uow.budgets.get(period)

        warn_bps = (
            _ratio_to_bps(warn_threshold, "warnThreshold")
            if warn_threshold is not None
            else (existing.warn_bps if existing else self._default_warn_bps)
        )
        alert_bps = (
            _ratio_to_bps(alert_threshold, "alertThreshold")
            if alert_threshold is not None
            else (existing.alert_bps if existing else self._default_alert_bps)
        )
        if warn_bps >= alert_bps:
            raise ValidationError("warnThreshold 必须小于 alertThreshold")

        budget = Budget(
            period=period,
            amount_cents=amount_cents,
            warn_bps=warn_bps,
            alert_bps=alert_bps,
            updated_at=self._clock.now(),
        )
        with self._uow_factory() as uow:
            saved = uow.budgets.upsert(budget)
            uow.commit()
        # 预算变更后立即复核一次，确保已有支出能触发事件
        self.ensure_events(period)
        return saved

    def ensure_events(self, period: str) -> list[BudgetEvent]:
        """把预警事件同步到当前支出水平；供交易写入/删除后的账期钩子调用。"""
        with self._uow_factory() as uow:
            budget = uow.budgets.get(period)
        if budget is None:
            return []

        spent = self._statistics.expense_total(period)
        thresholds = {
            AlertLevel.WARN: budget.warn_bps,
            AlertLevel.ALERT: budget.alert_bps,
        }
        with self._uow_factory() as uow:
            budget = uow.budgets.get(period) or budget
            events = uow.budget_events.list_for_period(period)
            active = [event.level for event in events if event.is_active]
            evaluation = evaluate_budget(budget, spent, active)
            changed = uow.budget_events.sync(
                period=period,
                budget_id=budget.id or 0,
                active_levels=set(evaluation.levels_due),
                spent_cents=spent,
                moment=self._clock.now(),
                thresholds=thresholds,
            )
            uow.commit()

        for event in changed:
            LOGGER.info(
                "预算预警状态变更 period=%s level=%s active=%s spent=%d",
                period,
                event.level.value,
                event.is_active,
                spent,
            )
        return changed

    def events(self, period: str, *, active_only: bool = False) -> list[BudgetEvent]:
        with self._uow_factory() as uow:
            return uow.budget_events.list_for_period(period, active_only=active_only)

    def alerts(
        self,
        *,
        level: AlertLevel | None = None,
        period: str | None = None,
        read: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BudgetEvent], int]:
        with self._uow_factory() as uow:
            return uow.budget_events.search(
                level=level,
                period=period,
                read=read,
                limit=page_size,
                offset=(page - 1) * page_size,
            )

    def mark_read(self, alert_id: int, read: bool = True) -> BudgetEvent:
        with self._uow_factory() as uow:
            event = uow.budget_events.get(alert_id)
            if event is None:
                raise NotFoundError(f"预警事件 {alert_id} 不存在")
            event.mark_read(read)
            saved = uow.budget_events.update(event)
            uow.commit()
        return saved

    def on_transaction_changed(self, period: str) -> None:
        """账期钩子：任何交易变更后复核预算。"""
        self.ensure_events(period)
