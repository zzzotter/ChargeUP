from __future__ import annotations

import logging

from app.domain.redaction import mask_external_id, redact_text
from app.infrastructure.logging import RedactingFilter


def test_mask_external_id_keeps_edges():
    value = "4200001234202611020000000001"
    masked = mask_external_id(value)
    assert masked.startswith("4200")
    assert masked.endswith("0001")
    assert "*" in masked
    assert len(masked) == len(value)
    assert mask_external_id("123") == "***"


def test_redact_text_masks_ids_and_phones():
    text = "交易单号 4200001234202611020000000001，手机 13812345678"
    result = redact_text(text)
    assert "4200001234202611020000000001" not in result
    assert "13812345678" not in result


def test_logging_filter_redacts_message():
    record = logging.LogRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "导入失败 row=4200001234202611020000000001",
        None,
        None,
    )
    RedactingFilter().filter(record)
    assert "4200001234202611020000000001" not in record.getMessage()


def test_logging_filter_redacts_args():
    record = logging.LogRecord(
        "test",
        logging.INFO,
        __file__,
        1,
        "order=%s",
        ("4200001234202611020000000001",),
        None,
    )
    RedactingFilter().filter(record)
    assert "4200001234202611020000000001" not in record.getMessage()
