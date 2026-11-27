"""微信解析器测试（真实 xlsx：表头第18行，11列，数值金额经 Decimal 还原）。"""
from src.ledger_guard.parser import parse_bill
from src.ledger_guard.parser.models import Direction, Source

from .conftest import read_fixture


def _parse():
    return parse_bill(read_fixture("wechat", "wechat_normal.xlsx"), Source.WECHAT)


def test_header_and_counts():
    report = _parse()
    assert report.fmt == "xlsx"
    assert report.header_line_no == 18
    assert report.parsed_count == 8
    assert report.rejected_count == 0


def test_numeric_float_amount_recovered_exactly():
    first = _parse().parsed[0]
    assert first.amount_cents == 29667          # xlsx 数值 296.67 经 Decimal 还原
    assert first.external_id == "WO1"


def test_direction_classification():
    directions = [tx.direction for tx in _parse().parsed]
    assert directions.count(Direction.EXPENSE) == 3
    assert directions.count(Direction.INCOME) == 3
    assert directions.count(Direction.TRANSFER) == 2  # 提现 + 充值
