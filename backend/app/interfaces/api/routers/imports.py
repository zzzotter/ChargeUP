"""导入路由：CSV 导入、截图候选入账、导入历史与报告。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.application.dto import ScreenshotRow
from app.domain.enums import Direction, Source
from app.domain.errors import ValidationError
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import (
    ImportRecordRead,
    ImportReportRead,
    Page,
    ScreenshotCandidatesRead,
    ScreenshotCandidatesRequest,
    ScreenshotFailureRead,
    import_record_to_read,
    import_report_to_read,
)

router = APIRouter(prefix="/imports", tags=["导入"])

_ALLOWED_SOURCES = (Source.ALIPAY, Source.WECHAT)
_CHUNK_SIZE = 256 * 1024


def human_size(num_bytes: int) -> str:
    """阈值文案自适应：不足 1MB 用 KB，避免显示成 0MB。"""
    if num_bytes >= 1024 * 1024:
        return f"{num_bytes / (1024 * 1024):.1f}MB"
    if num_bytes >= 1024:
        return f"{num_bytes / 1024:.1f}KB"
    return f"{num_bytes}B"


async def _read_limited(file: UploadFile, limit: int) -> bytes:
    """分块读取并在超限时立即中断，避免大文件整体进入内存。"""
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(_CHUNK_SIZE)
        if not chunk:
            break
        total += len(chunk)
        if total > limit:
            raise ValidationError(f"文件超过大小限制（{human_size(limit)}）")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post(
    "/csv",
    response_model=ImportReportRead,
    status_code=201,
    summary="导入微信/支付宝 CSV 账单",
)
async def import_csv(
    request: Request,
    file: UploadFile = File(..., description="微信/支付宝导出的 CSV 文件"),
    source: Source | None = Form(default=None, description="显式指定来源，留空则按内容探测"),
    container: Container = Depends(get_container),
) -> ImportReportRead:
    filename = file.filename or "upload.csv"
    if not filename.lower().endswith(".csv"):
        raise ValidationError("仅支持 .csv 文件")
    if source is not None and source not in _ALLOWED_SOURCES:
        raise ValidationError("source 仅支持 ALIPAY 或 WECHAT")

    limit = container.settings.max_upload_bytes
    declared = request.headers.get("content-length")
    if declared and declared.isdigit() and int(declared) > limit:
        raise ValidationError(f"文件超过大小限制（{human_size(limit)}）")

    content = await _read_limited(file, limit)
    if not content:
        raise ValidationError("文件内容为空")

    return import_report_to_read(container.imports.import_csv(filename, content, source=source))


@router.post(
    "/screenshot-candidates",
    response_model=ScreenshotCandidatesRead,
    summary="截图候选批量入账（source=SCREENSHOT）",
)
def screenshot_candidates(
    payload: ScreenshotCandidatesRequest,
    container: Container = Depends(get_container),
) -> ScreenshotCandidatesRead:
    rows = [
        ScreenshotRow(
            client_id=row.client_id,
            merchant=row.merchant,
            amount_cents=row.amount,
            direction=Direction(row.direction),
            occurred_at=row.occurred_at,
            category_id=row.category_id,
            note=row.note or "",
        )
        for row in payload.rows
    ]
    result = container.imports.create_screenshot_candidates(rows, payload.skipped_client_ids)
    return ScreenshotCandidatesRead(
        created=result.created,
        skipped=result.skipped,
        failed=result.failed,
        failures=[
            ScreenshotFailureRead(client_id=item.client_id, reason=item.reason)
            for item in result.failures
        ],
    )


@router.get("", response_model=Page[ImportRecordRead], summary="导入历史")
def list_imports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    container: Container = Depends(get_container),
) -> Page[ImportRecordRead]:
    records, total = container.imports.list_imports(page=page, page_size=page_size)
    return Page(
        items=[import_record_to_read(record, container.tz) for record in records],
        page=page,
        page_size=page_size,
        total=total,
    )


@router.get(
    "/{import_id}/report", response_model=ImportReportRead, summary="导入报告详情"
)
def import_report(
    import_id: int,
    container: Container = Depends(get_container),
) -> ImportReportRead:
    return import_report_to_read(container.imports.report(import_id))
