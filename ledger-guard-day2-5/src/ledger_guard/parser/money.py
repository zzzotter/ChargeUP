"""金额转换：元 -> 整数分（Cent）。

SRS 2.3 硬约束：金额强制使用整数分，严禁浮点数（float）。
本模块全程使用 Decimal 与整数运算，不引入 float。
"""
from decimal import Decimal, InvalidOperation
from enum import Enum


class MoneyError(ValueError):
    """金额解析非法（格式错误、小数位超 2 位等）。"""


class Sign(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"


# 需要剥离的货币符号与千分位/空白字符
_STRIP_CHARS = ("¥", "￥", "$", "元", " ", "\t", ",", "，")


def _clean(value: str) -> str:
    text = str(value).strip()
    for ch in _STRIP_CHARS:
        text = text.replace(ch, "")
    return text.strip()


def yuan_to_cents(value: str) -> int:
    """把以“元”表示的金额字符串精确转换为整数分。

    支持："12.34"、"¥12.34"、"1,234.50"、" 12.3 "、"-35.00"、"12"。
    拒绝：非数字、超过 2 位小数（如 12.345）。
    注意：入参必须是字符串，调用方若传入 float 直接视为违规。
    """
    if isinstance(value, (int, float)):
        # 浮点入参本身就违反整数分约束，直接拒绝，避免精度污染
        raise MoneyError(f"金额必须以字符串传入，禁止数值类型: {value!r}")

    text = _clean(value)
    if not text:
        raise MoneyError("金额为空")

    sign = 1
    if text.startswith("-"):
        sign = -1
        text = text[1:]
    elif text.startswith("+"):
        text = text[1:]

    try:
        dec = Decimal(text)
    except InvalidOperation:
        raise MoneyError(f"非法金额格式: {value!r}") from None

    if not dec.is_finite():
        raise MoneyError(f"金额必须为有限数: {value!r}")

    # 小数位不得超过 2（分是最小单位）
    if dec.as_tuple().exponent < -2:
        raise MoneyError(f"金额精度超过分（最多2位小数）: {value!r}")

    cents = int((dec * 100).to_integral_value())
    return sign * cents


def is_zero(cents: int) -> bool:
    return cents == 0
