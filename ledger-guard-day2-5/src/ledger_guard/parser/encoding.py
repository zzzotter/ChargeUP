"""账单文件编码探测与解码。

SRS F-P0-01：账单为 GBK 编码，需兼容 UTF-8/BOM 等变体。
GB18030 是 GBK 的超集，优先用它兜底中文账单。
"""
from dataclasses import dataclass

# 严格解码候选顺序（BOM 优先）
_CANDIDATES = ("utf-8-sig", "utf-8", "gb18030")
_FALLBACK = "gb18030"


@dataclass(frozen=True)
class DecodeResult:
    text: str
    encoding: str
    had_errors: bool  # 严格解码失败、使用 replace 兜底时为 True


def decode_bytes(raw: bytes) -> DecodeResult:
    if not raw:
        return DecodeResult(text="", encoding=_FALLBACK, had_errors=False)

    for enc in _CANDIDATES:
        try:
            return DecodeResult(text=raw.decode(enc), encoding=enc, had_errors=False)
        except UnicodeDecodeError:
            continue

    # 全部严格解码失败：用 GB18030 替换兜底，保证流程不崩溃
    text = raw.decode(_FALLBACK, errors="replace")
    return DecodeResult(text=text, encoding=_FALLBACK, had_errors=True)
