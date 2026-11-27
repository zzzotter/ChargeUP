"""交易用例：新建、列表、详情、编辑、软删除/恢复、批量归类、截图入账、收件箱。"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.application.categorization import auto_categorize, resolve_category
from app.application.dto import (
    BatchClassifyCommand,
    BatchClassifyResult,
    BatchFailure,
    CreateTransactionCommand,
    DuplicateProbe,
    ReclassifyResult,
    RowFailure,
    ScreenshotImportResult,
    ScreenshotRow,
    SuspectedDuplicate,
    UpdateTransactionCommand,
)
from app.application.notifications import PeriodHook, notify_periods
from app.application.periods import local_date, local_day_bounds, to_utc
from app.domain.entities import CategoryRule, Transaction
from app.domain.enums import CategorySource, Direction, Source
from app.domain.errors import (
    DomainError,
    DuplicateResourceError,
    HardDeleteForbidden,
    NotFoundError,
    ValidationError,
)
from app.domain.ports.clock import Clock
from app.domain.ports.repositories import TransactionFilter, UnitOfWork
from app.domain.services.categorization import normalize_text

LOGGER = logging.getLogger(__name__)

_MANUAL_PREFIX = "MAN-"
_SCREENSHOT_PREFIX = "SCR-"


class TransactionService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        tz: ZoneInfo,
        on_change: Sequence[PeriodHook] = (),
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._tz = tz
        self._on_change = tuple(on_change)

    # ------------------------------------------------------------------ 创建

    def create(self, command: CreateTransactionCommand) -> Transaction:
        if command.amount_cents <= 0:
            raise ValidationError("金额必须大于 0")
        occurred_at = to_utc(command.occurred_at, self._tz)
        with self._uow_factory() as uow:
            decision = resolve_category(
                uow, command.merchant, command.category_id, command.direction
            )
            transaction = Transaction(
                source=Source.MANUAL,
                external_id=f"{_MANUAL_PREFIX}{uuid4().hex}",
                amount_cents=command.amount_cents,
                direction=command.direction,
                occurred_at=occurred_at,
                merchant=command.merchant,
                note=command.note,
                category_id=decision.category_id,
                category_source=decision.source,
                created_at=self._clock.now(),
                updated_at=self._clock.now(),
            )
            saved = uow.transactions.add(transaction)
            uow.commit()

        notify_periods(self._on_change, [saved.occurred_at], self._tz)
        return saved

    def create_screenshot(
        self,
        rows: Sequence[ScreenshotRow],
        skipped_client_ids: Sequence[str] = (),
    ) -> ScreenshotImportResult:
        """截图候选批量入账：source=SCREENSHOT，系统生成 external_id。"""
        skipped_ids = {item for item in skipped_client_ids if item}
        moments = []
        failures: list[RowFailure] = []
        created = 0
        with self._uow_factory() as uow:
            for row in rows:
                if row.client_id and row.client_id in skipped_ids:
                    continue
                if row.amount_cents <= 0:
                    failures.append(RowFailure(row.client_id, "金额必须大于 0"))
                    continue
                try:
                    decision = resolve_category(
                        uow, row.merchant, row.category_id, row.direction
                    )
                except DomainError as exc:  # 单行失败不影响整批
                    failures.append(RowFailure(row.client_id, exc.message))
                    continue
                transaction = Transaction(
                    source=Source.SCREENSHOT,
                    external_id=f"{_SCREENSHOT_PREFIX}{uuid4().hex}",
                    amount_cents=row.amount_cents,
                    direction=row.direction,
                    occurred_at=to_utc(row.occurred_at, self._tz),
                    merchant=row.merchant,
                    note=row.note,
                    category_id=decision.category_id,
                    category_source=decision.source,
                    created_at=self._clock.now(),
                    updated_at=self._clock.now(),
                )
                uow.transactions.add(transaction)
                moments.append(transaction.occurred_at)
                created += 1
            uow.commit()

        if moments:
            notify_periods(self._on_change, moments, self._tz)
        return ScreenshotImportResult(
            created=created,
            skipped=len(skipped_ids),
            failed=len(failures),
            failures=tuple(failures),
        )

    # ------------------------------------------------------------------ 查询

    def list(self, filters: TransactionFilter) -> tuple[list[Transaction], int]:
        with self._uow_factory() as uow:
            return uow.transactions.search(filters)

    def get(self, transaction_id: int, *, include_deleted: bool = False) -> Transaction:
        with self._uow_factory() as uow:
            transaction = uow.transactions.get(transaction_id, include_deleted=include_deleted)
        if transaction is None:
            raise NotFoundError(f"交易 {transaction_id} 不存在")
        return transaction

    def inbox(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort: tuple[tuple[str, bool], ...] = (),
    ) -> tuple[list[Transaction], int]:
        """待分类收件箱：转账不参与分类，不进入收件箱。"""
        return self.list(
            TransactionFilter(
                uncategorized=True,
                include_transfers=False,
                sort=sort,
                limit=page_size,
                offset=(page - 1) * page_size,
            )
        )

    # ------------------------------------------------------------------ 修改

    def update(self, transaction_id: int, command: UpdateTransactionCommand) -> Transaction:
        with self._uow_factory() as uow:
            transaction = uow.transactions.get(transaction_id)
            if transaction is None or transaction.is_deleted:
                raise NotFoundError(f"交易 {transaction_id} 不存在")

            # 互斥参数：避免 clear_category + recategorize 时静默忽略后者
            choices = [
                command.category_id is not None,
                bool(command.clear_category),
                bool(command.recategorize),
            ]
            if sum(choices) > 1:
                raise ValidationError(
                    "categoryId、清空分类、重新分类三者互斥，只能提供一个"
                )

            original_moment = transaction.occurred_at

            if command.amount_cents is not None:
                if command.amount_cents <= 0:
                    raise ValidationError("金额必须大于 0")
                transaction.amount_cents = command.amount_cents
            if command.direction is not None:
                transaction.direction = Direction(command.direction)
                # 方向改变后原分类可能失效：未显式指定新分类时清空，避免收入挂支出分类
                if command.category_id is None and not command.recategorize:
                    self._drop_incompatible_category(uow, transaction)
            if command.merchant is not None:
                transaction.merchant = command.merchant.strip()
            if command.note is not None:
                transaction.note = command.note.strip()
            if command.occurred_at is not None:
                transaction.occurred_at = to_utc(command.occurred_at, self._tz)

            if command.clear_category:
                transaction.category_id = None
                transaction.category_source = None
            elif command.category_id is not None:
                decision = resolve_category(
                    uow, transaction.merchant, command.category_id, transaction.direction
                )
                transaction.category_id = decision.category_id
                transaction.category_source = decision.source
            elif command.recategorize:
                decision = auto_categorize(uow, transaction.merchant, transaction.direction)
                transaction.category_id = decision.category_id
                transaction.category_source = decision.source

            transaction.updated_at = self._clock.now()
            saved = uow.transactions.update(transaction)
            uow.commit()

        notify_periods(self._on_change, [original_moment, saved.occurred_at], self._tz)
        return saved

    def soft_delete(self, transaction_id: int, *, hard: bool = False) -> None:
        """财务记录禁止物理删除，只写 deleted_at。"""
        if hard:
            raise HardDeleteForbidden("财务记录禁止物理删除，仅支持移入回收（软删除）")
        with self._uow_factory() as uow:
            transaction = uow.transactions.get(transaction_id)
            if transaction is None or transaction.is_deleted:
                raise NotFoundError(f"交易 {transaction_id} 不存在")
            transaction.soft_delete(self._clock.now())
            transaction.updated_at = transaction.deleted_at
            saved = uow.transactions.update(transaction)
            uow.commit()

        notify_periods(self._on_change, [saved.occurred_at], self._tz)

    def restore(self, transaction_id: int) -> Transaction:
        with self._uow_factory() as uow:
            transaction = uow.transactions.get(transaction_id, include_deleted=True)
            if transaction is None:
                raise NotFoundError(f"交易 {transaction_id} 不存在")
            transaction.deleted_at = None
            transaction.updated_at = self._clock.now()
            saved = uow.transactions.update(transaction)
            uow.commit()

        notify_periods(self._on_change, [saved.occurred_at], self._tz)
        return saved

    def batch_classify(self, command: BatchClassifyCommand) -> BatchClassifyResult:
        """批量归类；可选同时沉淀一条用户关键词规则（规则冲突时 409）。"""
        ids = tuple(dict.fromkeys(command.transaction_ids))
        if not ids:
            raise ValidationError("ids 不能为空")

        moments: list = []
        failures: list[BatchFailure] = []
        updated = 0
        rule_created = False
        created_rule: CategoryRule | None = None

        with self._uow_factory() as uow:
            category = uow.categories.get(command.category_id)
            if category is None:
                raise NotFoundError(f"分类 {command.category_id} 不存在")

            if command.rule_keyword:
                keyword = command.rule_keyword.strip()
                if not keyword:
                    raise ValidationError("规则关键词不能为空")
                if uow.rules.find_duplicate(keyword, category.id or 0, is_builtin=False) is not None:
                    raise DuplicateResourceError(f"规则「{keyword}」已存在")

            for transaction_id in ids:
                transaction = uow.transactions.get(transaction_id)
                if transaction is None or transaction.is_deleted:
                    failures.append(BatchFailure(transaction_id, "记录不存在或已移入回收"))
                    continue
                if transaction.direction is Direction.TRANSFER:
                    failures.append(BatchFailure(transaction_id, "转账不参与分类"))
                    continue
                if category.type.value != transaction.direction.value:
                    failures.append(BatchFailure(transaction_id, "分类类型与收支方向不一致"))
                    continue
                transaction.category_id = category.id
                transaction.category_source = CategorySource.USER
                transaction.updated_at = self._clock.now()
                uow.transactions.update(transaction)
                moments.append(transaction.occurred_at)
                updated += 1

            if command.rule_keyword and updated:
                created_rule = uow.rules.add(
                    CategoryRule(
                        keyword=command.rule_keyword.strip(),
                        category_id=category.id or 0,
                        is_builtin=False,
                    )
                )
                rule_created = True

            uow.commit()

        if moments:
            notify_periods(self._on_change, moments, self._tz)
        return BatchClassifyResult(
            updated=updated,
            failed=tuple(failures),
            rule_created=rule_created,
            rule=created_rule,
        )

    def reclassify(self, transaction_ids: Sequence[int] | None = None) -> ReclassifyResult:
        """重跑分类规则（默认只处理待分类收件箱，单次最多 500 条）。"""
        scanned = 0
        updated = 0
        total = 0
        remaining = 0
        invalid_ids: list[int] = []

        with self._uow_factory() as uow:
            if transaction_ids:
                unique_ids = list(dict.fromkeys(transaction_ids))
                total = len(unique_ids)
                targets = []
                for tid in unique_ids:
                    txn = uow.transactions.get(tid)
                    if txn is None or txn.is_deleted:
                        invalid_ids.append(tid)
                        continue
                    targets.append(txn)
            else:
                targets, total = uow.transactions.search(
                    TransactionFilter(uncategorized=True, include_transfers=False, limit=500)
                )
                remaining = max(0, total - len(targets))

            for transaction in targets:
                scanned += 1
                if transaction.category_id is not None:
                    continue
                decision = auto_categorize(uow, transaction.merchant, transaction.direction)
                if decision.category_id is not None:
                    transaction.category_id = decision.category_id
                    transaction.category_source = decision.source
                    transaction.updated_at = self._clock.now()
                    uow.transactions.update(transaction)
                    updated += 1
            uow.commit()

        return ReclassifyResult(
            scanned=scanned,
            updated=updated,
            total=total,
            remaining=remaining,
            truncated=remaining > 0,
            invalid_ids=tuple(invalid_ids),
        )

    # -------------------------------------------------------------- 弱指纹查重

    def find_suspected_duplicates(self, probes: Sequence[DuplicateProbe]) -> list[SuspectedDuplicate]:
        """截图导入的弱指纹查重：同日期 + 同金额，商户可对应为 HIGH，缺商户信息为 LOW。"""
        results: list[SuspectedDuplicate] = []
        with self._uow_factory() as uow:
            for probe in probes:
                moment = to_utc(probe.occurred_at, self._tz)
                day = local_date(moment, self._tz)
                start, end = local_day_bounds(day, self._tz)
                same_day = uow.transactions.list_in_range(start, end)
                probe_merchant = normalize_text(probe.merchant)
                for candidate in same_day:
                    if candidate.amount_cents != probe.amount_cents:
                        continue
                    if local_date(candidate.occurred_at, self._tz) != day:
                        continue
                    candidate_merchant = normalize_text(candidate.merchant)
                    if probe_merchant and candidate_merchant:
                        if (
                            probe_merchant != candidate_merchant
                            and probe_merchant not in candidate_merchant
                            and candidate_merchant not in probe_merchant
                        ):
                            continue
                        confidence = "HIGH"
                    else:
                        confidence = "LOW"
                    if candidate.id is None:
                        continue
                    results.append(
                        SuspectedDuplicate(
                            transaction_id=candidate.id,
                            merchant=candidate.merchant,
                            amount_cents=candidate.amount_cents,
                            occurred_at=candidate.occurred_at,
                            external_id=candidate.external_id,
                            confidence=confidence,
                        )
                    )
        return results

    # ------------------------------------------------------------------ 内部

    @staticmethod
    def _drop_incompatible_category(uow: UnitOfWork, transaction: Transaction) -> None:
        """方向变化后清空不兼容分类（转账一律不挂分类），保证统计口径一致。"""
        if transaction.category_id is None:
            return
        if transaction.direction is Direction.TRANSFER:
            transaction.category_id = None
            transaction.category_source = None
            return
        category = uow.categories.get(transaction.category_id)
        if category is not None and category.type.value != transaction.direction.value:
            transaction.category_id = None
            transaction.category_source = None
