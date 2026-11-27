"""用户设置用例（时薪 / 人设 / 模块开关）。"""

from __future__ import annotations

from collections.abc import Callable, Mapping

from app.domain.entities import UserSettings
from app.domain.enums import Persona
from app.domain.ports.clock import Clock
from app.domain.ports.repositories import UnitOfWork


class _Unset:
    pass


UNSET = _Unset()


class SettingsService:
    def __init__(self, uow_factory: Callable[[], UnitOfWork], clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def get(self) -> UserSettings:
        with self._uow_factory() as uow:
            settings = uow.settings.get()
            if settings is not None:
                return settings
            saved = uow.settings.save(UserSettings(updated_at=self._clock.now()))
            uow.commit()
            return saved

    def update(
        self,
        *,
        hourly_rate_cents: int | None | _Unset = UNSET,
        persona: Persona | None = None,
        modules: Mapping[str, bool] | None = None,
    ) -> UserSettings:
        settings = self.get()
        with self._uow_factory() as uow:
            current = uow.settings.get() or settings
            if not isinstance(hourly_rate_cents, _Unset):
                current.hourly_rate_cents = hourly_rate_cents
            if persona is not None:
                current.persona = Persona(persona)
            if modules is not None:
                if "wardrobe" in modules:
                    current.module_wardrobe = bool(modules["wardrobe"])
                if "intents" in modules:
                    current.module_intents = bool(modules["intents"])
                if "feedback" in modules:
                    current.module_feedback = bool(modules["feedback"])
            current.updated_at = self._clock.now()
            saved = uow.settings.save(current)
            uow.commit()
        return saved
