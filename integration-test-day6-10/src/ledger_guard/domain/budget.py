"""预算阈值与预警事件（第 10 天，纯领域逻辑，整数分）。

规则：
- 已用金额达到预算 80% 触发 WARNING，达到 100% 触发 CRITICAL；
- 同一预算同一等级只预警一次（幂等），重复评估不重复告警；
- 从 80% 升到 100% 时追加一次 CRITICAL；
- 阈值用整数交叉相乘比较，不使用 float。
"""
from dataclasses import dataclass
from enum import Enum


class AlertLevel(str, Enum):
    WARNING = "WARNING"     # 80%
    CRITICAL = "CRITICAL"   # 100%


@dataclass(frozen=True)
class Budget:
    budget_id: int
    limit_cents: int
    category_id: int | None = None  # None 表示总预算


@dataclass(frozen=True)
class AlertEvent:
    budget_id: int
    level: AlertLevel
    spent_cents: int
    limit_cents: int


def reached_levels(spent_cents: int, limit_cents: int) -> list[AlertLevel]:
    """根据当前已用金额，返回已经达到的全部等级（用整数比较）。"""
    levels: list[AlertLevel] = []
    # spent / limit >= 0.8  <=>  spent * 100 >= limit * 80
    if spent_cents * 100 >= limit_cents * 80:
        levels.append(AlertLevel.WARNING)
    if spent_cents >= limit_cents:
        levels.append(AlertLevel.CRITICAL)
    return levels


def evaluate_budget(
    budget: Budget,
    spent_cents: int,
    already_alerted: set[AlertLevel] | None = None,
) -> list[AlertEvent]:
    """仅返回本次新达到、且此前未告警的等级事件。"""
    already = already_alerted or set()
    events: list[AlertEvent] = []
    for level in reached_levels(spent_cents, budget.limit_cents):
        if level not in already:
            events.append(AlertEvent(
                budget_id=budget.budget_id,
                level=level,
                spent_cents=spent_cents,
                limit_cents=budget.limit_cents,
            ))
    return events
