"""第 10 天：80%/100% 阈值与重复触发幂等。"""
from src.ledger_guard.domain import AlertLevel, Budget, evaluate_budget

BUDGET = Budget(budget_id=1, limit_cents=10000)


def test_below_threshold_no_alert():
    assert evaluate_budget(BUDGET, 7000) == []
    assert evaluate_budget(BUDGET, 7999) == []  # 79.99%，未到 80%


def test_exactly_80_percent_warning():
    events = evaluate_budget(BUDGET, 8000)
    assert len(events) == 1
    assert events[0].level == AlertLevel.WARNING


def test_100_percent_emits_warning_and_critical():
    events = evaluate_budget(BUDGET, 10000)
    levels = {e.level for e in events}
    assert levels == {AlertLevel.WARNING, AlertLevel.CRITICAL}


def test_same_level_not_re_alerted():
    first = evaluate_budget(BUDGET, 8000, set())
    assert len(first) == 1
    # 已记录 WARNING 后再次评估，不重复告警
    second = evaluate_budget(BUDGET, 8500, {AlertLevel.WARNING})
    assert second == []


def test_escalation_only_adds_critical():
    events = evaluate_budget(BUDGET, 10000, {AlertLevel.WARNING})
    assert len(events) == 1
    assert events[0].level == AlertLevel.CRITICAL


def test_over_limit_still_critical():
    events = evaluate_budget(BUDGET, 12000, set())
    assert AlertLevel.CRITICAL in {e.level for e in events}
