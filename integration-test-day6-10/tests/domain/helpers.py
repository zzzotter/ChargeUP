"""领域测试共享的交易工厂（构造整数分的脱敏数据）。"""
from datetime import datetime

from src.ledger_guard.parser.models import Direction, RawTransaction, Source


def make_tx(
    external_id: str,
    amount_cents: int,
    direction: Direction,
    item_name: str = "",
    counterparty: str = "",
    when: str = "2026-11-01 10:00:00",
    source: Source = Source.ALIPAY,
) -> RawTransaction:
    return RawTransaction(
        external_id=external_id,
        source=source,
        amount_cents=amount_cents,
        direction=direction,
        counterparty=counterparty,
        item_name=item_name,
        transacted_at=datetime.strptime(when, "%Y-%m-%d %H:%M:%S"),
    )
