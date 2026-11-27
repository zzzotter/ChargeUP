"""测试共用的样例账单路径与 XLSX 构造器。"""

from __future__ import annotations

import io
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"

ALIPAY_CSV = FIXTURES / "alipay_sample.csv"
WECHAT_CSV = FIXTURES / "wechat_sample.csv"
BROKEN_CSV = FIXTURES / "broken_rows.csv"


def make_xlsx(rows: Iterable[Sequence[object]]) -> bytes:
    """把二维数据写成 xlsx 字节流，用于测试单元格类型（数字/日期）转换。"""
    from openpyxl import Workbook

    workbook = Workbook()
    sheet = workbook.active
    for row in rows:
        sheet.append(list(row))
    buffer = io.BytesIO()
    workbook.save(buffer)
    workbook.close()
    return buffer.getvalue()


def wechat_xlsx_bytes() -> bytes:
    """模拟微信导出的账单：说明行 + 表头 + 数字金额 + 日期时间单元格。"""

    def row(day, hour, minute, merchant, product, amount, txn_id, trade_type="商户消费"):
        return [
            datetime(2026, 11, day, hour, minute),
            trade_type,
            merchant,
            product,
            "支出",
            amount,
            "零钱",
            "支付成功",
            txn_id,
            "",
            "/",
        ]

    return make_xlsx(
        [
            ["微信支付账单明细"],
            ["微信昵称：[ledger]"],
            ["起始时间：[2026-11-01 00:00:00] 终止时间：[2026-11-30 23:59:59]"],
            ["导出类型：[全部]"],
            ["导出时间：[2026-12-01 10:00:00]"],
            ["共4笔记录"],
            [],
            ["----------------------微信支付账单明细列表--------------------"],
            [
                "交易时间",
                "交易类型",
                "交易对方",
                "商品",
                "收/支",
                "金额(元)",
                "支付方式",
                "当前状态",
                "交易单号",
                "商户单号",
                "备注",
            ],
            row(2, 9, 15, "星巴克", "拿铁", 32.5, "4200001234202611020000000001"),
            row(3, 12, 20, "京东", "数据线", 49, "4200001234202611030000000002"),
            row(4, 8, 0, "李四", "转账备注", 200, "4200001234202611040000000003", "转账"),
            row(5, 19, 30, "美团", "外卖", 28.6, "4200001234202611050000000004"),
            ["以上为全部交易记录"],
        ]
    )
