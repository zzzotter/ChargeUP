"""导入网关的真实 HTTP 适配器（后端交付后启用，当前为占位骨架）。

后端 FastAPI 就绪并确认 OpenAPI 后：
1. 用 httpx 实现下面两个方法，端点路径/请求体以真实 OpenAPI 为准；
2. 在应用与测试中把 MockGateway 替换为 HttpGateway(base_url)；
3. domain 层与全部既有测试断言保持不变，无需修改。

真实联调时还需在此核对：响应金额是否整数分、错误状态码与统一错误体。
"""
from ..parser.models import RawTransaction, Source


class HttpGateway:
    def __init__(self, base_url: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def existing_external_ids(
        self, source: Source, external_ids: list[str]
    ) -> set[str]:
        # TODO(后端就绪): POST 导入预检/查询端点，返回已存在单号
        raise NotImplementedError("待 OpenAPI 确认后实现：批量查询已存在单号")

    def insert(self, rows: list[RawTransaction]) -> int:
        # TODO(后端就绪): POST 导入写入端点，返回成功写入条数
        raise NotImplementedError("待 OpenAPI 确认后实现：导入写入")
