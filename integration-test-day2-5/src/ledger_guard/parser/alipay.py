"""支付宝账单解析配置（已按真实导出 CSV 校准）。

真实文件：GBK/GB18030，表头位于第 24 行，共 13 列；
收/支取值：支出 / 收入 / 不计收支。
"""
from .base import BaseParser, ColumnSpec, PlatformConfig
from .models import Direction, Source

_COLUMNS = (
    ColumnSpec("transacted_at", ("交易时间",)),
    ColumnSpec("type", ("交易分类",)),
    ColumnSpec("counterparty", ("交易对方",)),
    ColumnSpec("item_name", ("商品说明",)),
    ColumnSpec("direction", ("收/支",)),
    ColumnSpec("amount", ("金额",)),
    ColumnSpec("status", ("交易状态",)),
    ColumnSpec("external_id", ("交易订单号",)),
    ColumnSpec("note", ("备注",)),
)

_NEUTRAL_VALUES = ("不计收支",)

# 中性兜底关键字（充值/还款/信用借还/理财等）
_TRANSFER_KEYWORDS = (
    "转账", "提现", "还款", "信用借还", "充值", "理财", "余额宝", "红包", "账户存取",
)

_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
)


class AlipayParser(BaseParser):
    config = PlatformConfig(
        source=Source.ALIPAY,
        expected_header_lines=24,
        columns=_COLUMNS,
        direction_map={"支出": Direction.EXPENSE, "收入": Direction.INCOME},
        neutral_direction_values=_NEUTRAL_VALUES,
        transfer_keywords=_TRANSFER_KEYWORDS,
        datetime_formats=_DATETIME_FORMATS,
    )
