"""交易路由：对齐前端 §7 /transactions 契约。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.application.dto import (
    BatchClassifyCommand,
    CreateTransactionCommand,
    DuplicateProbe,
    UpdateTransactionCommand,
)
from app.application.periods import month_bounds
from app.domain.enums import Direction, Source
from app.domain.errors import ValidationError
from app.domain.ports.repositories import TransactionFilter
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import (
    BatchClassifyRead,
    BatchClassifyRequest,
    DuplicateProbeList,
    Page,
    ReclassifyRequest,
    ReclassifyResultRead,
    SuspectedDuplicateList,
    SuspectedDuplicateRead,
    TransactionInput,
    TransactionRead,
    TransactionUpdateRequest,
    batch_result_to_read,
    transaction_to_read,
)

router = APIRouter(prefix="/transactions", tags=["交易"])

_SORTABLE = {"occurredAt", "amount", "createdAt"}
_PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


def parse_sort(raw: str | None) -> tuple[tuple[str, bool], ...]:
    """sort=occurredAt,-amount：字段名用 lowerCamelCase，前缀 - 表示降序。"""
    if not raw:
        return ()
    result: list[tuple[str, bool]] = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        descending = token.startswith("-")
        field = token[1:] if descending else token
        if field not in _SORTABLE:
            raise ValidationError(
                f"不支持的排序字段「{field}」，可选：{', '.join(sorted(_SORTABLE))}"
            )
        result.append((field, descending))
    return tuple(result)


def _page(items, total: int, page: int, page_size: int, container: Container):
    return Page(
        items=[transaction_to_read(item, container.tz) for item in items],
        page=page,
        page_size=page_size,
        total=total,
    )


# 静态路径必须声明在 /{transaction_id} 之前，避免被整数路径参数误吞
@router.get("/inbox", response_model=Page[TransactionRead], summary="待分类收件箱")
def list_inbox(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    sort: str | None = Query(default=None, description="如 -occurredAt"),
    container: Container = Depends(get_container),
) -> Page[TransactionRead]:
    items, total = container.transactions.inbox(
        page=page, page_size=page_size, sort=parse_sort(sort)
    )
    return _page(items, total, page, page_size, container)


@router.post(
    "/batch-classify",
    response_model=BatchClassifyRead,
    summary="批量归类（可选同时沉淀关键词规则）",
)
def batch_classify(
    payload: BatchClassifyRequest,
    container: Container = Depends(get_container),
) -> BatchClassifyRead:
    command = BatchClassifyCommand(
        transaction_ids=tuple(payload.ids),
        category_id=payload.category_id,
        rule_keyword=payload.create_rule.keyword if payload.create_rule else None,
    )
    return batch_result_to_read(container.transactions.batch_classify(command))


@router.post("/reclassify", response_model=ReclassifyResultRead, summary="重跑分类规则")
def reclassify(
    payload: ReclassifyRequest | None = None,
    container: Container = Depends(get_container),
) -> ReclassifyResultRead:
    result = container.transactions.reclassify(payload.transaction_ids if payload else None)
    return ReclassifyResultRead(
        scanned=result.scanned,
        updated=result.updated,
        total=result.total,
        remaining=result.remaining,
        truncated=result.truncated,
        invalid_ids=[str(item) for item in result.invalid_ids],
    )


@router.post(
    "/duplicates/check",
    response_model=SuspectedDuplicateList,
    summary="弱指纹查重（同日同额）",
)
def check_duplicates(
    payload: DuplicateProbeList,
    container: Container = Depends(get_container),
) -> SuspectedDuplicateList:
    probes = [
        DuplicateProbe(
            merchant=item.merchant, amount_cents=item.amount, occurred_at=item.occurred_at
        )
        for item in payload.items
    ]
    found = container.transactions.find_suspected_duplicates(probes)
    return SuspectedDuplicateList(
        items=[
            SuspectedDuplicateRead(
                transaction_id=str(item.transaction_id),
                merchant=item.merchant,
                amount=item.amount_cents,
                occurred_at=item.occurred_at,
                external_id=item.external_id,
                confidence=item.confidence,
            )
            for item in found
        ]
    )


@router.get("", response_model=Page[TransactionRead], summary="账本分页列表")
def list_transactions(
    month: str | None = Query(default=None, pattern=_PERIOD_PATTERN, description="YYYY-MM"),
    source: str | None = Query(default=None, description="ALIPAY/WECHAT/SCREENSHOT/MANUAL；ALL=不限"),
    category_id: str | None = Query(
        default=None, alias="categoryId", description="分类 id；ALL=不限，NONE=未分类"
    ),
    direction: Direction | None = Query(default=None),
    q: str | None = Query(default=None, max_length=255, description="商户/备注模糊匹配"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100, alias="pageSize"),
    sort: str | None = Query(default=None, description="如 -occurredAt,-amount"),
    container: Container = Depends(get_container),
) -> Page[TransactionRead]:
    start = end = None
    if month:
        start, end = month_bounds(month, container.tz)

    # 前端筛选直接映射 URL 参数，空值用 ALL 表示不限
    source_value: Source | None = None
    if source and source != "ALL":
        try:
            source_value = Source(source)
        except ValueError as exc:
            raise ValidationError("source 取值不在允许范围") from exc

    uncategorized = False
    category_value: int | None = None
    if category_id and category_id != "ALL":
        if category_id.upper() == "NONE":
            uncategorized = True
        else:
            try:
                category_value = int(category_id)
            except ValueError as exc:
                raise ValidationError("categoryId 必须为 ALL、NONE 或数字 id") from exc

    filters = TransactionFilter(
        start=start,
        end=end,
        category_id=category_value,
        uncategorized=uncategorized,
        direction=direction,
        source=source_value,
        keyword=q,
        sort=parse_sort(sort),
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    items, total = container.transactions.list(filters)
    return _page(items, total, page, page_size, container)


@router.post(
    "", response_model=TransactionRead, status_code=201, summary="新建交易（快捷填写/手动）"
)
def create_transaction(
    payload: TransactionInput,
    container: Container = Depends(get_container),
) -> TransactionRead:
    command = CreateTransactionCommand(
        amount_cents=payload.amount,
        occurred_at=payload.occurred_at,
        direction=Direction(payload.direction),
        merchant=payload.merchant,
        note=payload.note or "",
        category_id=payload.category_id,
    )
    return transaction_to_read(container.transactions.create(command), container.tz)


@router.get("/{transaction_id}", response_model=TransactionRead, summary="交易详情")
def get_transaction(
    transaction_id: int,
    include_deleted: bool = Query(default=False, alias="includeDeleted"),
    container: Container = Depends(get_container),
) -> TransactionRead:
    return transaction_to_read(
        container.transactions.get(transaction_id, include_deleted=include_deleted),
        container.tz,
    )


@router.patch("/{transaction_id}", response_model=TransactionRead, summary="编辑交易")
def update_transaction(
    transaction_id: int,
    payload: TransactionUpdateRequest,
    container: Container = Depends(get_container),
) -> TransactionRead:
    command = UpdateTransactionCommand(
        merchant=payload.merchant,
        amount_cents=payload.amount,
        direction=payload.direction,
        occurred_at=payload.occurred_at,
        note=payload.note,
        category_id=payload.category_id,
        clear_category=payload.clears_category,
        recategorize=payload.recategorize,
    )
    return transaction_to_read(
        container.transactions.update(transaction_id, command), container.tz
    )


@router.delete(
    "/{transaction_id}",
    status_code=204,
    summary="软删除（移入回收）",
    description="只写 deletedAt；hard=true 一律 405 HARD_DELETE_FORBIDDEN。",
)
def delete_transaction(
    transaction_id: int,
    hard: bool = Query(default=False, description="预留：硬删除请求一律拒绝"),
    container: Container = Depends(get_container),
) -> Response:
    container.transactions.soft_delete(transaction_id, hard=hard)
    return Response(status_code=204)


@router.post(
    "/{transaction_id}/restore", response_model=TransactionRead, summary="从回收恢复"
)
def restore_transaction(
    transaction_id: int,
    container: Container = Depends(get_container),
) -> TransactionRead:
    return transaction_to_read(container.transactions.restore(transaction_id), container.tz)
