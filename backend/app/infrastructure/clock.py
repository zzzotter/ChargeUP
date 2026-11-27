"""系统时钟实现。"""

from __future__ import annotations

from datetime import datetime

from app.domain.time import now_utc


class SystemClock:
    def now(self) -> datetime:
        return now_utc()
