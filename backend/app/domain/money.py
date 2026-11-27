"""金额工具。

硬约束（SRS 2.3）：所有金额计算与存储强制使用整数分（Cent），严禁浮点。
本模块是整个系统唯一允许进行「元 <-> 分」转换的地方，并负责金额上限校验，
保证超出十进制安全范围（如 1e999999999）或存储上限的输入统一转为 InvalidAmountError。
"""

from __future__ import annotations

import unicodedata
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

_CENT = Decimal("0.01")
_ONE = Decimal("1")
_STRIP_CHARS = " \t\r\n\u00a0\u3000"
_CURRENCY_MARKS = ("¥", "￥", "$", "€", "£", "元", "RMB", "CNY", "人民币")

# 单笔金额上限（整数分）：10^12 分 = 100 亿元，远小于 BIGINT 上限，避免训练/攻击性输入
MAX_AMOUNT_CENTS = 10**12
# Decimal 指数绝对值上限，用于快速拒绝 1e999999999 之类输入
_MAX_EXPONENT = 15


class InvalidAmountError(ValueError):
    """金额格式无法识别或超出可处理范围。"""


def _normalize_separators(text: str) -> str:
    """把千分位/小数点写法规整为 Python Decimal 可解析的形式。"""
    has_dot = "." in text
    has_comma = "," in text
    if has_dot and has_comma:
        if text.rfind(",") > text.rfind("."):  # 1.234,56 -> 1234.56
            return text.replace(".", "").replace(",", ".")
        return text.replace(",", "")  # 1,234.56 -> 1234.56
    if has_comma:
        parts = text.split(",")
        if len(parts) == 2 and 1 <= len(parts[1]) <= 2:  # 12,3 -> 12.3
            return f"{parts[0]}.{parts[1]}"
        return text.replace(",", "")  # 12,345 -> 12345
    return text


def _ensure_range(cents: int, raw: object) -> int:
    if abs(cents) > MAX_AMOUNT_CENTS:
        raise InvalidAmountError(
            f"金额超出可处理范围（单笔上限 {MAX_AMOUNT_CENTS // 100 // 100000000} 亿元）：{raw!r}"
        )
    return cents


def _decimal_to_cents(value: Decimal, raw: object) -> int:
    """Decimal -> 整数分；指数越界或量化溢出统一转为 InvalidAmountError。"""
    try:
        if abs(value.adjusted()) > _MAX_EXPONENT:
            raise InvalidAmountError(f"金额超出可处理范围：{raw!r}")
        cents = int((value * 100).quantize(_ONE, rounding=ROUND_HALF_UP))
    except InvalidAmountError:
        raise
    except (ArithmeticError, ValueError) as exc:
        raise InvalidAmountError(f"金额超出可处理范围：{raw!r}") from exc
    return _ensure_range(cents, raw)


def parse_amount_to_cents(raw: str | int | Decimal | None) -> int:
    """把用户输入/账单文本转换为整数分。

    >>> parse_amount_to_cents("¥1,234.56")
    123456
    >>> parse_amount_to_cents("-12.3")
    -1230
    """
    if raw is None:
        raise InvalidAmountError("金额为空")
    if isinstance(raw, bool):
        raise InvalidAmountError(f"无法识别的金额：{raw!r}")
    if isinstance(raw, int):
        return _ensure_range(raw, raw)
    if isinstance(raw, Decimal):
        return _decimal_to_cents(raw, raw)

    # 中文输入法常产生全角数字/全角小数点，先做 NFKC 归一化
    text = unicodedata.normalize("NFKC", str(raw))
    text = text.strip(_STRIP_CHARS).replace("\u00a0", "").replace(" ", "")
    if not text:
        raise InvalidAmountError("金额为空")

    negative = False
    if text.startswith("(") and text.endswith(")"):  # 会计负数写法 (12.30)
        negative = True
        text = text[1:-1]
    for mark in _CURRENCY_MARKS:
        text = text.replace(mark, "")
    text = text.strip(_STRIP_CHARS)
    if text.startswith("-"):
        negative = True
        text = text[1:]
    text = text.lstrip("+")
    if not text:
        raise InvalidAmountError(f"无法识别的金额：{raw!r}")

    text = _normalize_separators(text)
    try:
        value = Decimal(text)
    except (InvalidOperation, ArithmeticError, ValueError) as exc:
        raise InvalidAmountError(f"无法识别的金额：{raw!r}") from exc

    cents = _decimal_to_cents(value, raw)
    return -cents if negative else cents


def require_positive_cents(cents: int) -> int:
    """校验并返回非负整数分。"""
    if not isinstance(cents, int) or isinstance(cents, bool):
        raise InvalidAmountError("金额必须为整数分")
    if cents < 0:
        raise InvalidAmountError("金额不能为负数，收支方向由 direction 表达")
    return _ensure_range(cents, cents)


def format_cents(cents: int) -> str:
    """整数分 -> 展示用字符串（两位小数，永不使用浮点）。"""
    if not isinstance(cents, int):
        raise InvalidAmountError("金额必须为整数分")
    sign = "-" if cents < 0 else ""
    value = abs(cents)
    return f"{sign}{value // 100}.{value % 100:02d}"


def cents_to_decimal(cents: int) -> Decimal:
    return (Decimal(cents) / 100).quantize(_CENT)
