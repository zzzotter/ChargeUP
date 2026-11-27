"""健康检查（免鉴权，且不暴露鉴权开关等敏感配置）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from app.domain.ports.repositories import TransactionFilter
from app.interfaces.api.deps import Container, get_container

router = APIRouter(tags=["系统"])


@router.get("/health", summary="存活检查")
def health(container: Container = Depends(get_container)) -> dict:
    return {
        "status": "ok",
        "time": container.clock.now().isoformat(),
        # 同时给出配置值与实际生效值，时区误配时不会误导对账
        "timezone": container.settings.timezone,
        "timezone_effective": container.tz_effective,
        "timezone_fallback": container.tz_fallback,
    }


@router.get(
    "/health/ready",
    summary="就绪检查（数据库连通性 + 迁移版本 + 关键表可读）",
    response_model=None,
)
def ready(container: Container = Depends(get_container)):
    try:
        with container.database.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            inspector = inspect(connection)
            has_version_table = inspector.has_table("alembic_version")
            schema_version = (
                connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
                if has_version_table
                else None
            )
        with container.database.unit_of_work() as uow:
            _, total = uow.transactions.search(TransactionFilter(limit=1))
    except SQLAlchemyError:
        # 就绪失败必须用 503，避免编排系统把异常实例当成可用
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "database": "unavailable"},
        )

    return {
        "status": "ready",
        "database": "ok",
        "schema_version": schema_version or "unmanaged",
        "transactions": total,
    }
