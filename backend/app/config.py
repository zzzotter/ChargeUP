"""运行配置（从环境变量读取，含默认值）。"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:  # python-dotenv 为可选依赖：未安装时仅支持导出环境变量
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - 依赖缺失时降级
    load_dotenv = None

DEFAULT_DATABASE_URL = "postgresql+psycopg://ledger:ledger@localhost:5432/ledger"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_list(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = os.getenv(name)
    if not raw:
        return default
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    timezone: str = "Asia/Shanghai"
    api_prefix: str = "/api/v1"
    refund_window_days: int = 7
    warn_bps: int = 8000
    alert_bps: int = 10000
    max_upload_bytes: int = 10 * 1024 * 1024
    cors_origins: tuple[str, ...] = ("http://localhost:3000", "http://127.0.0.1:3000")
    seed_on_startup: bool = True
    create_schema_on_startup: bool = False
    log_level: str = "INFO"
    api_token: str | None = None
    # None = 自动：未配置令牌时开启，配置令牌时关闭；显式布尔值则强制生效
    docs_enabled: bool | None = None

    @classmethod
    def from_env(cls) -> Settings:
        if load_dotenv is not None:
            # 显式指定路径，避免 find_dotenv 从调用栈文件所在目录向上查找导致行为不确定；
            # 只补充未导出的变量，不覆盖显式环境变量。
            load_dotenv(dotenv_path=os.getenv("DOTENV_PATH", ".env"), override=False)
        token = os.getenv("API_TOKEN", "").strip()
        return cls(
            database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
            timezone=os.getenv("APP_TIMEZONE", "Asia/Shanghai"),
            api_prefix=os.getenv("API_PREFIX", "/api/v1"),
            refund_window_days=_env_int("REFUND_WINDOW_DAYS", 7),
            warn_bps=_env_int("BUDGET_WARN_BPS", 8000),
            alert_bps=_env_int("BUDGET_ALERT_BPS", 10000),
            max_upload_bytes=_env_int("MAX_UPLOAD_BYTES", 10 * 1024 * 1024),
            cors_origins=_env_list(
                "CORS_ORIGINS", ("http://localhost:3000", "http://127.0.0.1:3000")
            ),
            seed_on_startup=_env_bool("SEED_ON_STARTUP", True),
            create_schema_on_startup=_env_bool("CREATE_SCHEMA_ON_STARTUP", False),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            api_token=token or None,
            # 启用令牌时默认关闭文档，避免 /docs、/openapi.json 匿名暴露字段与示例
            docs_enabled=_env_bool("DOCS_ENABLED", not token),
        )
