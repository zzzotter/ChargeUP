"""仓储端口（Protocol）。领域层与用例层只依赖这里的抽象。"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from app.domain.entities import (
    Budget,
    BudgetEvent,
    Category,
    CategoryRule,
    ImportRecord,
    Transaction,
    UserSettings,
)
from app.domain.enums import AlertLevel, Direction, Source


@dataclass(frozen=True)
class TransactionFilter:
    """交易列表查询条件。sort 为 (字段名, 是否降序) 序列，字段名用 lowerCamelCase。"""

    start: datetime | None = None
    end: datetime | None = None
    category_id: int | None = None
    uncategorized: bool = False
    direction: Direction | None = None
    source: Source | None = None
    keyword: str | None = None
    include_deleted: bool = False
    include_transfers: bool = True
    sort: tuple[tuple[str, bool], ...] = ()
    limit: int = 50
    offset: int = 0


@runtime_checkable
class TransactionRepository(Protocol):
    def add(self, transaction: Transaction) -> Transaction: ...

    def add_many(self, transactions: Sequence[Transaction]) -> list[Transaction]: ...

    def get(self, transaction_id: int, *, include_deleted: bool = False) -> Transaction | None: ...

    def update(self, transaction: Transaction) -> Transaction: ...

    def search(self, filters: TransactionFilter) -> tuple[list[Transaction], int]: ...

    def list_in_range(
        self, start: datetime, end: datetime, *, include_deleted: bool = False
    ) -> list[Transaction]: ...

    def existing_external_ids(self, source: Source, external_ids: Sequence[str]) -> set[str]: ...

    def count_by_category(self, category_id: int) -> int:
        """引用该分类的交易数（含软删除），用于删除分类前的 409 判定。"""
        ...

    def counts_by_category(self) -> dict[int, int]:
        """按分类统计未删除交易数，用于分类列表的 transactionCount。"""
        ...


@runtime_checkable
class CategoryRepository(Protocol):
    def add(self, category: Category) -> Category: ...

    def get(self, category_id: int) -> Category | None: ...

    def list(self) -> list[Category]: ...

    def find_by_name(self, name: str) -> Category | None: ...

    def update(self, category: Category) -> Category: ...

    def delete(self, category_id: int) -> bool: ...


@runtime_checkable
class RuleRepository(Protocol):
    def add(self, rule: CategoryRule) -> CategoryRule: ...

    def get(self, rule_id: int) -> CategoryRule | None: ...

    def list(self) -> list[CategoryRule]: ...

    def delete(self, rule_id: int) -> bool: ...

    def find_duplicate(self, keyword: str, category_id: int, is_builtin: bool) -> CategoryRule | None: ...

    def counts_by_category(self) -> dict[int, int]: ...


@runtime_checkable
class BudgetRepository(Protocol):
    def upsert(self, budget: Budget) -> Budget: ...

    def get(self, period: str) -> Budget | None: ...


@runtime_checkable
class BudgetEventRepository(Protocol):
    def sync(
        self,
        period: str,
        budget_id: int,
        active_levels: set[AlertLevel],
        spent_cents: int,
        moment: datetime,
        thresholds: dict[AlertLevel, int],
    ) -> list[BudgetEvent]:
        """(period, level) 唯一；支出回落时撤销、再次越线时重新激活。"""
        ...

    def list_for_period(self, period: str, *, active_only: bool = False) -> list[BudgetEvent]:
        """active_only=True 时只返回当前生效事件（revoked_at 为空）。"""
        ...

    def get(self, event_id: int) -> BudgetEvent | None: ...

    def update(self, event: BudgetEvent) -> BudgetEvent: ...

    def search(
        self,
        *,
        level: AlertLevel | None = None,
        period: str | None = None,
        read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BudgetEvent], int]: ...


@runtime_checkable
class ImportRecordRepository(Protocol):
    def add(self, record: ImportRecord) -> ImportRecord: ...

    def get(self, record_id: int) -> ImportRecord | None: ...

    def search(self, *, limit: int, offset: int) -> tuple[list[ImportRecord], int]: ...


@runtime_checkable
class SettingsRepository(Protocol):
    def get(self) -> UserSettings | None: ...

    def save(self, settings: UserSettings) -> UserSettings: ...


@runtime_checkable
class UnitOfWork(Protocol):
    """事务边界。用例层通过 with 语句使用，领域层不感知数据库。"""

    transactions: TransactionRepository
    categories: CategoryRepository
    rules: RuleRepository
    budgets: BudgetRepository
    budget_events: BudgetEventRepository
    imports: ImportRecordRepository
    settings: SettingsRepository

    def __enter__(self) -> UnitOfWork: ...

    def __exit__(self, *exc_info: object) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
