"""领域规则层（不依赖 Web/DB 框架，对齐六边形架构 Domain 层）。"""
from .classification import (
    CategoryRule,
    RuleField,
    RuleSource,
    match_category,
    apply_classification,
    ordered_rules,
)
from .refund import RefundPair, find_refund_pairs, is_transfer
from .stats import MonthlyStats, monthly_summary
from .budget import (
    Budget,
    AlertLevel,
    AlertEvent,
    evaluate_budget,
    reached_levels,
)
from .importer import ImportResult, import_report

__all__ = [
    "CategoryRule", "RuleField", "RuleSource", "match_category",
    "apply_classification", "ordered_rules",
    "RefundPair", "find_refund_pairs", "is_transfer",
    "MonthlyStats", "monthly_summary",
    "Budget", "AlertLevel", "AlertEvent", "evaluate_budget", "reached_levels",
    "ImportResult", "import_report",
]
