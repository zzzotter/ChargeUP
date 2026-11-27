"""对外适配器：先提供内存 mock，后端就绪后启用 httpx 实现。"""
from .ports import ImportGateway
from .mock_gateway import MockGateway
from .http_gateway import HttpGateway

__all__ = ["ImportGateway", "MockGateway", "HttpGateway"]
