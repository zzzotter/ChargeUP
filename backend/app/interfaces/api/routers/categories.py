"""分类路由：CRUD + 分类建议（快捷填写用）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.domain.enums import CategoryType
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import (
    CategoryCreateRequest,
    CategoryRead,
    CategorySuggestRead,
    CategoryUpdateRequest,
    category_to_read,
    suggestion_to_read,
)

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", response_model=list[CategoryRead], summary="分类列表")
def list_categories(
    type: CategoryType | None = Query(default=None),
    container: Container = Depends(get_container),
) -> list[CategoryRead]:
    views = container.categories.list()
    if type is not None:
        views = [view for view in views if view.category.type is type]
    return [category_to_read(view) for view in views]


@router.post("", response_model=CategoryRead, status_code=201, summary="新建分类")
def create_category(
    payload: CategoryCreateRequest,
    container: Container = Depends(get_container),
) -> CategoryRead:
    category = container.categories.create(payload.name, payload.type, payload.color)
    views = container.categories.list()
    view = next(item for item in views if item.category.id == category.id)
    return category_to_read(view)


# 静态路径先于动态路径声明
@router.get(
    "/suggest",
    response_model=CategorySuggestRead,
    summary="分类建议（快捷填写实时调用）",
)
def suggest_category(
    name: str = Query(min_length=1, max_length=255),
    container: Container = Depends(get_container),
) -> CategorySuggestRead:
    return suggestion_to_read(container.categories.suggest(name))


@router.patch("/{category_id}", response_model=CategoryRead, summary="修改分类（改名/改色/停用）")
def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    container: Container = Depends(get_container),
) -> CategoryRead:
    category = container.categories.update(
        category_id,
        name=payload.name,
        color=payload.color,
        update_color=payload.update_color,
        is_active=payload.is_active,
    )
    views = container.categories.list()
    view = next(item for item in views if item.category.id == category.id)
    return category_to_read(view)


@router.delete("/{category_id}", status_code=204, summary="删除分类（被交易引用时 409）")
def delete_category(
    category_id: int,
    container: Container = Depends(get_container),
) -> Response:
    container.categories.delete(category_id)
    return Response(status_code=204)
