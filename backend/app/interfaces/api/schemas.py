"""HTTP DTO（Pydantic v2）：对齐前端《页面清单》§7 契约。

约定：
- 字段一律 lowerCamelCase（alias_generator=to_camel），请求/响应同构；
- 金额一律整数「分」，字段名为 amount / totalExpense 等；
- id 对外序列化为字符串，入参路径仍用整数（Pydantic 宽松接受 "12"）；
- 时间 ISO 8601 带 +08:00 偏移。
"""

from __future__ import annotations

from datetime import datetime, tzinfo
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel

from app.application.dto import (
    BatchClassifyResult,
    CategorySuggestion,
    CategoryView,
    ImportReportData,
    RuleTestResult,
    StatsSummaryData,
)
from app.domain.entities import Budget, BudgetEvent, CategoryRule, ImportRecord, Transaction
from app.domain.enums import (
    AlertLevel,
    CategorySource,
    CategoryType,
    Direction,
    ImportRowStatus,
    Persona,
    Source,
)
from app.domain.money import MAX_AMOUNT_CENTS


class ApiModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


# --------------------------------------------------------------------- 通用


class ErrorBody(ApiModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class Page[T](ApiModel):
    items: list[T]
    page: int
    page_size: int
    total: int


# --------------------------------------------------------------------- 交易


TransactionInputDirection = Literal["EXPENSE", "INCOME"]


class TransactionInput(ApiModel):
    merchant: str = Field(min_length=1, max_length=255)
    amount: int = Field(gt=0, le=MAX_AMOUNT_CENTS, description="金额（整数分）")
    direction: TransactionInputDirection
    occurred_at: datetime
    category_id: int | None = None
    note: str | None = Field(default=None, max_length=1000)


class TransactionUpdateRequest(ApiModel):
    merchant: str | None = Field(default=None, max_length=255)
    amount: int | None = Field(default=None, gt=0, le=MAX_AMOUNT_CENTS)
    direction: Direction | None = None
    occurred_at: datetime | None = None
    note: str | None = Field(default=None, max_length=1000)
    category_id: int | None = Field(
        default=None, description="显式传 null 等价于清空分类"
    )
    clear_category: bool = False
    recategorize: bool = False

    @property
    def clears_category(self) -> bool:
        explicit_null = "category_id" in self.model_fields_set and self.category_id is None
        return bool(self.clear_category) or explicit_null

    @model_validator(mode="after")
    def _check_exclusive(self) -> TransactionUpdateRequest:
        chosen = sum([self.category_id is not None, self.clears_category, bool(self.recategorize)])
        if chosen > 1:
            raise ValueError("categoryId、清空分类、重新分类三者互斥，只能提供一个")
        return self


class TransactionRead(ApiModel):
    id: str
    source: Source
    external_id: str
    merchant: str
    amount: int = Field(description="金额（整数分）")
    direction: Direction
    category_id: str | None
    occurred_at: datetime
    note: str | None
    refund_of_transaction_id: str | None
    category_source: CategorySource | None
    deleted_at: datetime | None
    # 前端 Transaction.status：classified / uncategorized / refund / duplicate
    status: Literal["classified", "uncategorized", "refund", "duplicate"]
    updated_at: datetime | None


class BatchRuleInput(ApiModel):
    keyword: str = Field(min_length=1, max_length=64)


class BatchClassifyRequest(ApiModel):
    ids: list[int] = Field(min_length=1, max_length=500)
    category_id: int
    create_rule: BatchRuleInput | None = None


class BatchFailureRead(ApiModel):
    id: str
    reason: str


class BatchClassifyRead(ApiModel):
    updated: int
    failed: list[BatchFailureRead]
    rule_created: bool
    # 前端 BatchClassifyResult.rule：本次沉淀的规则（未建规则为 null）
    rule: RuleRead | None = None


class ScreenshotRowInput(ApiModel):
    client_id: str | None = None
    merchant: str = Field(default="", max_length=255)
    amount: int = Field(gt=0, le=MAX_AMOUNT_CENTS)
    direction: TransactionInputDirection = "EXPENSE"
    occurred_at: datetime
    category_id: int | None = None
    note: str | None = Field(default=None, max_length=1000)


class ScreenshotCandidatesRequest(ApiModel):
    rows: list[ScreenshotRowInput] = Field(default_factory=list, max_length=200)
    skipped_client_ids: list[str] = Field(default_factory=list, max_length=200)


class ScreenshotFailureRead(ApiModel):
    client_id: str | None
    reason: str


class ScreenshotCandidatesRead(ApiModel):
    created: int
    skipped: int
    failed: int
    failures: list[ScreenshotFailureRead]


class DuplicateProbeRequest(ApiModel):
    merchant: str = Field(default="", max_length=255)
    amount: int = Field(gt=0, le=MAX_AMOUNT_CENTS)
    occurred_at: datetime


class DuplicateProbeList(ApiModel):
    items: list[DuplicateProbeRequest] = Field(min_length=1, max_length=200)


class SuspectedDuplicateRead(ApiModel):
    transaction_id: str
    merchant: str
    amount: int
    occurred_at: datetime
    external_id: str
    confidence: str


class SuspectedDuplicateList(ApiModel):
    items: list[SuspectedDuplicateRead]


class ReclassifyRequest(ApiModel):
    transaction_ids: list[int] | None = Field(default=None, max_length=500)


class ReclassifyResultRead(ApiModel):
    scanned: int
    updated: int
    total: int
    remaining: int
    truncated: bool
    invalid_ids: list[str]


# --------------------------------------------------------------------- 分类


class CategoryCreateRequest(ApiModel):
    name: str = Field(min_length=1, max_length=64)
    type: CategoryType
    color: str | None = Field(default=None, max_length=16)


class CategoryUpdateRequest(ApiModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    color: str | None = Field(default=None, max_length=16)
    is_active: bool | None = None

    @property
    def update_color(self) -> bool:
        return "color" in self.model_fields_set


class CategoryRead(ApiModel):
    id: str
    name: str
    type: CategoryType
    color: str | None
    is_active: bool
    source: str = Field(description="BUILTIN=内置分类，USER=自定义分类")
    rule_count: int
    # 前端 CategoryWithCount 字段
    tone: Literal["coral", "mint", "lilac", "clay", "default"]
    is_builtin: bool
    transaction_count: int


class RuleCreateRequest(ApiModel):
    keyword: str = Field(min_length=1, max_length=64)
    category_id: int
    priority: int = 0


class RuleRead(ApiModel):
    id: str
    keyword: str
    category_id: str
    is_builtin: bool
    priority: int
    # 前端 CategoryRule.source：USER / BUILTIN
    source: Literal["USER", "BUILTIN"]


class CategorySuggestRead(ApiModel):
    category_id: str | None
    matched_by: CategorySource | None
    keyword: str | None
    # 兼容既有调用方：与 keyword 同值
    rule_keyword: str | None


class RuleTestRequest(ApiModel):
    name: str = Field(min_length=1, max_length=255)


class RuleTestRead(ApiModel):
    matched: bool
    category_id: str | None = None
    category_name: str | None = None
    rule_id: str | None = None
    rule_keyword: str | None = None
    rule_source: CategorySource | None = None
    # 前端 RuleTestResult 字段
    matched_by: Literal["RULE", "BUILTIN"] | None = None
    keyword: str | None = None
    source: Literal["USER", "BUILTIN"] | None = None


# --------------------------------------------------------------------- 导入


class ImportFailureRead(ApiModel):
    row_number: int
    reason: str
    raw: str | None = None


class ImportReportRead(ApiModel):
    import_id: str
    recognized: int
    skipped_header_rows: int
    duplicated: int
    failed: int
    created: int
    failures: list[ImportFailureRead]
    duration_ms: int


class ImportRecordRead(ApiModel):
    id: str
    filename: str
    source: Source
    recognized: int
    skipped_header_rows: int
    duplicated: int
    failed: int
    created: int
    duration_ms: int
    created_at: datetime


class ImportIssueRead(ApiModel):
    line_no: int
    status: ImportRowStatus
    detail: str
    raw: str


# --------------------------------------------------------------------- 统计


class StatsSummaryRead(ApiModel):
    month: str
    total_expense: int
    total_income: int
    excluded_refund_count: int
    excluded_transfer_count: int
    uncategorized_count: int
    # 前端 MonthSummary 字段
    uncategorized: int
    duplicate: int


class MonthlyTrendPointRead(ApiModel):
    month: str
    expense: int


class CategoryStatRead(ApiModel):
    category_id: str | None
    name: str
    amount: int
    ratio: float


# --------------------------------------------------------------------- 预算


class BudgetUpsertRequest(ApiModel):
    month: str | None = Field(default=None, pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    amount: int = Field(gt=0, le=MAX_AMOUNT_CENTS, description="月度预算（整数分）")
    warn_threshold: float | None = Field(default=None, gt=0, le=1)
    alert_threshold: float | None = Field(default=None, gt=0, le=1)


class BudgetRead(ApiModel):
    month: str
    amount: int
    warn_threshold: float
    alert_threshold: float


class AlertEventRead(ApiModel):
    id: str
    level: AlertLevel
    period: str
    threshold: float
    actual: int
    created_at: datetime
    read: bool
    # 前端 AlertEvent.budget：触发时的预算（分）
    budget: int


class AlertPatchRequest(ApiModel):
    read: bool = True


# --------------------------------------------------------------------- 设置


class ModulesRead(ApiModel):
    wardrobe: bool
    intents: bool
    feedback: bool


class ModulesUpdate(ApiModel):
    wardrobe: bool | None = None
    intents: bool | None = None
    feedback: bool | None = None


class SettingsRead(ApiModel):
    hourly_rate: int | None
    persona: Persona
    modules: ModulesRead


class SettingsUpdateRequest(ApiModel):
    hourly_rate: int | None = Field(default=None, ge=0, le=MAX_AMOUNT_CENTS)
    persona: Persona | None = None
    modules: ModulesUpdate | None = None

    @property
    def sets_hourly_rate(self) -> bool:
        return "hourly_rate" in self.model_fields_set or "hourlyRate" in self.model_fields_set


# --------------------------------------------------------------------- 映射

_TONE_CYCLE = ("coral", "mint", "lilac", "clay")
# 内置分类固定配色，避免重启或改库后颜色漂移
_TONE_BY_NAME = {
    "餐饮": "coral",
    "交通": "mint",
    "购物": "lilac",
    "居住": "clay",
    "娱乐": "default",
    "医疗": "default",
    "其他支出": "default",
    "工资": "mint",
    "退款": "mint",
    "其他收入": "default",
}


def category_tone(category) -> str:
    """把 color 或分类名映射到前端设计令牌（coral/mint/lilac/clay/default）。"""
    if category.color in _TONE_CYCLE or category.color == "default":
        return category.color
    if category.name in _TONE_BY_NAME:
        return _TONE_BY_NAME[category.name]
    return _TONE_CYCLE[(category.id or 0) % len(_TONE_CYCLE)]


def transaction_status(transaction: Transaction) -> str:
    """派生前端展示状态；后端未持久化 duplicate 标记。"""
    if transaction.refund_of_transaction_id is not None:
        return "refund"
    if transaction.category_id is None:
        return "uncategorized"
    return "classified"


def transaction_to_read(transaction: Transaction, tz: tzinfo) -> TransactionRead:
    return TransactionRead(
        id=str(transaction.id or 0),
        source=transaction.source,
        external_id=transaction.external_id,
        merchant=transaction.merchant,
        amount=transaction.amount_cents,
        direction=transaction.direction,
        category_id=str(transaction.category_id) if transaction.category_id is not None else None,
        occurred_at=transaction.occurred_at.astimezone(tz),
        note=transaction.note or None,
        refund_of_transaction_id=(
            str(transaction.refund_of_transaction_id)
            if transaction.refund_of_transaction_id is not None
            else None
        ),
        category_source=transaction.category_source,
        deleted_at=transaction.deleted_at.astimezone(tz) if transaction.deleted_at else None,
        status=transaction_status(transaction),
        updated_at=transaction.updated_at.astimezone(tz) if transaction.updated_at else None,
    )


def category_to_read(view: CategoryView) -> CategoryRead:
    category = view.category
    return CategoryRead(
        id=str(category.id or 0),
        name=category.name,
        type=category.type,
        color=category.color,
        is_active=category.is_active,
        source="BUILTIN" if category.is_builtin else "USER",
        rule_count=view.rule_count,
        tone=category_tone(category),
        is_builtin=category.is_builtin,
        transaction_count=view.transaction_count,
    )


def rule_to_read(rule: CategoryRule) -> RuleRead:
    return RuleRead(
        id=str(rule.id or 0),
        keyword=rule.keyword,
        category_id=str(rule.category_id),
        is_builtin=rule.is_builtin,
        priority=rule.priority,
        source="BUILTIN" if rule.is_builtin else "USER",
    )


def suggestion_to_read(item: CategorySuggestion) -> CategorySuggestRead:
    return CategorySuggestRead(
        category_id=str(item.category_id) if item.category_id is not None else None,
        matched_by=item.matched_by,
        keyword=item.rule_keyword,
        rule_keyword=item.rule_keyword,
    )


def rule_test_to_read(result: RuleTestResult) -> RuleTestRead:
    is_builtin = result.rule_source is CategorySource.BUILTIN
    has_rule = result.rule_source is not None
    return RuleTestRead(
        matched=result.matched,
        category_id=str(result.category_id) if result.category_id is not None else None,
        category_name=result.category_name,
        rule_id=str(result.rule_id) if result.rule_id is not None else None,
        rule_keyword=result.rule_keyword,
        rule_source=result.rule_source,
        matched_by=("BUILTIN" if is_builtin else "RULE") if has_rule else None,
        keyword=result.rule_keyword,
        source=("BUILTIN" if is_builtin else "USER") if has_rule else None,
    )


def batch_result_to_read(result: BatchClassifyResult) -> BatchClassifyRead:
    return BatchClassifyRead(
        updated=result.updated,
        failed=[
            BatchFailureRead(id=str(item.transaction_id), reason=item.reason)
            for item in result.failed
        ],
        rule_created=result.rule_created,
        rule=rule_to_read(result.rule) if result.rule is not None else None,
    )


def import_report_to_read(report: ImportReportData) -> ImportReportRead:
    return ImportReportRead(
        import_id=str(report.import_id),
        recognized=report.recognized,
        skipped_header_rows=report.skipped_header_rows,
        duplicated=report.duplicated,
        failed=report.failed,
        created=report.created,
        failures=[
            ImportFailureRead(row_number=item.row_number, reason=item.reason, raw=item.raw)
            for item in report.failures
        ],
        duration_ms=report.duration_ms,
    )


def import_record_to_read(record: ImportRecord, tz: tzinfo) -> ImportRecordRead:
    return ImportRecordRead(
        id=str(record.id or 0),
        filename=record.filename,
        source=record.source,
        recognized=record.recognized,
        skipped_header_rows=record.skipped_header_rows,
        duplicated=record.duplicated,
        failed=record.failed,
        created=record.created,
        duration_ms=record.duration_ms,
        created_at=(record.created_at or datetime.now(tz)).astimezone(tz),
    )


def stats_summary_to_read(data: StatsSummaryData) -> StatsSummaryRead:
    return StatsSummaryRead(
        month=data.month,
        total_expense=data.total_expense_cents,
        total_income=data.total_income_cents,
        excluded_refund_count=data.excluded_refund_count,
        excluded_transfer_count=data.excluded_transfer_count,
        uncategorized_count=data.uncategorized_count,
        uncategorized=data.uncategorized_count,
        duplicate=data.duplicate_count,
    )


def budget_to_read(budget: Budget) -> BudgetRead:
    return BudgetRead(
        month=budget.period,
        amount=budget.amount_cents,
        warn_threshold=round(budget.warn_bps / 10000, 4),
        alert_threshold=round(budget.alert_bps / 10000, 4),
    )


def alert_to_read(event: BudgetEvent, tz: tzinfo, budget_cents: int = 0) -> AlertEventRead:
    return AlertEventRead(
        id=str(event.id or 0),
        level=event.level,
        period=event.period,
        threshold=round(event.threshold_bps / 10000, 4),
        actual=event.spent_cents,
        created_at=event.created_at.astimezone(tz),
        read=event.read,
        budget=budget_cents,
    )


# BatchClassifyRead 引用后定义的 RuleRead，模块加载完成后重建一次模型
BatchClassifyRead.model_rebuild()
