"""统计用例：统一「排除转账 + 剔除退款对」口径，供仪表盘三张卡使用。"""

from __future__ import annotations

from collections.abc import Callable
from datetime import timedelta
from zoneinfo import ZoneInfo

from app.application.dto import CategoryStat, MonthlyTrendPoint, StatsSummaryData
from app.application.periods import month_bounds, period_of
from app.domain.errors import ValidationError
from app.domain.ports.clock import Clock
from app.domain.ports.repositories import TransactionFilter, UnitOfWork
from app.domain.services.refunds import detect_refund_pairs
from app.domain.services.statistics import MonthlyReport, build_monthly_report

DEFAULT_REFUND_WINDOW_DAYS = 7


def _shift_period(period: str, delta: int) -> str:
    year, month = int(period[:4]), int(period[5:7])
    ordinal = year * 12 + (month - 1) + delta
    return f"{ordinal // 12:04d}-{ordinal % 12 + 1:02d}"


class StatisticsService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        tz: ZoneInfo,
        clock: Clock,
        refund_window_days: int = DEFAULT_REFUND_WINDOW_DAYS,
    ) -> None:
        self._uow_factory = uow_factory
        self._tz = tz
        self._clock = clock
        self._window = timedelta(days=refund_window_days)

    def monthly(self, period: str) -> MonthlyReport:
        try:
            start, end = month_bounds(period, self._tz)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        # 多取前后各一个退款窗口，用于识别跨月退款对
        window_start = start - self._window
        window_end = end + self._window

        with self._uow_factory() as uow:
            scope = uow.transactions.list_in_range(window_start, window_end)
            categories = {category.id: category.name for category in uow.categories.list()}

        period_transactions = [txn for txn in scope if start <= txn.occurred_at < end]
        pairs = detect_refund_pairs(scope, self._window)

        return build_monthly_report(
            period=period,
            transactions=period_transactions,
            refund_pairs=pairs,
            category_names=categories,
            tzinfo=self._tz,
        )

    def expense_total(self, period: str) -> int:
        return self.monthly(period).expense_cents

    # -------------------------------------------------------------- 契约端点

    def summary(self, period: str) -> StatsSummaryData:
        report = self.monthly(period)
        try:
            start, end = month_bounds(period, self._tz)
        except ValueError as exc:  # pragma: no cover - monthly 已校验
            raise ValidationError(str(exc)) from exc
        with self._uow_factory() as uow:
            _, uncategorized = uow.transactions.search(
                TransactionFilter(
                    start=start,
                    end=end,
                    uncategorized=True,
                    include_transfers=False,
                    limit=1,
                )
            )
        return StatsSummaryData(
            month=period,
            total_expense_cents=report.expense_cents,
            total_income_cents=report.income_cents,
            excluded_refund_count=report.refund_excluded_count,
            excluded_transfer_count=report.transfer_count,
            uncategorized_count=int(uncategorized),
        )

    def trend(self, months: int = 6, end_period: str | None = None) -> list[MonthlyTrendPoint]:
        months = max(1, min(int(months), 24))
        current = end_period or period_of(self._clock.now(), self._tz)
        periods = [_shift_period(current, -offset) for offset in range(months - 1, -1, -1)]
        return [
            MonthlyTrendPoint(month=period, expense_cents=self.monthly(period).expense_cents)
            for period in periods
        ]

    def categories(self, period: str) -> list[CategoryStat]:
        report = self.monthly(period)
        total = report.expense_cents
        result = []
        for item in report.by_category:
            ratio = round(item.total_cents / total, 4) if total else 0.0
            result.append(
                CategoryStat(
                    category_id=item.category_id,
                    name=item.category_name,
                    amount_cents=item.total_cents,
                    ratio=ratio,
                )
            )
        return result
