"""金额元转分测试（整数分、零浮点底线）。"""
import pytest

from src.ledger_guard.parser.money import MoneyError, yuan_to_cents


@pytest.mark.parametrize("text,expected", [
    ("35.00", 3500),
    ("28.80", 2880),
    ("¥12.34", 1234),
    ("1,234.50", 123450),
    ("12.3", 1230),
    ("-36.00", -3600),
    ("12", 1200),
    ("0.01", 1),
    ("  7.00  ", 700),
])
def test_yuan_to_cents(text, expected):
    assert yuan_to_cents(text) == expected


@pytest.mark.parametrize("bad", ["12.345", "", "abc", "¥", "1.2.3"])
def test_invalid_text_raises(bad):
    with pytest.raises(MoneyError):
        yuan_to_cents(bad)


def test_numeric_input_rejected():
    # 浮点/数值入参本身违反整数分约束，必须拒绝
    with pytest.raises(MoneyError):
        yuan_to_cents(12.34)
    with pytest.raises(MoneyError):
        yuan_to_cents(0)
