"""日志脱敏配置（SRS 5.2）。

任何进入日志的文本都会先经过 domain.redaction.redact_text，
确保导入失败的原始账单片段、交易单号不会以明文落盘。
"""

from __future__ import annotations

import logging

from app.domain.redaction import redact_text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_text(record.msg, max_length=2000)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    redact_text(arg, max_length=500) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    key: redact_text(value, max_length=500) if isinstance(value, str) else value
                    for key, value in record.args.items()
                }
        return True


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    handler.addFilter(RedactingFilter())

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
