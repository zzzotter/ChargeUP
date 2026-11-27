"""领域异常。接口层负责把它们翻译成 HTTP 状态码，领域层不感知 HTTP。"""

from __future__ import annotations


class DomainError(Exception):
    """所有业务异常的基类。"""

    code = "DOMAIN_ERROR"
    http_status = 400

    def __init__(
        self,
        message: str,
        *,
        details: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.headers = headers or {}


class ValidationError(DomainError):
    code = "VALIDATION_ERROR"
    http_status = 422


class NotFoundError(DomainError):
    code = "NOT_FOUND"
    http_status = 404


class ConflictError(DomainError):
    code = "CONFLICT"
    http_status = 409


class DuplicateResourceError(DomainError):
    """唯一约束冲突（重复交易/规则）。前端 §7.5 约定 409 DUPLICATE_RESOURCE。"""

    code = "DUPLICATE_RESOURCE"
    http_status = 409


class HardDeleteForbidden(DomainError):
    """财务记录禁止物理删除。前端只提供「移入回收」。"""

    code = "HARD_DELETE_FORBIDDEN"
    http_status = 405


class UnauthorizedError(DomainError):
    """缺少或无效的访问令牌。"""

    code = "UNAUTHORIZED"
    http_status = 401


class SoftDeleteViolation(DomainError):
    """财务记录禁止物理删除，只用 deleted_at 标记。"""

    code = "SOFT_DELETE_REQUIRED"
    http_status = 409


class ParseError(DomainError):
    code = "PARSE_ERROR"
    http_status = 422
