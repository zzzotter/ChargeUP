"""表格来源适配器：CSV 字节 / xlsx 字节 -> 统一的字符串行表。

核心解析逻辑只面对 list[list[str]]，与文件格式解耦（六边形架构的适配器）。
xlsx 中的 float 金额经 Decimal 还原为干净字符串，避免浮点污染；
datetime 统一格式化为字符串，与 CSV 走同一套时间解析。
"""
import csv
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import openpyxl

from .encoding import decode_bytes


@dataclass(frozen=True)
class TableData:
    rows: list[list[str]]
    fmt: str                       # "csv" | "xlsx"
    encoding: str
    had_decoding_errors: bool


def _xlsx_cell_to_str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, float):
        # 经 Decimal 还原，去掉浮点尾差，不把 float 直接送入金额逻辑
        return format(Decimal(str(value)), "f")
    if isinstance(value, int):
        return str(value)
    return str(value)


def _read_xlsx(raw: bytes) -> TableData:
    wb = openpyxl.load_workbook(
        io.BytesIO(raw), read_only=True, data_only=True
    )
    ws = wb.active
    rows = [
        [_xlsx_cell_to_str(v) for v in row]
        for row in ws.iter_rows(values_only=True)
    ]
    wb.close()
    return TableData(rows=rows, fmt="xlsx", encoding="xlsx",
                     had_decoding_errors=False)


def _read_csv(raw: bytes) -> TableData:
    decoded = decode_bytes(raw)
    rows = list(csv.reader(io.StringIO(decoded.text)))
    return TableData(rows=rows, fmt="csv", encoding=decoded.encoding,
                     had_decoding_errors=decoded.had_errors)


def read_table(raw: bytes) -> TableData:
    if not raw:
        return TableData(rows=[], fmt="csv", encoding="gb18030",
                         had_decoding_errors=False)
    if raw[:2] == b"PK":  # xlsx(zip) 魔数
        return _read_xlsx(raw)
    return _read_csv(raw)
