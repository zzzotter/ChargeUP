"""微信账单解析配置（已按真实导出 xlsx 校准）。

真实文件：xlsx，表头位于第 18 行，共 11 列；
收/支取值：支出 / 收入 / "/"（中性交易，如充值、提现）。
"""
from .base import BaseParser, ColumnSpec, PlatformConfig
from .models import Direction, Source

_COLUMNS = (
    ColumnSpec("transacted_at", ("交易时间",)),
    ColumnSpec("type", ("交易类型",)),
    ColumnSpec("counterparty", ("交易对方",)),
    ColumnSpec("item_name", ("商品",)),
    ColumnSpec("direction", ("收/支",)),
    ColumnSpec("amount", ("金额",)),
    ColumnSpec("status", ("当前状态",)),
    ColumnSpec("external_id", ("交易单号",)),
    ColumnSpec("note", ("备注",)),
)

_NEUTRAL_VALUES = ("/",)

_TRANSFER_KEYWORDS = (
    "转账", "零钱", "提现", "红包", "还款", "充值", "理财",
)

_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y/%m/%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y/%m/%d %H:%M",
)


class WechatParser(BaseParser):
    config = PlatformConfig(
        source=Source.WECHAT,
        expected_header_lines=18,
        columns=_COLUMNS,
        direction_map={"支出": Direction.EXPENSE, "收入": Direction.INCOME},
        neutral_direction_values=_NEUTRAL_VALUES,
        transfer_keywords=_TRANSFER_KEYWORDS,
        datetime_formats=_DATETIME_FORMATS,
    )
