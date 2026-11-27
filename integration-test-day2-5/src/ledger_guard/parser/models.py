"""解析层数据模型与枚举（对齐第 1 天冻结的接口约定，按真实账单校准）。"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Source(str, Enum):
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"


class Direction(str, Enum):
    """资金流向：TRANSFER 在统计月度支出时强制排除。

    真实账单的“不计收支/中性”（充值、提现、还款、信用借还、理财等）
    当前统一归入 TRANSFER 以保证不计入支出；是否新增 NON_CASH 枚举待团队确认。
    """

    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"


@dataclass
class RawTransaction:
    """解析得到的待入库原始交易（category_id 由后续分类引擎填充）。"""

    external_id: str            # 外部交易单号，文本保留
    source: Source
    amount_cents: int           # 非负整数分；方向由 direction 表达
    direction: Direction
    counterparty: str           # 交易对方
    item_name: str              # 商品名称（分类关键词匹配的输入）
    transacted_at: datetime
    status: str = ""
    note: str = ""
    category_id: int | None = None
    refund_of_external_id: str | None = None


@dataclass
class RejectedRow:
    line_no: int
    reason: str
    raw_line: str


@dataclass
class ParseReport:
    source: Source
    fmt: str
    encoding: str
    had_decoding_errors: bool
    header_line_no: int
    total_data_rows: int = 0
    parsed: list[RawTransaction] = field(default_factory=list)
    zero_amount: list[RawTransaction] = field(default_factory=list)
    rejected: list[RejectedRow] = field(default_factory=list)

    @property
    def parsed_count(self) -> int:
        return len(self.parsed)

    @property
    def zero_amount_count(self) -> int:
        return len(self.zero_amount)

    @property
    def rejected_count(self) -> int:
        return len(self.rejected)
