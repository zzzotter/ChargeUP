"""领域枚举。字段名与取值在第 1 天的接口约定中冻结，前后端保持一致。"""

from __future__ import annotations

from enum import Enum


class Source(str, Enum):
    """账单来源。"""

    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"
    SCREENSHOT = "SCREENSHOT"
    MANUAL = "MANUAL"

    @property
    def is_imported(self) -> bool:
        return self in (Source.ALIPAY, Source.WECHAT)


class Direction(str, Enum):
    """资金流向。TRANSFER（转账/不计收支）必须被统计排除。"""

    INCOME = "INCOME"
    EXPENSE = "EXPENSE"
    TRANSFER = "TRANSFER"


class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class AlertLevel(str, Enum):
    """预算预警级别：warnThreshold 默认 80%，alertThreshold 默认 100%。"""

    WARN = "WARN"
    ALERT = "ALERT"

    @property
    def rank(self) -> int:
        return 1 if self is AlertLevel.WARN else 2


class BudgetState(str, Enum):
    NORMAL = "NORMAL"
    WARN = "WARN"
    ALERT = "ALERT"


class ImportRowStatus(str, Enum):
    OK = "OK"
    EMPTY = "EMPTY"
    MISSING_COLUMNS = "MISSING_COLUMNS"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    INVALID_TIME = "INVALID_TIME"
    MISSING_EXTERNAL_ID = "MISSING_EXTERNAL_ID"
    MISSING_HEADER = "MISSING_HEADER"
    GARBLED_ROW = "GARBLED_ROW"


class CategorySource(str, Enum):
    """分类来源（前端 §7.3 冻结）：用户手动 > 用户规则 > 内置词库。"""

    RULE = "RULE"
    BUILTIN = "BUILTIN"
    USER = "USER"

    @property
    def label(self) -> str:
        return {
            CategorySource.RULE: "用户规则",
            CategorySource.BUILTIN: "内置词库",
            CategorySource.USER: "手动指定",
        }[self]


class AlertStatus(str, Enum):
    UNREAD = "UNREAD"
    READ = "READ"


class Persona(str, Enum):
    """AI 劝动人设（P2 使用，设置页先持久化）。"""

    DIRECT = "DIRECT"
    GENTLE = "GENTLE"
    RATIONAL = "RATIONAL"


class ModuleKey(str, Enum):
    """可整体下线的功能模块。"""

    WARDROBE = "wardrobe"
    INTENTS = "intents"
    FEEDBACK = "feedback"


class IntentStatus(str, Enum):
    CREATED = "CREATED"
    COOLING_DOWN = "COOLING_DOWN"
    DECIDED = "DECIDED"


class Decision(str, Enum):
    BOUGHT = "BOUGHT"
    ABANDONED = "ABANDONED"
    DEFERRED = "DEFERRED"
