"""预算路由：GET/PUT /budget（金额整数分，阈值用 0~1 小数）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.periods import period_of
from app.domain.entities import Budget
from app.domain.errors import NotFoundError
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import BudgetRead, BudgetUpsertRequest, budget_to_read

router = APIRouter(prefix="/budget", tags=["预算"])

_PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"
# 前端预算页首次进入时没有已保存的预算，按开发桩默认值回填
_DEFAULT_BUDGET_CENTS = 420_000


@router.get("", response_model=BudgetRead, summary="读取预算与阈值（未设置返回默认值）")
def get_budget(
    month: str | None = Query(default=None, pattern=_PERIOD_PATTERN, description="YYYY-MM，默认当月"),
    container: Container = Depends(get_container),
) -> BudgetRead:
    explicit = month is not None
    period = month or period_of(container.clock.now(), container.tz)
    try:
        budget = container.budgets.get(period)
    except NotFoundError:
        if explicit:
            raise
        budget = Budget(
            period=period,
            amount_cents=_DEFAULT_BUDGET_CENTS,
            warn_bps=container.settings.warn_bps,
            alert_bps=container.settings.alert_bps,
        )
    return budget_to_read(budget)


@router.put("", response_model=BudgetRead, summary="保存预算与双阈值（warn < alert）")
def upsert_budget(
    payload: BudgetUpsertRequest,
    container: Container = Depends(get_container),
) -> BudgetRead:
    period = payload.month or period_of(container.clock.now(), container.tz)
    saved = container.budgets.upsert(
        period=period,
        amount_cents=payload.amount,
        warn_threshold=payload.warn_threshold,
        alert_threshold=payload.alert_threshold,
    )
    return budget_to_read(saved)
