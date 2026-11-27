"""导入网关的内存模拟实现（后端交付前使用）。

用一个集合模拟数据库中已有的 external_id，行为对齐“幂等去重”预期：
- 已存在的单号再次导入不会重复写入；
- insert 只写入此前不存在的单号。
"""
from ..parser.models import RawTransaction, Source


class MockGateway:
    def __init__(self) -> None:
        # key: (source, external_id)，全局唯一
        self._stored: set[tuple[Source, str]] = set()

    def existing_external_ids(
        self, source: Source, external_ids: list[str]
    ) -> set[str]:
        return {
            ext for ext in external_ids if (source, ext) in self._stored
        }

    def insert(self, rows: list[RawTransaction]) -> int:
        count = 0
        for tx in rows:
            key = (tx.source, tx.external_id)
            if key not in self._stored:
                self._stored.add(key)
                count += 1
        return count

    @property
    def stored_count(self) -> int:
        return len(self._stored)
