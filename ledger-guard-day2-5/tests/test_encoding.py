"""编码探测测试。"""
from src.ledger_guard.parser.encoding import decode_bytes


def test_utf8_bom_detected():
    r = decode_bytes("你好".encode("utf-8-sig"))
    assert r.encoding == "utf-8-sig"
    assert r.had_errors is False
    assert r.text == "你好"


def test_gbk_chinese_falls_back_to_gb18030():
    r = decode_bytes("微信账单".encode("gbk"))
    assert r.encoding == "gb18030"
    assert r.had_errors is False
    assert r.text == "微信账单"


def test_invalid_bytes_replaced_not_crash():
    r = decode_bytes(b"abc\xffdef")
    assert r.had_errors is True
    assert "abc" in r.text and "def" in r.text


def test_empty_bytes():
    r = decode_bytes(b"")
    assert r.text == ""
    assert r.had_errors is False
