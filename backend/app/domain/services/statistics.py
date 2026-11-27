"""月度统计（SRS F-P0-03 / F-P0-05）。

统计口径：
1. 排除 direction = TRANSFER（转账 / 不计收支）；
2. 排除被识别为退款对的双方（退款与其原支出）；
3. 分类分布与柱状趋势基于同一份净支出，保证与图表、人工核对一致。
"""

from __future__ import annotations

import calendar
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.entities import Transaction
from app.domain.enums import Direction
from app.domain.services.refunds import RefundPair, linked_transaction_ids
from app.domain.time import as_utc

_PERIOD_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


@dataclass(frozen=True)
class CategorySlice:
    category_id: int | None
    category_name: str
    total_cents: int
    count: int
    share_bps: int


@dataclass(frozen=True)
class DailyPoint:
    day: date
    expense_cents: int
    expense_count: int


@dataclass(frozen=True)
class MonthlyReport:
    period: str
    expense_cents: int
    income_cents: int
    refund_cents: int
    transfer_excluded_cents: int
    refunded_expense_cents: int
    counted_transactions: int
    refund_pair_count: int
    refund_excluded_count: int = 0
    transfer_count: int = 0
    by_category: tuple[CategorySlice, ...] = field(default_factory=tuple)
    daily: tuple[DailyPoint, ...] = field(default_factory=tuple)


def period_bounds(period: str, tzinfo: ZoneInfo) -> tuple[datetime, datetime]:
    """返回该自然月（按用户时区）的 [起, 止) UTC 时间。"""
    match = _PERIOD_RE.match(period or "")
    if not match:
        raise ValueError("period 必须为 YYYY-MM")
    year, month = int(match.group(1)), int(match.group(2))
    start = datetime(year, month, 1, tzinfo=tzinfo)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=tzinfo)
    else:
        end = datetime(year, month + 1, 1, tzinfo=tzinfo)
    return as_utc(start), as_utc(end)


def build_monthly_report(
    *,
    period: str,
    transactions: Sequence[Transaction],
    refund_pairs: Sequence[RefundPair],
    category_names: Mapping[int | None, str],
    tzinfo: ZoneInfo,
) -> MonthlyReport:
    excluded = linked_transaction_ids(refund_pairs)

    expense_cents = 0
    income_cents = 0
    refund_cents = 0
    refunded_expense_cents = 0
    transfer_cents = 0
    transfer_count = 0
    refund_excluded_count = 0
    counted = 0
    by_category: dict[int | None, list[int]] = {}
    daily: dict[date, list[int]] = {}

    for txn in transactions:
        if txn.direction is Direction.TRANSFER:
            transfer_cents += txn.amount_cents
            transfer_count += 1
            continue
        if txn.id is not None and txn.id in excluded:
            refund_excluded_count += 1
            if txn.direction is Direction.INCOME:
                refund_cents += txn.amount_cents
            else:
                refunded_expense_cents += txn.amount_cents
            continue
        if txn.direction is Direction.INCOME:
            income_cents += txn.amount_cents
            continue

        expense_cents += txn.amount_cents
        counted += 1
        bucket = by_category.setdefault(txn.category_id, [0, 0])
        bucket[0] += txn.amount_cents
        bucket[1] += 1
        day = txn.occurred_at.astimezone(tzinfo).date()
        slot = daily.setdefault(day, [0, 0])
        slot[0] += txn.amount_cents
        slot[1] += 1

    slices = []
    for category_id, (total, count) in by_category.items():
        share = (total * 10000) // expense_cents if expense_cents else 0
        name = category_names.get(category_id) or "未分类"
        slices.append(
            CategorySlice(
                category_id=category_id,
                category_name=name,
                total_cents=total,
                count=count,
                share_bps=share,
            )
        )
    slices.sort(key=lambda item: (-item.total_cents, item.category_name))

    year, month = int(period[:4]), int(period[5:7])
    days_in_month = calendar.monthrange(year, month)[1]
    points = []
    for offset in range(days_in_month):
        day = date(year, month, 1) + timedelta(days=offset)
        totals = daily.get(day, [0, 0])
        points.append(DailyPoint(day=day, expense_cents=totals[0], expense_count=totals[1]))

    return MonthlyReport(
        period=period,
        expense_cents=expense_cents,
        income_cents=income_cents,
        refund_cents=refund_cents,
        transfer_excluded_cents=transfer_cents,
        refunded_expense_cents=refunded_expense_cents,
        counted_transactions=counted,
        refund_pair_count=len(refund_pairs),
        refund_excluded_count=refund_excluded_count,
        transfer_count=transfer_count,
        by_category=tuple(slices),
        daily=tuple(points),
    )
