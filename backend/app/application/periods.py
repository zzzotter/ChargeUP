"""账期与本地时区换算。"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.domain.services.statistics import period_bounds
from app.domain.time import as_utc

DEFAULT_DAY_TIME = time(12, 0)


def resolve_timezone(name: str, logger: logging.Logger | None = None) -> tzinfo:
    """解析时区；无效或缺少 tzdata 时回退 UTC，并通过 logger 输出 ERROR 告警。

    回退而不是拒绝启动，是为了让误配时区的自托管实例仍能启动；
    但账期会按 UTC 计算，必须在日志与 /health 中明确暴露。
    """
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError):
        pass
    if logger is not None:
        logger.error("APP_TIMEZONE=%r 无法识别，已回退为 UTC，账期与本地日期将按 UTC 计算", name)
    try:
        return ZoneInfo("UTC")
    except (ZoneInfoNotFoundError, ValueError):
        return UTC


def period_of(moment: datetime, tz: ZoneInfo) -> str:
    local = as_utc(moment).astimezone(tz)
    return f"{local.year:04d}-{local.month:02d}"


def to_utc(moment: datetime, tz: ZoneInfo) -> datetime:
    """naive 时间按用户本地时区解释，再转 UTC。"""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=tz)
    return as_utc(moment)


def combine_local(day: date, at: time | None, tz: ZoneInfo) -> datetime:
    return as_utc(datetime.combine(day, at or DEFAULT_DAY_TIME).replace(tzinfo=tz))


def local_day_bounds(day: date, tz: ZoneInfo) -> tuple[datetime, datetime]:
    start = as_utc(datetime.combine(day, time.min).replace(tzinfo=tz))
    end = as_utc(datetime.combine(day, time.max).replace(tzinfo=tz))
    return start, end


def month_bounds(period: str, tz: ZoneInfo) -> tuple[datetime, datetime]:
    return period_bounds(period, tz)


def local_date(moment: datetime, tz: ZoneInfo) -> date:
    return as_utc(moment).astimezone(tz).date()
