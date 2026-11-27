"""支付宝解析器测试（真实格式：表头第24行，13列）。"""
from src.ledger_guard.parser import parse_bill
from src.ledger_guard.parser.models import Direction, Source

from .conftest import read_fixture


def _parse():
    return parse_bill(read_fixture("alipay", "alipay_normal.csv"), Source.ALIPAY)


def test_header_and_counts():
    report = _parse()
    assert report.header_line_no == 24
    assert report.total_data_rows == 10
    assert report.parsed_count == 8
    assert report.zero_amount_count == 2
    assert report.rejected_count == 0
    assert report.had_decoding_errors is False


def test_amount_to_cents_and_id_text():
    first = _parse().parsed[0]
    assert first.amount_cents == 3500           # 35.00 元
    assert first.external_id == "AO1"           # 单号文本保留
    assert first.source == Source.ALIPAY


def test_direction_classification():
    report = _parse()
    all_tx = report.parsed + report.zero_amount
    directions = [tx.direction for tx in all_tx]
    assert directions.count(Direction.EXPENSE) == 4
    assert directions.count(Direction.INCOME) == 1
    assert directions.count(Direction.TRANSFER) == 5


def test_zero_amount_records_excluded_from_money_stats():
    zero = _parse().zero_amount
    assert len(zero) == 2
    assert all(tx.amount_cents == 0 for tx in zero)
    assert all(tx.direction == Direction.TRANSFER for tx in zero)
