"""账期变更通知：交易写入后触发预算复核等副作用，失败不阻塞主流程。"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from app.application.periods import period_of

LOGGER = logging.getLogger(__name__)

PeriodHook = Callable[[str], None]


def notify_periods(hooks: Sequence[PeriodHook], moments: Iterable[datetime], tz: ZoneInfo) -> None:
    periods = {period_of(moment, tz) for moment in moments}
    for period in sorted(periods):
        for hook in hooks:
            try:
                hook(period)
            except Exception:  # pragma: no cover - 副作用失败不得影响记账主流程
                LOGGER.exception("账期 %s 的后续处理失败", period)
