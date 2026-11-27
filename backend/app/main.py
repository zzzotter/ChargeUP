"""FastAPI 应用装配（六边形架构的「接口层入口」）。"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.infrastructure.db import Database
from app.infrastructure.logging import configure_logging
from app.infrastructure.seeding import seed_defaults
from app.interfaces.api.auth import install_docs_guard, require_token
from app.interfaces.api.deps import Container
from app.interfaces.api.errors import install_request_context, register_error_handlers
from app.interfaces.api.routers import (
    alerts,
    budget,
    categories,
    category_rules,
    health,
    imports,
    stats,
    transactions,
)
from app.interfaces.api.routers import (
    settings as settings_router,
)

LOGGER = logging.getLogger(__name__)

TAGS_METADATA = [
    {"name": "交易", "description": "账本分页、详情、编辑、软删除/恢复、批量归类"},
    {"name": "分类", "description": "分类 CRUD、分类建议与来源标注"},
    {"name": "分类规则", "description": "关键词规则 CRUD 与干跑测试"},
    {"name": "导入", "description": "CSV 导入、截图候选入账、导入历史与报告"},
    {"name": "统计", "description": "仪表盘概要、月度趋势与分类分布"},
    {"name": "预算", "description": "月度预算与 warn/alert 双阈值"},
    {"name": "预警", "description": "预警事件流与已读标记"},
    {"name": "设置", "description": "时薪、人设与模块开关"},
    {"name": "系统", "description": "健康检查（免鉴权）"},
]

DESCRIPTION = """
ledger-guard 智能记账与消费干预系统 —— 后端 API（P0 + 设置，对齐前端《页面清单》§7 契约）。

约定：
- 前缀 `/api/v1`，请求/响应字段一律 lowerCamelCase。
- 金额一律整数「分」，字段名 `amount` / `totalExpense` 等；不接受浮点金额。
- 时间 ISO 8601 带时区偏移（如 `2026-11-24T18:20:11+08:00`）。
- 分页 `page` 从 1 开始，`pageSize` 默认 20（上限 100），响应 `{items,page,pageSize,total}`。
- 排序 `sort=occurredAt,-amount`（前缀 `-` 表示降序）。
- 财务记录只做软删除：`DELETE` 仅写 `deletedAt` 并返回 204；硬删除一律 405 `HARD_DELETE_FORBIDDEN`。
- 错误统一 `{code, message, details}`；重复资源 409 `DUPLICATE_RESOURCE`，参数校验 422 `VALIDATION_ERROR`。
- 设置环境变量 `API_TOKEN` 后，除 `/health*` 外的接口都需要 `Authorization: Bearer <token>`。
"""

_PROTECTED_ROUTERS = (
    transactions,
    categories,
    category_rules,
    imports,
    stats,
    budget,
    alerts,
    settings_router,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    configure_logging(getattr(logging, settings.log_level.upper(), logging.INFO))

    database = Database(settings.database_url)
    container = Container(settings, database)

    # 文档策略：显式配置优先；否则「有令牌即关闭」，避免匿名暴露接口字段
    docs_enabled = (
        settings.docs_enabled
        if settings.docs_enabled is not None
        else not bool(settings.api_token)
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.create_schema_on_startup:
            database.create_schema()
        if settings.seed_on_startup:
            seed_defaults(database.unit_of_work)
        if settings.api_token:
            LOGGER.info(
                "API_TOKEN 已启用：除健康检查外的接口需要 Bearer 令牌；文档 %s",
                "已开启（同样需令牌）" if docs_enabled else "已关闭",
            )
        else:
            LOGGER.warning(
                "未配置 API_TOKEN，接口处于免鉴权模式；请仅绑定 127.0.0.1 或配置令牌后再对外提供服务"
            )
        LOGGER.info("ledger-guard 后端启动完成 timezone=%s", settings.timezone)
        try:
            yield
        finally:
            database.dispose()

    app = FastAPI(
        title="ledger-guard API",
        version="0.1.0",
        description=DESCRIPTION,
        openapi_tags=TAGS_METADATA,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
        openapi_url="/openapi.json" if docs_enabled else None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.container = container

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 先装文档守卫、再装请求上下文：保证 401 响应也带真实 request id
    install_docs_guard(app, settings.api_token, docs_enabled=docs_enabled)
    install_request_context(app)
    register_error_handlers(app)

    # 健康检查保持免鉴权，便于编排系统探活
    app.include_router(health.router, prefix=settings.api_prefix)
    for module in _PROTECTED_ROUTERS:
        app.include_router(
            module.router,
            prefix=settings.api_prefix,
            dependencies=[Depends(require_token)],
        )

    return app


app = create_app()
