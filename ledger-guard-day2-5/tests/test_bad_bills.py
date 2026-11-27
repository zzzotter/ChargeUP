"""坏账单测试：空行、缺列、乱码、致命表头缺失。"""
import pytest

from src.ledger_guard.parser import parse_bill
from src.ledger_guard.parser.base import ParseError
from src.ledger_guard.parser.models import Source

from .conftest import read_fixture


def test_empty_rows_skipped():
    a = parse_bill(read_fixture("alipay", "alipay_empty_rows.csv"), Source.ALIPAY)
    assert a.parsed_count == 2
    assert a.rejected_count == 0

    w = parse_bill(read_fixture("wechat", "wechat_empty_rows.xlsx"), Source.WECHAT)
    assert w.parsed_count == 2
    assert w.rejected_count == 0


def test_missing_columns_rejected_but_continue():
    a = parse_bill(read_fixture("alipay", "alipay_missing_cols.csv"), Source.ALIPAY)
    assert a.parsed_count == 2
    assert a.rejected_count == 1

    w = parse_bill(read_fixture("wechat", "wechat_missing_cols.xlsx"), Source.WECHAT)
    assert w.parsed_count == 2
    assert w.rejected_count == 1


def test_garbled_decoded_with_replace_and_continue():
    a = parse_bill(read_fixture("alipay", "alipay_garbled.csv"), Source.ALIPAY)
    assert a.had_decoding_errors is True
    assert a.parsed_count == 4
    assert a.rejected_count == 1  # 末尾乱码行无法解析

    w = parse_bill(read_fixture("wechat", "wechat_garbled.csv"), Source.WECHAT)
    assert w.had_decoding_errors is True
    assert w.parsed_count == 4
    assert w.rejected_count == 1


def test_missing_header_raises_fatal():
    with pytest.raises(ParseError):
        parse_bill(b"hello\nworld\nfoo,bar,baz\n", Source.ALIPAY)
