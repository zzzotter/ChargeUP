"""第 8 天：退款配对、转账排除与坏账单业务回归。"""
from src.ledger_guard.domain import find_refund_pairs, is_transfer
from src.ledger_guard.parser.models import Direction

from .helpers import make_tx


def test_full_refund_pair_within_window():
    expense = make_tx("e1", 1500, Direction.EXPENSE, item_name="益禾堂奶茶",
                      when="2026-11-01 10:00:00")
    refund = make_tx("r1", 1500, Direction.INCOME, item_name="益禾堂-退款",
                     when="2026-11-02 09:00:00")
    pairs = find_refund_pairs([expense, refund])
    assert len(pairs) == 1
    assert pairs[0].full_refund is True
    assert pairs[0].refund.external_id == "r1"


def test_partial_refund_marked():
    expense = make_tx("e2", 3000, Direction.EXPENSE, item_name="商品A",
                      when="2026-11-01 10:00:00")
    refund = make_tx("r2", 1000, Direction.INCOME, item_name="商品A-退款",
                     when="2026-11-03 10:00:00")
    pairs = find_refund_pairs([expense, refund])
    assert len(pairs) == 1
    assert pairs[0].full_refund is False


def test_refund_outside_window_not_paired():
    expense = make_tx("e3", 1500, Direction.EXPENSE, item_name="益禾堂奶茶",
                      when="2026-11-01 10:00:00")
    refund = make_tx("r3", 1500, Direction.INCOME, item_name="益禾堂-退款",
                     when="2026-11-10 10:00:00")  # 第 9 天，超过 7 天窗口
    assert find_refund_pairs([expense, refund]) == []


def test_refund_larger_than_expense_rejected():
    expense = make_tx("e4", 1000, Direction.EXPENSE, item_name="商品B",
                      when="2026-11-01 10:00:00")
    refund = make_tx("r4", 2000, Direction.INCOME, item_name="商品B-退款",
                     when="2026-11-02 10:00:00")
    assert find_refund_pairs([expense, refund]) == []


def test_unrelated_name_not_paired():
    expense = make_tx("e5", 1000, Direction.EXPENSE, item_name="咖啡",
                      when="2026-11-01 10:00:00")
    refund = make_tx("r5", 1000, Direction.INCOME, item_name="工资-退款",
                     when="2026-11-02 10:00:00")
    assert find_refund_pairs([expense, refund]) == []


def test_one_refund_used_once():
    expense1 = make_tx("e6", 1500, Direction.EXPENSE, item_name="益禾堂奶茶",
                       when="2026-11-01 10:00:00")
    expense2 = make_tx("e7", 1500, Direction.EXPENSE, item_name="益禾堂奶茶",
                       when="2026-11-01 11:00:00")
    refund = make_tx("r6", 1500, Direction.INCOME, item_name="益禾堂-退款",
                     when="2026-11-02 10:00:00")
    pairs = find_refund_pairs([expense1, expense2, refund])
    assert len(pairs) == 1  # 一笔退款不能同时配两笔消费


def test_transfer_excluded():
    transfer = make_tx("x1", 10000, Direction.TRANSFER, item_name="零钱充值")
    assert is_transfer(transfer) is True
    assert find_refund_pairs([transfer]) == []
