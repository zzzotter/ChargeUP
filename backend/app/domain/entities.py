"""领域实体（纯 dataclass，不依赖 ORM）。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.enums import (
    AlertLevel,
    BudgetState,
    CategorySource,
    CategoryType,
    Direction,
    Persona,
    Source,
)
from app.domain.errors import ValidationError
from app.domain.money import require_positive_cents
from app.domain.time import as_utc, now_utc

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


@dataclass(slots=True)
class Transaction:
    """交易。amount_cents 恒为非负整数分，收支方向由 direction 表达。"""

    source: Source
    external_id: str
    amount_cents: int
    direction: Direction
    occurred_at: datetime
    merchant: str = ""
    note: str = ""
    category_id: int | None = None
    category_source: CategorySource | None = None
    refund_of_transaction_id: int | None = None
    id: int | None = None
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, Source):
            self.source = Source(self.source)
        if not isinstance(self.direction, Direction):
            self.direction = Direction(self.direction)
        self.amount_cents = require_positive_cents(self.amount_cents)
        self.external_id = (self.external_id or "").strip()
        if not self.external_id:
            raise ValidationError("external_id 不能为空")
        self.merchant = (self.merchant or "").strip()
        self.note = (self.note or "").strip()
        if self.category_id is None:
            # 未分类必然没有来源；避免出现「无分类却有来源」的矛盾数据
            self.category_source = None
        elif self.category_source is not None and not isinstance(
            self.category_source, CategorySource
        ):
            self.category_source = CategorySource(self.category_source)
        self.occurred_at = as_utc(self.occurred_at)
        if self.deleted_at is not None:
            self.deleted_at = as_utc(self.deleted_at)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def is_expense(self) -> bool:
        return self.direction is Direction.EXPENSE

    def soft_delete(self, at: datetime | None = None) -> None:
        if self.deleted_at is None:
            self.deleted_at = as_utc(at or now_utc())


@dataclass(slots=True)
class Category:
    name: str
    type: CategoryType
    is_system: bool = False
    color: str | None = None
    is_active: bool = True
    id: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.type, CategoryType):
            self.type = CategoryType(self.type)
        self.name = (self.name or "").strip()
        if not self.name:
            raise ValidationError("分类名称不能为空")
        if len(self.name) > 64:
            raise ValidationError("分类名称过长")
        self.color = (self.color or "").strip() or None
        if self.color is not None and len(self.color) > 16:
            raise ValidationError("分类颜色值过长")

    @property
    def is_builtin(self) -> bool:
        """内置分类（随系统播种）对应用户侧的 BUILTIN 来源。"""
        return self.is_system


@dataclass(slots=True)
class CategoryRule:
    """分类规则。用户规则优先级永远高于内置词库。"""

    keyword: str
    category_id: int
    is_builtin: bool = False
    priority: int = 0
    id: int | None = None

    def __post_init__(self) -> None:
        self.keyword = (self.keyword or "").strip()
        if not self.keyword:
            raise ValidationError("规则关键词不能为空")
        if len(self.keyword) > 64:
            raise ValidationError("规则关键词过长")
        if self.category_id is None:
            raise ValidationError("规则必须关联分类")


@dataclass(slots=True)
class Budget:
    """预算。阈值用基点（bps）存储，避免浮点误差：8000 = 80%。"""

    period: str
    amount_cents: int
    warn_bps: int = 8000
    alert_bps: int = 10000
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not _PERIOD_RE.match(self.period or ""):
            raise ValidationError("period 必须为 YYYY-MM")
        self.amount_cents = require_positive_cents(self.amount_cents)
        if self.amount_cents == 0:
            raise ValidationError("预算金额必须大于 0")
        for name, value in (("warn_bps", self.warn_bps), ("alert_bps", self.alert_bps)):
            if not 0 < value <= 10000:
                raise ValidationError(f"{name} 必须在 1..10000 之间")
        if self.warn_bps > self.alert_bps:
            raise ValidationError("warn 阈值不能高于 alert 阈值")


@dataclass(slots=True)
class BudgetEvent:
    """预警事件。(period, level) 唯一，同一周期同一级别只有一行。

    支出回落到阈值以下时写入 revoked_at（历史保留、不再生效）；
    再次越过阈值时清除 revoked_at 重新激活，避免重复插入或重复提醒。
    """

    budget_id: int
    period: str
    level: AlertLevel
    spent_cents: int
    created_at: datetime = field(default_factory=now_utc)
    threshold_bps: int = 0
    read: bool = False
    id: int | None = None
    revoked_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.level, AlertLevel):
            self.level = AlertLevel(self.level)
        self.spent_cents = require_positive_cents(self.spent_cents)
        if not 0 <= self.threshold_bps <= 10000:
            raise ValidationError("threshold_bps 必须在 0..10000 之间")
        self.created_at = as_utc(self.created_at)
        if self.revoked_at is not None:
            self.revoked_at = as_utc(self.revoked_at)

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def mark_read(self, read: bool = True) -> None:
        self.read = bool(read)


@dataclass(slots=True)
class BudgetReport:
    """预算执行情况（由领域服务计算，接口层直接序列化）。"""

    period: str
    amount_cents: int
    spent_cents: int
    remaining_cents: int
    used_bps: int
    warn_bps: int
    alert_bps: int
    state: BudgetState
    emitted_levels: tuple[AlertLevel, ...] = ()


@dataclass(frozen=True, slots=True)
class ImportFailure:
    """导入失败行（原始片段已脱敏）。"""

    row_number: int
    reason: str
    raw: str | None = None

    def as_dict(self) -> dict:
        payload = {"rowNumber": self.row_number, "reason": self.reason}
        if self.raw:
            payload["raw"] = self.raw
        return payload


@dataclass(slots=True)
class ImportRecord:
    """一次导入的历史记录（前端 P04 导入历史 / P05 报告详情）。"""

    filename: str
    source: Source
    recognized: int
    skipped_header_rows: int
    duplicated: int
    failed: int
    created: int
    duration_ms: int
    encoding: str = "utf-8"
    failures: tuple[ImportFailure, ...] = field(default_factory=tuple)
    id: int | None = None
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.source, Source):
            self.source = Source(self.source)
        for name in ("recognized", "skipped_header_rows", "duplicated", "failed", "created"):
            value = getattr(self, name)
            if value < 0:
                raise ValidationError(f"{name} 不能为负")
        if self.duration_ms < 0:
            raise ValidationError("duration_ms 不能为负")
        self.filename = (self.filename or "").strip() or "upload.csv"
        self.failures = tuple(self.failures)


@dataclass(slots=True)
class UserSettings:
    """用户设置（时薪、人设、模块开关）。hourly_rate_cents 为空表示不参与工时换算。"""

    hourly_rate_cents: int | None = None
    persona: Persona = Persona.RATIONAL
    module_wardrobe: bool = True
    module_intents: bool = True
    module_feedback: bool = True
    id: int | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.persona, Persona):
            self.persona = Persona(self.persona)
        if self.hourly_rate_cents is not None:
            self.hourly_rate_cents = require_positive_cents(self.hourly_rate_cents)

    def modules(self) -> dict[str, bool]:
        return {
            "wardrobe": self.module_wardrobe,
            "intents": self.module_intents,
            "feedback": self.module_feedback,
        }
