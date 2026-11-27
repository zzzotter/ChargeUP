"""第 6 天：重复导入幂等、0 元跳过与拒识计数（经 MockGateway）。"""
from src.ledger_guard.domain import import_report
from src.ledger_guard.gateway import MockGateway
from src.ledger_guard.parser import parse_bill
from src.ledger_guard.parser.models import (
    Direction,
    ParseReport,
    RejectedRow,
    Source,
)

from ..conftest import read_fixture
from .helpers import make_tx


def test_first_then_second_import_is_idempotent():
    gateway = MockGateway()
    raw = read_fixture("alipay", "alipay_normal.csv")
    report = parse_bill(raw, Source.ALIPAY)

    first = import_report(report, gateway)
    assert first.inserted == report.parsed_count
    assert first.duplicated == 0

    second = import_report(report, gateway)  # 同一账单再次导入
    assert second.inserted == 0
    assert second.duplicated == report.parsed_count
    assert gateway.stored_count == report.parsed_count  # 库里没有翻倍


def test_partial_overlap():
    gateway = MockGateway()
    raw = read_fixture("alipay", "alipay_normal.csv")
    report = parse_bill(raw, Source.ALIPAY)

    import_report(report, gateway)
    # 构造一半旧单号、一半新单号的混合批次
    mixed = ParseReport(
        source=Source.ALIPAY, fmt="csv", encoding="gb18030",
        had_decoding_errors=False, header_line_no=24,
    )
    existing_tx = report.parsed[0]
    new_tx = make_tx("brand-new-id", 1200, Direction.EXPENSE, item_name="新消费")
    mixed.parsed = [existing_tx, new_tx]

    result = import_report(mixed, gateway)
    assert result.inserted == 1
    assert result.duplicated == 1


def test_zero_and_rejected_counted():
    gateway = MockGateway()
    report = ParseReport(
        source=Source.WECHAT, fmt="xlsx", encoding="utf-8",
        had_decoding_errors=False, header_line_no=18,
    )
    report.zero_amount = [
        make_tx("z0", 0, Direction.EXPENSE, item_name="解冻")
    ]
    report.rejected = [RejectedRow(20, "缺少金额列", "raw")]

    result = import_report(report, gateway)
    assert result.zero_skipped == 1
    assert result.rejected == 1
    assert result.inserted == 0
    assert gateway.stored_count == 0
