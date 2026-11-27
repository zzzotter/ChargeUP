"""第 11 天检查（二）：日志脱敏，单号/手机号不得明文落日志。"""
import logging

from app.domain.redaction import mask_external_id, redact_text
from app.infrastructure.logging import RedactingFilter

LONG_ID = "4200001234202611020000000001"


def test_mask_keeps_edges_and_hides_middle():
    masked = mask_external_id(LONG_ID)
    assert masked.startswith("4200") and masked.endswith("0001")
    assert "*" in masked and len(masked) == len(LONG_ID)
    assert mask_external_id("123") == "***"


def test_redact_text_hides_id_and_phone():
    text = f"单号 {LONG_ID}，手机 13812345678"
    out = redact_text(text)
    assert LONG_ID not in out and "13812345678" not in out


def test_log_filter_redacts_message_and_args():
    record = logging.LogRecord("t", logging.INFO, __file__, 1,
                               f"导入失败 row={LONG_ID}", None, None)
    RedactingFilter().filter(record)
    assert LONG_ID not in record.getMessage()

    record_args = logging.LogRecord("t", logging.INFO, __file__, 1,
                                    "order=%s", (LONG_ID,), None)
    RedactingFilter().filter(record_args)
    assert LONG_ID not in record_args.getMessage()
