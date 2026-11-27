"""集成检查公共夹具：把真实后端 ChargeUP/backend 加入路径并提供内存 TestClient。

不修改后端代码，仅在独立进程中对真实 app 做检查；使用 SQLite 内存库，无需 PostgreSQL。
"""
from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

BACKEND = Path(__file__).resolve().parents[1] / "ChargeUP" / "backend"
sys.path.insert(0, str(BACKEND))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402


@contextmanager
def _build_client():
    settings = Settings(
        database_url="sqlite+pysqlite://",
        seed_on_startup=True,
        create_schema_on_startup=True,
    )
    with TestClient(create_app(settings)) as client:
        yield client


@pytest.fixture()
def client():
    with _build_client() as c:
        yield c


@pytest.fixture()
def backend_path() -> Path:
    return BACKEND
