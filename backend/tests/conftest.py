from __future__ import annotations

from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@contextmanager
def build_client(**overrides):
    """独立内存库 + 可选配置覆盖，用于鉴权/上传上限等场景。"""
    raise_server_exceptions = overrides.pop("raise_server_exceptions", True)
    config = {
        "database_url": "sqlite+pysqlite://",
        "timezone": "Asia/Shanghai",
        "seed_on_startup": True,
        "create_schema_on_startup": True,
    }
    config.update(overrides)
    settings = Settings(**config)
    app = create_app(settings)
    with TestClient(app, raise_server_exceptions=raise_server_exceptions) as client:
        yield client


@pytest.fixture()
def api_client():
    """每个用例独立的内存库，启动时建表并播种默认分类/词库。"""
    with build_client() as client:
        yield client


@pytest.fixture()
def client_factory():
    return build_client
