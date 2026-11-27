"""分类规则路由：列表、新建、删除、干跑测试。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.schemas import (
    RuleCreateRequest,
    RuleRead,
    RuleTestRead,
    RuleTestRequest,
    rule_test_to_read,
    rule_to_read,
)

router = APIRouter(prefix="/category-rules", tags=["分类规则"])


@router.get("", response_model=list[RuleRead], summary="规则列表（用户规则优先）")
def list_rules(container: Container = Depends(get_container)) -> list[RuleRead]:
    return [rule_to_read(item) for item in container.categories.list_rules()]


@router.post("", response_model=RuleRead, status_code=201, summary="新增用户规则")
def create_rule(
    payload: RuleCreateRequest,
    container: Container = Depends(get_container),
) -> RuleRead:
    rule = container.categories.create_rule(
        keyword=payload.keyword, category_id=payload.category_id, priority=payload.priority
    )
    return rule_to_read(rule)


@router.post("/test", response_model=RuleTestRead, summary="规则干跑测试（不写库）")
def test_rule(
    payload: RuleTestRequest,
    container: Container = Depends(get_container),
) -> RuleTestRead:
    return rule_test_to_read(container.categories.test_rule(payload.name))


@router.delete("/{rule_id}", status_code=204, summary="删除用户规则（内置规则只读，409）")
def delete_rule(rule_id: int, container: Container = Depends(get_container)) -> Response:
    container.categories.delete_rule(rule_id)
    return Response(status_code=204)
