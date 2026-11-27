from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.entities import Transaction
from app.domain.enums import Direction, Source
from app.domain.services.refunds import detect_refund_pairs, linked_transaction_ids

BASE = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)


def make(
    txn_id: int,
    cents: int,
    direction: Direction,
    days: float = 0,
    merchant: str = "星巴克",
) -> Transaction:
    return Transaction(
        id=txn_id,
        source=Source.MANUAL,
        external_id=f"T{txn_id}",
        amount_cents=cents,
        direction=direction,
        occurred_at=BASE + timedelta(days=days),
        merchant=merchant,
    )


def test_pairs_within_seven_days():
    expense = make(1, 3250, Direction.EXPENSE, days=0)
    refund = make(2, 3250, Direction.INCOME, days=3)
    pairs = detect_refund_pairs([expense, refund])
    assert [(p.original_id, p.refund_id) for p in pairs] == [(1, 2)]
    assert linked_transaction_ids(pairs) == {1, 2}


def test_no_pair_beyond_window():
    expense = make(1, 3250, Direction.EXPENSE, days=0)
    refund = make(2, 3250, Direction.INCOME, days=8)
    assert detect_refund_pairs([expense, refund]) == []


def test_refund_before_expense_is_not_paired():
    refund = make(2, 3250, Direction.INCOME, days=0)
    expense = make(1, 3250, Direction.EXPENSE, days=1)
    assert detect_refund_pairs([refund, expense]) == []


def test_prefers_same_merchant():
    same_amount_a = make(1, 3250, Direction.EXPENSE, days=0, merchant="星巴克")
    same_amount_b = make(2, 3250, Direction.EXPENSE, days=1, merchant="瑞幸")
    refund = make(3, 3250, Direction.INCOME, days=2, merchant="瑞幸咖啡")
    pairs = detect_refund_pairs([same_amount_a, same_amount_b, refund])
    assert [(p.original_id, p.refund_id) for p in pairs] == [(2, 3)]


def test_one_expense_only_matched_once():
    expense = make(1, 3250, Direction.EXPENSE, days=0)
    refund_a = make(2, 3250, Direction.INCOME, days=1)
    refund_b = make(3, 3250, Direction.INCOME, days=2)
    pairs = detect_refund_pairs([expense, refund_a, refund_b])
    assert len(pairs) == 1


def test_existing_explicit_link_is_respected():
    expense = make(1, 5000, Direction.EXPENSE, days=0)
    refund = make(2, 5000, Direction.INCOME, days=2)
    refund.refund_of_transaction_id = 1
    pairs = detect_refund_pairs([expense, refund])
    assert [(p.original_id, p.refund_id) for p in pairs] == [(1, 2)]
