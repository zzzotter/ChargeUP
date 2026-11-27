"""六边形架构：集成所需的对外端口（抽象接口，不绑定具体实现）。

后端就绪前由 MockGateway 内存实现；后端就绪后换成 HttpGateway（httpx），
应用层与测试断言保持不变。
"""
from typing import Protocol

from ..parser.models import RawTransaction, Source


class ImportGateway(Protocol):
    def existing_external_ids(
        self, source: Source, external_ids: list[str]
    ) -> set[str]:
        """返回这些单号中已经存在于数据库的子集。"""
        ...

    def insert(self, rows: list[RawTransaction]) -> int:
        """写入一批交易，返回写入条数。"""
        ...
