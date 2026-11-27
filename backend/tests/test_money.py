from __future__ import annotations

from decimal import Decimal

import pytest

from app.domain.money import (
    InvalidAmountError,
    format_cents,
    parse_amount_to_cents,
    require_positive_cents,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("32.50", 3250),
        ("¥1,234.56", 123456),
        ("￥12.3", 1230),
        ("-12.30", -1230),
        ("(12.30)", -1230),
        ("1.234,56", 123456),
        ("12,345", 1234500),  # 千分位写法：一万二千三百四十五元
        ("0.005", 1),
        ("199", 19900),
        ("32.50元", 3250),
        (Decimal("19.99"), 1999),
        (3250, 3250),
    ],
)
def test_parse_amount(raw, expected):
    assert parse_amount_to_cents(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", None, "¥", "12.3.4"])
def test_parse_amount_rejects_invalid(raw):
    with pytest.raises(InvalidAmountError):
        parse_amount_to_cents(raw)


def test_format_cents():
    assert format_cents(3250) == "32.50"
    assert format_cents(19900) == "199.00"
    assert format_cents(-5) == "-0.05"
    assert format_cents(0) == "0.00"


def test_require_positive_cents():
    assert require_positive_cents(0) == 0
    with pytest.raises(InvalidAmountError):
        require_positive_cents(-1)
    with pytest.raises(InvalidAmountError):
        require_positive_cents(1.5)  # type: ignore[arg-type]
