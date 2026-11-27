"""仓储实现：负责 ORM 模型 <-> 领域实体 的映射。"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.domain.entities import (
    Budget,
    BudgetEvent,
    Category,
    CategoryRule,
    ImportFailure,
    ImportRecord,
    Transaction,
    UserSettings,
)
from app.domain.enums import AlertLevel, CategorySource, CategoryType, Direction, Persona, Source
from app.domain.ports.repositories import TransactionFilter
from app.domain.time import as_utc, now_utc
from app.infrastructure.models import (
    AppSettingsModel,
    BudgetEventModel,
    BudgetModel,
    CategoryModel,
    CategoryRuleModel,
    ImportRecordModel,
    TransactionModel,
)

_CHUNK = 500


def _to_transaction(model: TransactionModel) -> Transaction:
    return Transaction(
        id=model.id,
        source=Source(model.source),
        external_id=model.external_id,
        amount_cents=model.amount_cents,
        direction=Direction(model.direction),
        occurred_at=as_utc(model.occurred_at),
        merchant=model.merchant or "",
        note=model.note or "",
        category_id=model.category_id,
        category_source=CategorySource(model.category_source) if model.category_source else None,
        refund_of_transaction_id=model.refund_of_transaction_id,
        deleted_at=as_utc(model.deleted_at) if model.deleted_at else None,
        created_at=as_utc(model.created_at) if model.created_at else None,
        updated_at=as_utc(model.updated_at) if model.updated_at else None,
    )


def _apply_transaction(model: TransactionModel, entity: Transaction) -> None:
    model.source = entity.source.value
    model.external_id = entity.external_id
    model.amount_cents = entity.amount_cents
    model.direction = entity.direction.value
    model.occurred_at = entity.occurred_at
    model.merchant = entity.merchant
    model.note = entity.note
    model.category_id = entity.category_id
    model.category_source = entity.category_source.value if entity.category_source else None
    model.refund_of_transaction_id = entity.refund_of_transaction_id
    model.deleted_at = entity.deleted_at
    if entity.updated_at is not None:
        model.updated_at = entity.updated_at


def _to_category(model: CategoryModel) -> Category:
    return Category(
        id=model.id,
        name=model.name,
        type=CategoryType(model.type),
        is_system=model.is_system,
        color=model.color,
        is_active=model.is_active,
    )


def _to_rule(model: CategoryRuleModel) -> CategoryRule:
    return CategoryRule(
        id=model.id,
        keyword=model.keyword,
        category_id=model.category_id,
        is_builtin=model.is_builtin,
        priority=model.priority,
    )


def _to_budget(model: BudgetModel) -> Budget:
    return Budget(
        id=model.id,
        period=model.period,
        amount_cents=model.amount_cents,
        warn_bps=model.warn_bps,
        alert_bps=model.alert_bps,
        created_at=as_utc(model.created_at) if model.created_at else None,
        updated_at=as_utc(model.updated_at) if model.updated_at else None,
    )


def _to_event(model: BudgetEventModel) -> BudgetEvent:
    return BudgetEvent(
        id=model.id,
        budget_id=model.budget_id,
        period=model.period,
        level=AlertLevel(model.level),
        spent_cents=model.spent_cents,
        threshold_bps=model.threshold_bps,
        read=model.read,
        created_at=as_utc(model.created_at) if model.created_at else now_utc(),
        revoked_at=as_utc(model.revoked_at) if model.revoked_at else None,
    )


def _to_import_record(model: ImportRecordModel) -> ImportRecord:
    failures = tuple(
        ImportFailure(
            row_number=int(item.get("rowNumber", 0)),
            reason=str(item.get("reason", "")),
            raw=item.get("raw"),
        )
        for item in (model.failures or [])
        if isinstance(item, dict)
    )
    return ImportRecord(
        id=model.id,
        filename=model.filename,
        source=Source(model.source),
        encoding=model.encoding,
        recognized=model.recognized,
        skipped_header_rows=model.skipped_header_rows,
        duplicated=model.duplicated,
        failed=model.failed,
        created=model.created,
        duration_ms=model.duration_ms,
        failures=failures,
        created_at=as_utc(model.created_at) if model.created_at else None,
    )


def _to_user_settings(model: AppSettingsModel) -> UserSettings:
    return UserSettings(
        id=model.id,
        hourly_rate_cents=model.hourly_rate_cents,
        persona=Persona(model.persona),
        module_wardrobe=model.module_wardrobe,
        module_intents=model.module_intents,
        module_feedback=model.module_feedback,
        updated_at=as_utc(model.updated_at) if model.updated_at else None,
    )


class SqlAlchemyTransactionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, transaction: Transaction) -> Transaction:
        model = TransactionModel()
        _apply_transaction(model, transaction)
        self._session.add(model)
        self._session.flush()
        return _to_transaction(model)

    def add_many(self, transactions: Sequence[Transaction]) -> list[Transaction]:
        models = []
        for transaction in transactions:
            model = TransactionModel()
            _apply_transaction(model, transaction)
            models.append(model)
        self._session.add_all(models)
        self._session.flush()
        return [_to_transaction(model) for model in models]

    def get(self, transaction_id: int, *, include_deleted: bool = False) -> Transaction | None:
        stmt = select(TransactionModel).where(TransactionModel.id == transaction_id)
        if not include_deleted:
            stmt = stmt.where(TransactionModel.deleted_at.is_(None))
        model = self._session.scalar(stmt)
        return _to_transaction(model) if model else None

    def update(self, transaction: Transaction) -> Transaction:
        if transaction.id is None:
            raise ValueError("更新交易必须带 id")
        model = self._session.get(TransactionModel, transaction.id)
        if model is None:
            raise ValueError(f"交易 {transaction.id} 不存在")
        _apply_transaction(model, transaction)
        self._session.flush()
        return _to_transaction(model)

    def search(self, filters: TransactionFilter) -> tuple[list[Transaction], int]:
        conditions = []
        if not filters.include_deleted:
            conditions.append(TransactionModel.deleted_at.is_(None))
        if filters.start:
            conditions.append(TransactionModel.occurred_at >= filters.start)
        if filters.end:
            conditions.append(TransactionModel.occurred_at < filters.end)
        if filters.category_id is not None:
            conditions.append(TransactionModel.category_id == filters.category_id)
        if filters.uncategorized:
            conditions.append(TransactionModel.category_id.is_(None))
        if filters.direction is not None:
            conditions.append(TransactionModel.direction == filters.direction.value)
        if filters.source is not None:
            conditions.append(TransactionModel.source == filters.source.value)
        if not filters.include_transfers:
            conditions.append(TransactionModel.direction != Direction.TRANSFER.value)
        if filters.keyword:
            # 用户输入的 % / _ / \ 按字面量匹配，避免通配符注入导致「搜 % 返回全部」
            keyword = filters.keyword.strip()
            for char in ("\\", "%", "_"):
                keyword = keyword.replace(char, f"\\{char}")
            like = f"%{keyword}%"
            conditions.append(
                or_(
                    TransactionModel.merchant.ilike(like, escape="\\"),
                    TransactionModel.note.ilike(like, escape="\\"),
                )
            )

        total = self._session.scalar(
            select(func.count(TransactionModel.id)).where(*conditions)
        ) or 0
        stmt = (
            select(TransactionModel)
            .where(*conditions)
            .order_by(*self._order_by(filters.sort))
            .limit(filters.limit)
            .offset(filters.offset)
        )
        models = self._session.scalars(stmt).all()
        return [_to_transaction(model) for model in models], int(total)

    @staticmethod
    def _order_by(sort: tuple[tuple[str, bool], ...]):
        columns = {
            "occurredAt": TransactionModel.occurred_at,
            "amount": TransactionModel.amount_cents,
            "createdAt": TransactionModel.created_at,
        }
        clauses = []
        for field, descending in sort:
            column = columns.get(field)
            if column is None:
                continue
            clauses.append(column.desc() if descending else column.asc())
        if not clauses:
            clauses.append(TransactionModel.occurred_at.desc())
        # 排序键始终追加 id，保证分页稳定
        clauses.append(TransactionModel.id.desc())
        return clauses

    def count_by_category(self, category_id: int) -> int:
        return int(
            self._session.scalar(
                select(func.count(TransactionModel.id)).where(
                    TransactionModel.category_id == category_id
                )
            )
            or 0
        )

    def counts_by_category(self) -> dict[int, int]:
        """未删除交易按分类分组计数（分类列表 transactionCount）。"""
        rows = self._session.execute(
            select(TransactionModel.category_id, func.count(TransactionModel.id))
            .where(
                TransactionModel.category_id.is_not(None),
                TransactionModel.deleted_at.is_(None),
            )
            .group_by(TransactionModel.category_id)
        ).all()
        return {int(category_id): int(count) for category_id, count in rows}

    def list_in_range(
        self, start: datetime, end: datetime, *, include_deleted: bool = False
    ) -> list[Transaction]:
        conditions = [TransactionModel.occurred_at >= start, TransactionModel.occurred_at < end]
        if not include_deleted:
            conditions.append(TransactionModel.deleted_at.is_(None))
        stmt = (
            select(TransactionModel)
            .where(*conditions)
            .order_by(TransactionModel.occurred_at.asc(), TransactionModel.id.asc())
        )
        return [_to_transaction(model) for model in self._session.scalars(stmt).all()]

    def existing_external_ids(self, source: Source, external_ids: Sequence[str]) -> set[str]:
        wanted = [value for value in dict.fromkeys(external_ids) if value]
        found: set[str] = set()
        for index in range(0, len(wanted), _CHUNK):
            chunk = wanted[index : index + _CHUNK]
            rows = self._session.scalars(
                select(TransactionModel.external_id).where(
                    TransactionModel.source == source.value,
                    TransactionModel.external_id.in_(chunk),
                )
            ).all()
            found.update(rows)
        return found


class SqlAlchemyCategoryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, category: Category) -> Category:
        model = CategoryModel(
            name=category.name,
            type=category.type.value,
            is_system=category.is_system,
            color=category.color,
            is_active=category.is_active,
        )
        self._session.add(model)
        self._session.flush()
        return _to_category(model)

    def get(self, category_id: int) -> Category | None:
        model = self._session.get(CategoryModel, category_id)
        return _to_category(model) if model else None

    def list(self) -> list[Category]:
        models = self._session.scalars(select(CategoryModel).order_by(CategoryModel.id)).all()
        return [_to_category(model) for model in models]

    def find_by_name(self, name: str) -> Category | None:
        model = self._session.scalar(select(CategoryModel).where(CategoryModel.name == name))
        return _to_category(model) if model else None

    def update(self, category: Category) -> Category:
        if category.id is None:
            raise ValueError("更新分类必须带 id")
        model = self._session.get(CategoryModel, category.id)
        if model is None:
            raise ValueError(f"分类 {category.id} 不存在")
        model.name = category.name
        model.type = category.type.value
        model.color = category.color
        model.is_active = category.is_active
        self._session.flush()
        return _to_category(model)

    def delete(self, category_id: int) -> bool:
        model = self._session.get(CategoryModel, category_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True


class SqlAlchemyRuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, rule: CategoryRule) -> CategoryRule:
        model = CategoryRuleModel(
            keyword=rule.keyword,
            category_id=rule.category_id,
            is_builtin=rule.is_builtin,
            priority=rule.priority,
        )
        self._session.add(model)
        self._session.flush()
        return _to_rule(model)

    def get(self, rule_id: int) -> CategoryRule | None:
        model = self._session.get(CategoryRuleModel, rule_id)
        return _to_rule(model) if model else None

    def list(self) -> list[CategoryRule]:
        models = self._session.scalars(
            select(CategoryRuleModel).order_by(
                CategoryRuleModel.is_builtin, CategoryRuleModel.priority.desc(), CategoryRuleModel.id
            )
        ).all()
        return [_to_rule(model) for model in models]

    def delete(self, rule_id: int) -> bool:
        model = self._session.get(CategoryRuleModel, rule_id)
        if model is None:
            return False
        self._session.delete(model)
        self._session.flush()
        return True

    def find_duplicate(self, keyword: str, category_id: int, is_builtin: bool) -> CategoryRule | None:
        model = self._session.scalar(
            select(CategoryRuleModel).where(
                CategoryRuleModel.keyword == keyword,
                CategoryRuleModel.category_id == category_id,
                CategoryRuleModel.is_builtin.is_(is_builtin),
            )
        )
        return _to_rule(model) if model else None

    def counts_by_category(self) -> dict[int, int]:
        rows = self._session.execute(
            select(CategoryRuleModel.category_id, func.count(CategoryRuleModel.id)).group_by(
                CategoryRuleModel.category_id
            )
        ).all()
        return {int(category_id): int(count) for category_id, count in rows}


class SqlAlchemyBudgetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _find(self, period: str) -> BudgetModel | None:
        return self._session.scalar(select(BudgetModel).where(BudgetModel.period == period))

    def upsert(self, budget: Budget) -> Budget:
        """先查后写，但并发下可能同时 INSERT；用保存点捕获唯一冲突后重读再更新。"""
        model = self._find(budget.period)
        if model is None:
            try:
                with self._session.begin_nested():
                    model = BudgetModel(period=budget.period, amount_cents=budget.amount_cents)
                    self._session.add(model)
                    self._session.flush()
            except IntegrityError:
                model = self._find(budget.period)
                if model is None:  # pragma: no cover - 唯一冲突后仍查不到属异常状态
                    raise
        model.amount_cents = budget.amount_cents
        model.warn_bps = budget.warn_bps
        model.alert_bps = budget.alert_bps
        model.updated_at = budget.updated_at or model.updated_at
        self._session.flush()
        return _to_budget(model)

    def get(self, period: str) -> Budget | None:
        model = self._find(period)
        return _to_budget(model) if model else None


class SqlAlchemyBudgetEventRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def sync(
        self,
        period: str,
        budget_id: int,
        active_levels: set[AlertLevel],
        spent_cents: int,
        moment: datetime,
        thresholds: dict[AlertLevel, int],
    ) -> list[BudgetEvent]:
        """把事件行同步为「当前生效级别」：越线激活、回落撤销，保留历史行。"""
        models = {
            model.level: model
            for model in self._session.scalars(
                select(BudgetEventModel).where(BudgetEventModel.period == period)
            ).all()
        }
        changed: list[BudgetEvent] = []

        for level in AlertLevel:
            model = models.get(level.value)
            threshold = thresholds.get(level, 0)
            if level in active_levels:
                if model is None:
                    model = BudgetEventModel(
                        budget_id=budget_id,
                        period=period,
                        level=level.value,
                        spent_cents=spent_cents,
                        threshold_bps=threshold,
                        read=False,
                        created_at=moment,
                    )
                    try:
                        with self._session.begin_nested():
                            self._session.add(model)
                            self._session.flush()
                    except IntegrityError:  # 并发下的唯一约束保护
                        model = self._session.scalar(
                            select(BudgetEventModel).where(
                                BudgetEventModel.period == period,
                                BudgetEventModel.level == level.value,
                            )
                        )
                        if model is None:  # pragma: no cover
                            continue
                        model.revoked_at = None
                        model.spent_cents = spent_cents
                        model.threshold_bps = threshold
                    changed.append(_to_event(model))
                else:
                    reactivating = model.revoked_at is not None
                    if reactivating:
                        model.revoked_at = None
                        # 重新越线视为新事件：重置已读，确保再次提醒
                        model.read = False
                    model.spent_cents = spent_cents
                    model.threshold_bps = threshold
                    changed.append(_to_event(model))
            elif model is not None and model.revoked_at is None:
                model.revoked_at = moment
                changed.append(_to_event(model))

        self._session.flush()
        return changed

    def list_for_period(self, period: str, *, active_only: bool = False) -> list[BudgetEvent]:
        statement = select(BudgetEventModel).where(BudgetEventModel.period == period)
        if active_only:
            statement = statement.where(BudgetEventModel.revoked_at.is_(None))
        models = self._session.scalars(
            statement.order_by(BudgetEventModel.created_at, BudgetEventModel.id)
        ).all()
        return [_to_event(model) for model in models]

    def get(self, event_id: int) -> BudgetEvent | None:
        model = self._session.get(BudgetEventModel, event_id)
        return _to_event(model) if model else None

    def update(self, event: BudgetEvent) -> BudgetEvent:
        if event.id is None:
            raise ValueError("更新预警事件必须带 id")
        model = self._session.get(BudgetEventModel, event.id)
        if model is None:
            raise ValueError(f"预警事件 {event.id} 不存在")
        model.read = event.read
        model.threshold_bps = event.threshold_bps
        model.spent_cents = event.spent_cents
        model.revoked_at = event.revoked_at
        self._session.flush()
        return _to_event(model)

    def search(
        self,
        *,
        level: AlertLevel | None = None,
        period: str | None = None,
        read: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[BudgetEvent], int]:
        conditions = []
        if level is not None:
            conditions.append(BudgetEventModel.level == level.value)
        if period is not None:
            conditions.append(BudgetEventModel.period == period)
        if read is not None:
            conditions.append(BudgetEventModel.read.is_(read))
        total = int(
            self._session.scalar(
                select(func.count(BudgetEventModel.id)).where(*conditions)
            )
            or 0
        )
        models = self._session.scalars(
            select(BudgetEventModel)
            .where(*conditions)
            .order_by(BudgetEventModel.created_at.desc(), BudgetEventModel.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return [_to_event(model) for model in models], total


class SqlAlchemyImportRecordRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, record: ImportRecord) -> ImportRecord:
        model = ImportRecordModel(
            filename=record.filename,
            source=record.source.value,
            encoding=record.encoding,
            recognized=record.recognized,
            skipped_header_rows=record.skipped_header_rows,
            duplicated=record.duplicated,
            failed=record.failed,
            created=record.created,
            duration_ms=record.duration_ms,
            failures=[failure.as_dict() for failure in record.failures],
            created_at=record.created_at or now_utc(),
        )
        self._session.add(model)
        self._session.flush()
        return _to_import_record(model)

    def get(self, record_id: int) -> ImportRecord | None:
        model = self._session.get(ImportRecordModel, record_id)
        return _to_import_record(model) if model else None

    def search(self, *, limit: int, offset: int) -> tuple[list[ImportRecord], int]:
        total = int(
            self._session.scalar(select(func.count(ImportRecordModel.id))) or 0
        )
        models = self._session.scalars(
            select(ImportRecordModel)
            .order_by(ImportRecordModel.created_at.desc(), ImportRecordModel.id.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return [_to_import_record(model) for model in models], total


class SqlAlchemySettingsRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self) -> UserSettings | None:
        model = self._session.scalar(select(AppSettingsModel).order_by(AppSettingsModel.id))
        return _to_user_settings(model) if model else None

    def save(self, settings: UserSettings) -> UserSettings:
        model = self._session.scalar(select(AppSettingsModel).order_by(AppSettingsModel.id))
        if model is None:
            model = AppSettingsModel()
            self._session.add(model)
        model.hourly_rate_cents = settings.hourly_rate_cents
        model.persona = settings.persona.value
        model.module_wardrobe = settings.module_wardrobe
        model.module_intents = settings.module_intents
        model.module_feedback = settings.module_feedback
        model.updated_at = settings.updated_at or now_utc()
        self._session.flush()
        return _to_user_settings(model)


def build_session_factory(engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, autoflush=False, future=True)
