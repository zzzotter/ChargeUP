"""预算双阈值判定（SRS F-P0-06）。

warnThreshold 默认 80%，alertThreshold 默认 100%；
同一周期同一级别只触发一次事件（幂等由仓储的唯一约束 + 本函数共同保证）。
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from app.domain.entities import Budget
from app.domain.enums import AlertLevel, BudgetState


@dataclass(frozen=True)
class BudgetEvaluation:
    period: str
    amount_cents: int
    spent_cents: int
    remaining_cents: int
    used_bps: int
    warn_bps: int
    alert_bps: int
    state: BudgetState
    levels_due: tuple[AlertLevel, ...]
    levels_to_emit: tuple[AlertLevel, ...]


def evaluate_budget(
    budget: Budget,
    spent_cents: int,
    emitted_levels: Sequence[AlertLevel] = (),
) -> BudgetEvaluation:
    if spent_cents < 0:
        raise ValueError("spent_cents 不能为负")

    used_bps = (spent_cents * 10000) // budget.amount_cents

    levels_due: list[AlertLevel] = []
    if used_bps >= budget.warn_bps:
        levels_due.append(AlertLevel.WARN)
    if used_bps >= budget.alert_bps:
        levels_due.append(AlertLevel.ALERT)

    emitted = set(emitted_levels)
    to_emit = tuple(level for level in levels_due if level not in emitted)

    if AlertLevel.ALERT in levels_due:
        state = BudgetState.ALERT
    elif AlertLevel.WARN in levels_due:
        state = BudgetState.WARN
    else:
        state = BudgetState.NORMAL

    return BudgetEvaluation(
        period=budget.period,
        amount_cents=budget.amount_cents,
        spent_cents=spent_cents,
        remaining_cents=max(budget.amount_cents - spent_cents, 0),
        used_bps=used_bps,
        warn_bps=budget.warn_bps,
        alert_bps=budget.alert_bps,
        state=state,
        levels_due=tuple(levels_due),
        levels_to_emit=to_emit,
    )
