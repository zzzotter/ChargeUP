"""CSV 导入与截图候选入账用例。

幂等口径（SRS F-P0-02）：基于 (source, external_id) 判重；
文件内重复行与库内已存在单号都计入 duplicated，不产生重复流水。
每次导入都会落一条 ImportRecord，供导入历史与报告详情使用。
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from time import perf_counter
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError

from app.application.categorization import auto_categorize
from app.application.dto import (
    ImportReportData,
    ScreenshotImportResult,
    ScreenshotRow,
)
from app.application.notifications import PeriodHook, notify_periods
from app.application.transactions import TransactionService
from app.domain.entities import ImportFailure, ImportRecord, Transaction
from app.domain.enums import Direction, Source
from app.domain.errors import ConflictError, NotFoundError
from app.domain.ports.clock import Clock
from app.domain.ports.repositories import UnitOfWork
from app.domain.services.csv_parser import parse_csv

LOGGER = logging.getLogger(__name__)


class ImportService:
    def __init__(
        self,
        uow_factory: Callable[[], UnitOfWork],
        clock: Clock,
        tz: ZoneInfo,
        on_change: Sequence[PeriodHook] = (),
        transactions: TransactionService | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._tz = tz
        self._on_change = tuple(on_change)
        self._transactions = transactions

    def import_csv(
        self,
        filename: str,
        content: bytes,
        *,
        source: Source | None = None,
    ) -> ImportReportData:
        """source 显式指定时优先采用；未指定时按文件内容探测（默认支付宝）。"""
        started = perf_counter()
        parsed = parse_csv(
            content, tzinfo=self._tz, default_source=Source.ALIPAY, explicit_source=source
        )

        candidates: list[Transaction] = []
        duplicates = 0
        record_id: int | None = None
        duration_ms = 0

        with self._uow_factory() as uow:
            known = uow.transactions.existing_external_ids(
                parsed.source, [row.external_id for row in parsed.rows]
            )
            seen: set[str] = set()
            now = self._clock.now()

            for row in parsed.rows:
                if row.external_id in known or row.external_id in seen:
                    duplicates += 1
                    continue
                seen.add(row.external_id)
                decision = (
                    auto_categorize(uow, row.merchant, row.direction)
                    if row.direction is not Direction.TRANSFER
                    else None
                )
                candidates.append(
                    Transaction(
                        source=parsed.source,
                        external_id=row.external_id,
                        amount_cents=row.amount_cents,
                        direction=row.direction,
                        occurred_at=row.occurred_at,
                        merchant=row.merchant,
                        note=row.note,
                        category_id=decision.category_id if decision else None,
                        category_source=decision.source if decision else None,
                        created_at=now,
                        updated_at=now,
                    )
                )

            duration_ms = int((perf_counter() - started) * 1000)
            record = ImportRecord(
                filename=filename,
                source=parsed.source,
                encoding=parsed.encoding,
                recognized=len(candidates) + duplicates,
                skipped_header_rows=parsed.skipped_lines,
                duplicated=duplicates,
                failed=parsed.rejected_total,
                created=len(candidates),
                duration_ms=duration_ms,
                failures=tuple(
                    ImportFailure(
                        row_number=issue.line_no, reason=issue.detail, raw=issue.raw
                    )
                    for issue in parsed.issues
                ),
                created_at=now,
            )

            try:
                if candidates:
                    uow.transactions.add_many(candidates)
                saved_record = uow.imports.add(record)
                record_id = saved_record.id
                uow.commit()
            except IntegrityError as exc:
                # 与另一并发导入撞上同一 (source, external_id)：提示重试而非 500
                raise ConflictError("导入与另一请求发生单号冲突，请稍后重试") from exc

        if candidates:
            LOGGER.info(
                "CSV 导入完成 file=%s source=%s created=%d duplicates=%d failed=%d",
                filename,
                parsed.source.value,
                len(candidates),
                duplicates,
                parsed.rejected_total,
            )
            notify_periods(self._on_change, [txn.occurred_at for txn in candidates], self._tz)

        return ImportReportData(
            import_id=record_id or 0,
            filename=filename,
            source=parsed.source,
            encoding=parsed.encoding,
            recognized=len(candidates) + duplicates,
            skipped_header_rows=parsed.skipped_lines,
            duplicated=duplicates,
            failed=parsed.rejected_total,
            created=len(candidates),
            duration_ms=duration_ms,
            failures=record.failures,
        )

    def create_screenshot_candidates(
        self,
        rows: Sequence[ScreenshotRow],
        skipped_client_ids: Sequence[str] = (),
    ) -> ScreenshotImportResult:
        if self._transactions is None:  # pragma: no cover - 装配错误
            raise RuntimeError("截图入账需要 TransactionService")
        return self._transactions.create_screenshot(rows, skipped_client_ids)

    def list_imports(
        self, *, page: int = 1, page_size: int = 20
    ) -> tuple[list[ImportRecord], int]:
        with self._uow_factory() as uow:
            return uow.imports.search(limit=page_size, offset=(page - 1) * page_size)

    def report(self, import_id: int) -> ImportReportData:
        with self._uow_factory() as uow:
            record = uow.imports.get(import_id)
        if record is None:
            raise NotFoundError(f"导入记录 {import_id} 不存在")
        return ImportReportData(
            import_id=record.id or import_id,
            filename=record.filename,
            source=record.source,
            encoding=record.encoding,
            recognized=record.recognized,
            skipped_header_rows=record.skipped_header_rows,
            duplicated=record.duplicated,
            failed=record.failed,
            created=record.created,
            duration_ms=record.duration_ms,
            failures=record.failures,
        )
