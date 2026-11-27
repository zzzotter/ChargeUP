"""设置路由：时薪 / 人设 / 模块开关。"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.application.settings import UNSET
from app.domain.entities import UserSettings
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import ModulesRead, SettingsRead, SettingsUpdateRequest

router = APIRouter(prefix="/settings", tags=["设置"])


def _to_read(settings: UserSettings) -> SettingsRead:
    return SettingsRead(
        hourly_rate=settings.hourly_rate_cents,
        persona=settings.persona,
        modules=ModulesRead(**settings.modules()),
    )


@router.get("", response_model=SettingsRead, summary="读取设置")
def get_settings(container: Container = Depends(get_container)) -> SettingsRead:
    return _to_read(container.user_settings.get())


@router.patch("", response_model=SettingsRead, summary="保存设置")
def update_settings(
    payload: SettingsUpdateRequest,
    container: Container = Depends(get_container),
) -> SettingsRead:
    modules = None
    if payload.modules is not None:
        modules = {
            key: value
            for key, value in payload.modules.model_dump(exclude_none=True).items()
        }
    saved = container.user_settings.update(
        hourly_rate_cents=payload.hourly_rate if payload.sets_hourly_rate else UNSET,
        persona=payload.persona,
        modules=modules,
    )
    return _to_read(saved)
