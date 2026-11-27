"""脱敏工具（纯函数，无框架依赖）。

SRS 5.2：导入的 CSV 原始内容需脱敏后再进入日志；账单截图原图不得落到服务端日志。
所有需要落日志的原始文本都必须先经过本模块。
"""

from __future__ import annotations

import re

# 交易单号/订单号：11 位以上纯数字（支付宝 28 位、微信 32 位）
_LONG_DIGITS = re.compile(r"\d{11,}")
# 长串字母数字混合单号
_LONG_TOKEN = re.compile(r"[A-Za-z0-9]{16,}")
# 手机号
_PHONE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")


def mask_external_id(value: str) -> str:
    """遮蔽单号中段，只保留前 4 位与后 4 位。"""
    text = (value or "").strip()
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:4]}{'*' * (len(text) - 8)}{text[-4:]}"


def _mask_token(match: re.Match[str]) -> str:
    return mask_external_id(match.group(0))


def redact_text(value: str, *, max_length: int = 300) -> str:
    """对可能包含账单原文的文本做脱敏并截断。"""
    text = (value or "").replace("\r", " ").replace("\n", " ")
    text = _PHONE.sub(lambda m: m.group(0)[:3] + "****" + m.group(0)[-4:], text)
    text = _LONG_TOKEN.sub(_mask_token, text)
    text = _LONG_DIGITS.sub(_mask_token, text)
    text = " ".join(text.split())
    if len(text) > max_length:
        text = text[:max_length] + "…"
    return text
