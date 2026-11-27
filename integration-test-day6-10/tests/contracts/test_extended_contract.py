"""第 6–10 天扩展 DTO 的契约约束（整数分、extra forbid、枚举）。"""
import pytest
from pydantic import ValidationError

from src.ledger_guard.contracts import (
    AlertEventOut,
    AlertLevelOut,
    BudgetOut,
    CategoryRuleOut,
    ImportResultOut,
    MonthlyStatsOut,
    RefundPairOut,
)


def test_import_result_dto():
    out = ImportResultOut(inserted=3, duplicated=2, zero_skipped=1, rejected=1)
    assert out.inserted == 3


def test_category_rule_dto_rejects_bad_enum():
    with pytest.raises(ValidationError):
        CategoryRuleOut(
            rule_id=1, category_id=2, keyword="咖啡",
            field="WRONG", priority=1, source="CUSTOM",
        )


def test_refund_pair_dto():
    pair = RefundPairOut(
        expense_external_id="e1", refund_external_id="r1", full_refund=True
    )
    assert pair.full_refund is True


def test_monthly_stats_dto_rejects_float_and_undeclared():
    with pytest.raises(ValidationError):
        MonthlyStatsOut(
            year=2026, month=11,
            total_expense_cents=12.34,  # float 被拒
            total_income_cents=0, net_balance_cents=-12, transaction_count=1,
        )
    with pytest.raises(ValidationError):
        MonthlyStatsOut(
            year=2026, month=11, total_expense_cents=100, total_income_cents=0,
            net_balance_cents=-100, transaction_count=1, extra_field="x",
        )


def test_budget_and_alert_dto():
    budget = BudgetOut(budget_id=1, limit_cents=10000)
    assert budget.category_id is None
    event = AlertEventOut(
        budget_id=1, level=AlertLevelOut.CRITICAL,
        spent_cents=10000, limit_cents=10000,
    )
    assert event.level == AlertLevelOut.CRITICAL
