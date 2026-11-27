"""路由聚合。"""

from app.interfaces.api.routers import (
    alerts,
    budget,
    categories,
    category_rules,
    health,
    imports,
    settings,
    stats,
    transactions,
)

__all__ = [
    "alerts",
    "budget",
    "categories",
    "category_rules",
    "health",
    "imports",
    "settings",
    "stats",
    "transactions",
]
