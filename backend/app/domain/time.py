"""时间工具：系统内部统一使用带时区的 UTC 时间。"""

from __future__ import annotations

from datetime import UTC, datetime


def as_utc(value: datetime) -> datetime:
    """把任意 datetime 规整为 UTC。

    SQLite 不保存时区信息，读出的 naive 值按 UTC 解释。
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def now_utc() -> datetime:
    return datetime.now(UTC)
