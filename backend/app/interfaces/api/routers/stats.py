"""仪表盘统计路由：summary / monthly / categories。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.application.periods import period_of
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import (
    CategoryStatRead,
    MonthlyTrendPointRead,
    StatsSummaryRead,
    stats_summary_to_read,
)

router = APIRouter(prefix="/stats", tags=["统计"])

_PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


def _current_month(month: str | None, container: Container) -> str:
    return month or period_of(container.clock.now(), container.tz)


@router.get("/summary", response_model=StatsSummaryRead, summary="仪表盘概要")
def summary(
    month: str | None = Query(default=None, pattern=_PERIOD_PATTERN, description="YYYY-MM，默认当月"),
    container: Container = Depends(get_container),
) -> StatsSummaryRead:
    return stats_summary_to_read(container.statistics.summary(_current_month(month, container)))


@router.get("/monthly", response_model=list[MonthlyTrendPointRead], summary="月度趋势")
def monthly_trend(
    months: int = Query(default=6, ge=1, le=24),
    month: str | None = Query(
        default=None, pattern=_PERIOD_PATTERN, description="趋势截止月份，默认当月"
    ),
    container: Container = Depends(get_container),
) -> list[MonthlyTrendPointRead]:
    return [
        MonthlyTrendPointRead(month=point.month, expense=point.expense_cents)
        for point in container.statistics.trend(months, month)
    ]


@router.get("/categories", response_model=list[CategoryStatRead], summary="分类分布")
def category_stats(
    month: str | None = Query(default=None, pattern=_PERIOD_PATTERN),
    container: Container = Depends(get_container),
) -> list[CategoryStatRead]:
    return [
        CategoryStatRead(
            category_id=str(item.category_id) if item.category_id is not None else None,
            name=item.name,
            amount=item.amount_cents,
            ratio=item.ratio,
        )
        for item in container.statistics.categories(_current_month(month, container))
    ]
