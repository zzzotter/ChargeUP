"""用例输入/输出对象（与 HTTP DTO 解耦）。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.domain.entities import Category, CategoryRule, ImportFailure
from app.domain.enums import CategorySource, Direction, Source

# ------------------------------------------------------------------ 交易


@dataclass(frozen=True)
class CreateTransactionCommand:
    """POST /transactions：服务端固定 source=MANUAL 并生成 external_id。"""

    amount_cents: int
    occurred_at: datetime
    direction: Direction = Direction.EXPENSE
    merchant: str = ""
    note: str = ""
    category_id: int | None = None


@dataclass(frozen=True)
class UpdateTransactionCommand:
    merchant: str | None = None
    amount_cents: int | None = None
    direction: Direction | None = None
    occurred_at: datetime | None = None
    note: str | None = None
    category_id: int | None = None
    clear_category: bool = False
    recategorize: bool = False


@dataclass(frozen=True)
class ScreenshotRow:
    """截图 OCR 校对后的单行候选（client_id 仅用于回传跳过/失败）。"""

    amount_cents: int
    occurred_at: datetime
    merchant: str = ""
    direction: Direction = Direction.EXPENSE
    note: str = ""
    category_id: int | None = None
    client_id: str | None = None


@dataclass(frozen=True)
class RowFailure:
    client_id: str | None
    reason: str


@dataclass(frozen=True)
class ScreenshotImportResult:
    created: int
    skipped: int
    failed: int
    failures: tuple[RowFailure, ...] = ()


@dataclass(frozen=True)
class BatchClassifyCommand:
    transaction_ids: tuple[int, ...]
    category_id: int
    rule_keyword: str | None = None


@dataclass(frozen=True)
class BatchFailure:
    transaction_id: int
    reason: str


@dataclass(frozen=True)
class BatchClassifyResult:
    updated: int
    failed: tuple[BatchFailure, ...] = ()
    rule_created: bool = False
    # 前端 BatchClassifyResult 要求直接返回沉淀后的规则对象
    rule: CategoryRule | None = None


@dataclass(frozen=True)
class DuplicateProbe:
    merchant: str
    amount_cents: int
    occurred_at: datetime


@dataclass(frozen=True)
class SuspectedDuplicate:
    transaction_id: int
    merchant: str
    amount_cents: int
    occurred_at: datetime
    external_id: str
    confidence: str = "HIGH"  # HIGH=商户可对应；LOW=商户缺失，仅同日同额


@dataclass(frozen=True)
class ReclassifyResult:
    scanned: int
    updated: int
    total: int = 0
    remaining: int = 0
    truncated: bool = False
    invalid_ids: tuple[int, ...] = ()


# ------------------------------------------------------------------ 导入


@dataclass(frozen=True)
class ImportReportData:
    import_id: int
    filename: str
    source: Source
    encoding: str
    recognized: int
    skipped_header_rows: int
    duplicated: int
    failed: int
    created: int
    duration_ms: int
    failures: tuple[ImportFailure, ...] = field(default_factory=tuple)


# ------------------------------------------------------------------ 统计


@dataclass(frozen=True)
class StatsSummaryData:
    month: str
    total_expense_cents: int
    total_income_cents: int
    excluded_refund_count: int
    excluded_transfer_count: int
    uncategorized_count: int
    # 前端 MonthSummary 还要求 duplicate；当前后端未持久化重复标记，恒为 0
    duplicate_count: int = 0


@dataclass(frozen=True)
class MonthlyTrendPoint:
    month: str
    expense_cents: int


@dataclass(frozen=True)
class CategoryStat:
    category_id: int | None
    name: str
    amount_cents: int
    ratio: float


# ------------------------------------------------------------------ 分类


@dataclass(frozen=True)
class CategoryView:
    category: Category
    rule_count: int
    transaction_count: int = 0


@dataclass(frozen=True)
class CategorySuggestion:
    category_id: int | None
    matched_by: CategorySource | None
    rule_keyword: str | None


@dataclass(frozen=True)
class RuleTestResult:
    matched: bool
    category_id: int | None = None
    category_name: str | None = None
    rule_id: int | None = None
    rule_keyword: str | None = None
    rule_source: CategorySource | None = None
