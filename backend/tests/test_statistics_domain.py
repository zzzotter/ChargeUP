from __future__ import annotations

from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from app.domain.entities import Transaction
from app.domain.enums import Direction, Source
from app.domain.services.refunds import RefundPair
from app.domain.services.statistics import build_monthly_report, period_bounds

TZ = ZoneInfo("Asia/Shanghai")
BASE = datetime(2026, 11, 1, 4, 0, tzinfo=UTC)


def make(
    txn_id: int,
    cents: int,
    direction: Direction,
    days: float = 0,
    category_id: int | None = None,
    merchant: str = "商户",
) -> Transaction:
    return Transaction(
        id=txn_id,
        source=Source.MANUAL,
        external_id=f"T{txn_id}",
        amount_cents=cents,
        direction=direction,
        occurred_at=BASE + timedelta(days=days),
        merchant=merchant,
        category_id=category_id,
    )


def test_period_bounds_are_utc_and_local_month():
    start, end = period_bounds("2026-11", TZ)
    assert start == datetime(2026, 10, 31, 16, 0, tzinfo=UTC)
    assert end == datetime(2026, 11, 30, 16, 0, tzinfo=UTC)


def test_monthly_report_excludes_transfer_and_refund_pairs():
    transactions = [
        make(1, 3250, Direction.EXPENSE, days=0, category_id=1, merchant="星巴克"),
        make(2, 3250, Direction.INCOME, days=3, category_id=9, merchant="星巴克"),
        make(3, 19900, Direction.EXPENSE, days=4, category_id=2, merchant="淘宝"),
        make(4, 10000, Direction.TRANSFER, days=5),
    ]
    report = build_monthly_report(
        period="2026-11",
        transactions=transactions,
        refund_pairs=[RefundPair(original_id=1, refund_id=2)],
        category_names={1: "餐饮", 2: "购物", 9: "退款"},
        tzinfo=TZ,
    )

    assert report.expense_cents == 19900
    assert report.income_cents == 0
    assert report.refund_cents == 3250
    assert report.refunded_expense_cents == 3250
    assert report.transfer_excluded_cents == 10000
    assert report.counted_transactions == 1
    assert report.refund_pair_count == 1
    assert [item.category_name for item in report.by_category] == ["购物"]
    assert report.by_category[0].share_bps == 10000
    assert len(report.daily) == 30
    assert sum(point.expense_cents for point in report.daily) == report.expense_cents


def test_uncategorized_slice_is_named():
    report = build_monthly_report(
        period="2026-11",
        transactions=[make(1, 1200, Direction.EXPENSE, category_id=None)],
        refund_pairs=[],
        category_names={},
        tzinfo=TZ,
    )
    assert report.by_category[0].category_name == "未分类"
    assert report.by_category[0].category_id is None


def test_empty_month():
    report = build_monthly_report(
        period="2026-02",
        transactions=[],
        refund_pairs=[],
        category_names={},
        tzinfo=TZ,
    )
    assert report.expense_cents == 0
    assert report.by_category == ()
    assert len(report.daily) == 28
