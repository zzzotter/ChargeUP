"""预警事件路由：分页查询 + 标记已读。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.domain.enums import AlertLevel
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import AlertEventRead, AlertPatchRequest, Page, alert_to_read

router = APIRouter(prefix="/alerts", tags=["预警"])

_PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get("", response_model=Page[AlertEventRead], summary="预警事件流")
def list_alerts(
    level: AlertLevel | None = Query(default=None),
    period: str | None = Query(default=None, pattern=_PERIOD_PATTERN),
    month: str | None = Query(
        default=None, pattern=_PERIOD_PATTERN, description="前端按 month 过滤，等价 period"
    ),
    read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    container: Container = Depends(get_container),
) -> Page[AlertEventRead]:
    period = period or month
    events, total = container.budgets.alerts(
        level=level, period=period, read=read, page=page, page_size=page_size
    )
    amounts = {item.period: container.budgets.amount_for(item.period) for item in events}
    return Page(
        items=[alert_to_read(event, container.tz, amounts.get(event.period, 0)) for event in events],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.patch("/{alert_id}", response_model=AlertEventRead, summary="标记预警已读")
def patch_alert(
    alert_id: int,
    payload: AlertPatchRequest,
    container: Container = Depends(get_container),
) -> AlertEventRead:
    event = container.budgets.mark_read(alert_id, payload.read)
    return alert_to_read(event, container.tz, container.budgets.amount_for(event.period))
