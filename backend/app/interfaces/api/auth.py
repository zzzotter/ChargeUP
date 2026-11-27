"""可选的 Bearer Token 鉴权。

个人自托管场景下，默认（未配置 API_TOKEN）免密访问，但服务只应绑定回环地址；
设置 API_TOKEN 后：
- 除 /health* 外的全部 /api/v1 接口都要求 `Authorization: Bearer <token>`；
- 文档默认关闭（DOCS_ENABLED=false）；若显式开启，/docs、/redoc、/openapi.json
  同样要求令牌，避免匿名枚举接口字段。
"""

from __future__ import annotations

import secrets

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.domain.errors import UnauthorizedError
from app.interfaces.api.deps import Container, get_container
from app.interfaces.api.errors import REQUEST_ID_HEADER

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="ApiToken",
    description="在 .env 设置 API_TOKEN 后，携带 Authorization: Bearer <token>",
)

_DOC_PATHS = {"/docs", "/redoc", "/openapi.json", "/docs/oauth2-redirect"}


def token_matches(provided: str | None, expected: str) -> bool:
    if not provided:
        return False
    return secrets.compare_digest(provided, expected)


def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    container: Container = Depends(get_container),
) -> None:
    token = container.settings.api_token
    if not token:
        return
    if credentials is None or not token_matches(credentials.credentials, token):
        raise UnauthorizedError(
            "缺少或无效的访问令牌（Authorization: Bearer <API_TOKEN>）",
            headers={"WWW-Authenticate": "Bearer"},
        )


def install_docs_guard(app: FastAPI, token: str | None, *, docs_enabled: bool) -> None:
    """开启文档且配置了令牌时，文档路径同样需要 Bearer 令牌。"""
    if not token or not docs_enabled:
        return

    @app.middleware("http")
    async def _docs_guard(request: Request, call_next):
        if request.url.path in _DOC_PATHS:
            header = request.headers.get("authorization", "")
            scheme, _, provided = header.partition(" ")
            if scheme.lower() != "bearer" or not token_matches(provided.strip(), token):
                request_id = getattr(request.state, "request_id", "-")
                return JSONResponse(
                    status_code=401,
                    content={
                        "code": "UNAUTHORIZED",
                        "message": "文档接口需要访问令牌",
                        "details": {"request_id": request_id},
                    },
                    headers={
                        "WWW-Authenticate": "Bearer",
                        REQUEST_ID_HEADER: request_id,
                    },
                )
        return await call_next(request)
