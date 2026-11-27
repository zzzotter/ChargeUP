from __future__ import annotations

import pytest

from app.domain.entities import Budget
from app.domain.enums import AlertLevel, BudgetState
from app.domain.services.budget import evaluate_budget


def make_budget() -> Budget:
    return Budget(period="2026-11", amount_cents=100000)  # 1000.00 元


def test_below_warn_threshold():
    result = evaluate_budget(make_budget(), 79999)
    assert result.state is BudgetState.NORMAL
    assert result.levels_due == ()
    assert result.levels_to_emit == ()
    assert result.remaining_cents == 20001


def test_warn_exactly_at_eighty_percent():
    result = evaluate_budget(make_budget(), 80000)
    assert result.used_bps == 8000
    assert result.state is BudgetState.WARN
    assert result.levels_due == (AlertLevel.WARN,)
    assert result.levels_to_emit == (AlertLevel.WARN,)


def test_alert_at_full_amount_includes_both_levels():
    result = evaluate_budget(make_budget(), 100000)
    assert result.state is BudgetState.ALERT
    assert result.levels_due == (AlertLevel.WARN, AlertLevel.ALERT)
    assert result.levels_to_emit == (AlertLevel.WARN, AlertLevel.ALERT)
    assert result.remaining_cents == 0


def test_events_are_not_repeated():
    result = evaluate_budget(make_budget(), 130000, emitted_levels=[AlertLevel.WARN, AlertLevel.ALERT])
    assert result.state is BudgetState.ALERT
    assert result.levels_to_emit == ()
    assert result.remaining_cents == 0


def test_partial_emitted_levels():
    result = evaluate_budget(make_budget(), 100000, emitted_levels=[AlertLevel.WARN])
    assert result.levels_to_emit == (AlertLevel.ALERT,)


def test_custom_thresholds():
    budget = Budget(period="2026-11", amount_cents=100000, warn_bps=5000, alert_bps=9000)
    result = evaluate_budget(budget, 50000)
    assert result.levels_due == (AlertLevel.WARN,)


def test_invalid_budget_thresholds():
    from app.domain.errors import ValidationError

    with pytest.raises(ValidationError):
        Budget(period="2026-11", amount_cents=100000, warn_bps=9000, alert_bps=8000)
    with pytest.raises(ValidationError):
        Budget(period="2026-13", amount_cents=100000)
