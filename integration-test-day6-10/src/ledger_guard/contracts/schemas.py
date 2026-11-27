"""前后端接口契约 DTO（Pydantic v2）。

对齐第 1 天冻结的约定：
- 金额一律 amount_cents 整数分，严格拒绝浮点；
- 枚举与数据字典一致；
- 时间 ISO8601，软删除字段 deleted_at 可空。
"""
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

T = TypeVar("T")


class Source(str, Enum):
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"


class Direction(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"


class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")  # 禁止未声明字段，及早暴露契约偏差

    @field_validator("*", mode="before")
    @classmethod
    def _reject_float_amount(cls, value, info):
        # 任何金额字段都不接受浮点输入
        if info.field_name.endswith("_cents") and isinstance(value, float):
            raise ValueError(f"{info.field_name} 必须为整数分，禁止浮点: {value}")
        return value


class QuickEntryCreate(_StrictModel):
    """快捷录入请求体。"""

    source: Source
    amount_cents: int = Field(gt=0, description="金额，整数分")
    direction: Direction
    counterparty: str = Field(min_length=1, max_length=128)
    item_name: str = Field(min_length=1, max_length=128)
    transacted_at: datetime
    category_id: int | None = Field(default=None, gt=0)


class TransactionOut(_StrictModel):
    """交易列表/详情响应项。"""

    id: int = Field(gt=0)
    external_id: str | None = None
    source: Source
    amount_cents: int = Field(gt=0)
    direction: Direction
    counterparty: str = ""
    item_name: str = ""
    transacted_at: datetime
    status: str = ""
    category_id: int | None = None
    deleted_at: datetime | None = None


class PagedResponse(BaseModel, Generic[T]):
    """统一分页响应包。"""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)


class ErrorResponse(BaseModel):
    """统一错误响应体。"""

    code: str
    message: str
    details: dict | None = None


# ============ 第 6–10 天扩展契约（后端 OpenAPI 就绪后用于校验真实响应） ============

# ---- 第 6 天：导入结果 ----
class ImportResultOut(_StrictModel):
    inserted: int = Field(ge=0)
    duplicated: int = Field(ge=0)
    zero_skipped: int = Field(ge=0)
    rejected: int = Field(ge=0)


# ---- 第 7 天：分类规则 ----
class RuleFieldOut(str, Enum):
    ITEM_NAME = "ITEM_NAME"
    COUNTERPARTY = "COUNTERPARTY"


class RuleSourceOut(str, Enum):
    CUSTOM = "CUSTOM"
    SYSTEM = "SYSTEM"


class CategoryRuleOut(_StrictModel):
    rule_id: int = Field(gt=0)
    category_id: int = Field(gt=0)
    keyword: str = Field(min_length=1, max_length=64)
    field: RuleFieldOut = RuleFieldOut.ITEM_NAME
    priority: int = Field(ge=0)
    source: RuleSourceOut = RuleSourceOut.CUSTOM


# ---- 第 8 天：退款配对 ----
class RefundPairOut(_StrictModel):
    expense_external_id: str
    refund_external_id: str
    full_refund: bool


# ---- 第 9 天：月度统计 ----
class MonthlyStatsOut(_StrictModel):
    year: int = Field(ge=2000)
    month: int = Field(ge=1, le=12)
    total_expense_cents: int = Field(ge=0)
    total_income_cents: int = Field(ge=0)
    net_balance_cents: int
    transaction_count: int = Field(ge=0)


# ---- 第 10 天：预算与预警 ----
class AlertLevelOut(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class BudgetOut(_StrictModel):
    budget_id: int = Field(gt=0)
    limit_cents: int = Field(gt=0)
    category_id: int | None = None


class AlertEventOut(_StrictModel):
    budget_id: int = Field(gt=0)
    level: AlertLevelOut
    spent_cents: int = Field(ge=0)
    limit_cents: int = Field(gt=0)
