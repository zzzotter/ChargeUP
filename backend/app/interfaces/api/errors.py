"""统一错误响应与请求追踪。

所有错误（含 404/405/500）都返回 {code, message, details.request_id}，
便于前端走同一套错误分支、线上按 request_id 检索日志。
"""

from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.errors import DomainError

LOGGER = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

_STATUS_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    429: "TOO_MANY_REQUESTS",
}

# Pydantic 校验消息中英混杂 -> 统一中文提示
_VALIDATION_MESSAGES = {
    "missing": "缺少必填字段",
    "too_short": "长度不足",
    "too_long": "长度超出上限",
    "string_too_short": "长度不足",
    "string_too_long": "长度超出上限",
    "string_type": "必须为字符串",
    "value_error": "取值不合法",
    "literal_error": "取值不在允许范围",
    "enum": "取值不在允许范围",
    "date_from_datetime_parsing": "日期格式不正确",
    "date_parsing": "日期格式不正确",
    "datetime_from_date_parsing": "时间格式不正确",
    "datetime_parsing": "时间格式不正确",
    "time_parsing": "时间格式不正确",
    "int_parsing": "必须为整数",
    "int_type": "必须为整数",
    "float_parsing": "必须为数值",
    "greater_than": "必须大于设定下限",
    "greater_than_equal": "必须不小于设定下限",
    "less_than": "必须小于设定上限",
    "less_than_equal": "必须不大于设定上限",
    "list_too_long": "数量超过上限",
    "list_too_short": "数量不足",
    "list_type": "必须为列表",
    "bool_type": "必须为布尔值",
    "bool_parsing": "必须为布尔值",
    "json_invalid": "请求体不是合法 JSON",
    "model_attributes_type": "请求体必须为对象",
}


def install_request_context(app: FastAPI) -> None:
    """为每个请求生成/透传 request id，并写入响应头。"""

    @app.middleware("http")
    async def _request_id_middleware(request: Request, call_next):
        request_id = (request.headers.get(REQUEST_ID_HEADER) or uuid4().hex[:12]).strip()[:64]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "-")


def _error_body(
    code: str,
    message: str,
    request_id: str,
    details: dict | None = None,
) -> dict:
    payload = {"request_id": request_id}
    if details:
        payload.update(details)
    return {"code": code, "message": message, "details": payload}


def _translate_validation_error(error: dict) -> dict:
    message = str(error.get("msg") or "")
    for prefix in ("Value error, ", "Assertion failed, "):
        if message.startswith(prefix):
            message = message[len(prefix) :]
            break
    else:
        error_type = str(error.get("type"))
        ctx = error.get("ctx") or {}
        if error_type in ("too_short", "string_too_short") and ctx.get("min_length") is not None:
            message = f"长度不能少于 {ctx['min_length']} 个字符"
        elif error_type in ("too_long", "string_too_long") and ctx.get("max_length") is not None:
            message = f"长度不能超过 {ctx['max_length']} 个字符"
        elif error_type in ("list_too_short", "list_too_long"):
            message = _VALIDATION_MESSAGES[error_type]
        else:
            message = _VALIDATION_MESSAGES.get(error_type, message)
    return {
        "loc": list(error.get("loc") or ()),
        "type": error.get("type"),
        "msg": message,
    }


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        LOGGER.info(
            "业务异常 request_id=%s code=%s message=%s",
            _request_id(request),
            exc.code,
            exc.message,
        )
        request_id = _request_id(request)
        headers = {**exc.headers, REQUEST_ID_HEADER: request_id}
        return JSONResponse(
            status_code=exc.http_status,
            content=_error_body(exc.code, exc.message, request_id, exc.details),
            headers=headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = _request_id(request)
        return JSONResponse(
            status_code=422,
            content=_error_body(
                "VALIDATION_ERROR",
                "请求参数校验失败",
                request_id,
                {"errors": [_translate_validation_error(e) for e in exc.errors()]},
            ),
            headers={REQUEST_ID_HEADER: request_id},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "请求无法处理"
        code = _STATUS_CODES.get(exc.status_code, "HTTP_ERROR")
        request_id = _request_id(request)
        headers = {**(getattr(exc, "headers", None) or {}), REQUEST_ID_HEADER: request_id}
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(code, detail, request_id),
            headers=headers,
        )

    @app.exception_handler(Exception)
    async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = _request_id(request)
        LOGGER.exception("未处理异常 request_id=%s", request_id, exc_info=exc)
        # 对外只暴露追踪标识，不泄露堆栈
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "服务器内部错误，请稍后重试", request_id),
            headers={REQUEST_ID_HEADER: request_id},
        )
