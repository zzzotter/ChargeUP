"""第 9 天：月度统计口径与对账样例（数字可手算复核）。"""
from src.ledger_guard.domain import monthly_summary
from src.ledger_guard.parser.models import Direction

from .helpers import make_tx


def _november_dataset():
    return [
        make_tx("e1", 1000, Direction.EXPENSE, item_name="早餐", when="2026-11-02 09:00:00"),
        make_tx("e2", 2000, Direction.EXPENSE, item_name="午餐", when="2026-11-03 12:00:00"),
        make_tx("e3", 500, Direction.EXPENSE, item_name="零食", when="2026-11-04 15:00:00"),
        make_tx("i1", 5000, Direction.INCOME, item_name="退款", when="2026-11-05 10:00:00"),
        make_tx("x1", 10000, Direction.TRANSFER, item_name="零钱充值", when="2026-11-06 10:00:00"),
        make_tx("z1", 0, Direction.EXPENSE, item_name="信用借还", when="2026-11-07 10:00:00"),
        make_tx("old", 9999, Direction.EXPENSE, item_name="上月消费", when="2026-10-31 20:00:00"),
    ]


def test_monthly_totals_exclude_transfer_and_zero():
    stats = monthly_summary(_november_dataset(), 2026, 11)
    assert stats.total_expense_cents == 3500   # 1000+2000+500
    assert stats.total_income_cents == 5000
    assert stats.net_balance_cents == 1500    # 5000-3500
    assert stats.transaction_count == 4       # 3 支出 + 1 收入


def test_other_month_excluded():
    stats = monthly_summary(_november_dataset(), 2026, 10)
    assert stats.total_expense_cents == 9999
    assert stats.transaction_count == 1


def test_expense_grouped_by_category():
    txs = _november_dataset()
    txs[0].category_id = 1   # 早餐
    txs[1].category_id = 2   # 午餐
    txs[2].category_id = 1   # 零食
    stats = monthly_summary(txs, 2026, 11)
    assert stats.expense_by_category[1] == 1500  # 早餐 1000 + 零食 500
    assert stats.expense_by_category[2] == 2000
