"""月度统计口径与对账（第 9 天，纯领域逻辑，整数分）。

默认口径（待团队最终确认，已在格式分析文档列出）：
- 支出总额只累加 EXPENSE；INCOME 计入收入；TRANSFER/中性强制排除；0 元排除；
- 退款默认计入 INCOME，不直接冲减单笔支出，净结余自然体现；
- 净结余 = 收入总额 - 支出总额。
所有汇总均为整数运算，不使用 float。
"""
from dataclasses import dataclass, field

from ..parser.models import Direction, RawTransaction


@dataclass
class MonthlyStats:
    year: int
    month: int
    total_expense_cents: int = 0
    total_income_cents: int = 0
    transaction_count: int = 0
    expense_by_category: dict[int | None, int] = field(default_factory=dict)

    @property
    def net_balance_cents(self) -> int:
        return self.total_income_cents - self.total_expense_cents


def _in_month(tx: RawTransaction, year: int, month: int) -> bool:
    return (
        tx.transacted_at.year == year
        and tx.transacted_at.month == month
        and tx.amount_cents > 0
    )


def monthly_summary(
    transactions: list[RawTransaction], year: int, month: int
) -> MonthlyStats:
    stats = MonthlyStats(year=year, month=month)
    for tx in transactions:
        if not _in_month(tx, year, month):
            continue
        if tx.direction == Direction.TRANSFER:
            continue  # 转账/中性不计收支
        stats.transaction_count += 1
        if tx.direction == Direction.EXPENSE:
            stats.total_expense_cents += tx.amount_cents
            bucket = stats.expense_by_category.setdefault(tx.category_id, 0)
            stats.expense_by_category[tx.category_id] = bucket + tx.amount_cents
        elif tx.direction == Direction.INCOME:
            stats.total_income_cents += tx.amount_cents
    return stats
