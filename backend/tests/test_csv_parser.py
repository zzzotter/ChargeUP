from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from app.domain.enums import Direction, ImportRowStatus, Source
from app.domain.services.csv_parser import decode_csv, parse_bill, parse_csv
from tests.support import (
    ALIPAY_CSV,
    BROKEN_CSV,
    WECHAT_CSV,
    make_xlsx,
    wechat_xlsx_bytes,
)

TZ = ZoneInfo("Asia/Shanghai")


def test_alipay_sample_parses():
    result = parse_csv(ALIPAY_CSV.read_bytes(), tzinfo=TZ)

    assert result.source is Source.ALIPAY
    assert result.issues == ()
    assert len(result.rows) == 5

    first = result.rows[0]
    assert first.amount_cents == 3250
    assert first.merchant == "星巴克"
    assert first.external_id == "2026110122001412345678901234"
    # 09:15 Asia/Shanghai -> 01:15 UTC
    assert first.occurred_at == datetime(2026, 11, 2, 1, 15, tzinfo=UTC)

    assert [row.direction for row in result.rows] == [
        Direction.EXPENSE,
        Direction.EXPENSE,
        Direction.EXPENSE,
        Direction.TRANSFER,
        Direction.INCOME,
    ]


def test_wechat_sample_parses_and_skips_transfer():
    result = parse_csv(WECHAT_CSV.read_bytes(), tzinfo=TZ)

    assert result.source is Source.WECHAT
    assert result.issues == ()
    assert len(result.rows) == 4
    assert result.rows[0].amount_cents == 3250
    assert result.rows[2].direction is Direction.TRANSFER


def test_gbk_encoded_file_is_decoded():
    content = WECHAT_CSV.read_text(encoding="utf-8").encode("gb18030")
    decoded, encoding = decode_csv(content)
    assert encoding == "gb18030"
    assert "星巴克" in decoded

    result = parse_csv(content, tzinfo=TZ)
    assert len(result.rows) == 4


def test_broken_rows_are_rejected_without_crashing():
    result = parse_csv(BROKEN_CSV.read_bytes(), tzinfo=TZ)

    assert len(result.rows) == 1
    assert result.skipped_lines == 1
    statuses = [issue.status for issue in result.issues]
    assert statuses.count(ImportRowStatus.MISSING_EXTERNAL_ID) == 2
    assert ImportRowStatus.INVALID_AMOUNT in statuses
    assert ImportRowStatus.INVALID_TIME in statuses
    # 拒识原文必须脱敏
    assert all("42000000000000000002" not in issue.raw for issue in result.issues)


def test_missing_header():
    result = parse_csv("随便写点什么\n1,2\n".encode(), tzinfo=TZ)
    assert result.rows == ()
    assert result.issues[0].status is ImportRowStatus.MISSING_HEADER


def test_missing_external_id_column():
    content = "交易时间,金额(元)\n2026-11-02 09:15:00,32.50\n".encode()
    result = parse_csv(content, tzinfo=TZ)
    assert result.rows == ()
    assert result.issues[0].status is ImportRowStatus.MISSING_COLUMNS


def test_garbage_bytes_do_not_crash():
    content = b"\xff\xfe\xff" + "交易时间,金额(元),交易单号\n".encode("gb18030")
    result = parse_csv(content, tzinfo=TZ)
    assert result.rows == ()
    assert result.issues  # 至少有表头识别失败的提示


def test_empty_file():
    result = parse_csv(b"", tzinfo=TZ)
    assert result.rows == ()
    assert result.issues[0].status is ImportRowStatus.MISSING_HEADER


def test_wechat_xlsx_parses_numeric_and_datetime_cells():
    result = parse_bill(wechat_xlsx_bytes(), tzinfo=TZ)

    assert result.source is Source.WECHAT
    assert result.encoding == "xlsx"
    assert result.issues == ()
    assert len(result.rows) == 4

    first = result.rows[0]
    assert first.amount_cents == 3250
    assert first.merchant == "星巴克"
    assert first.external_id == "4200001234202611020000000001"
    # 09:15 Asia/Shanghai -> 01:15 UTC
    assert first.occurred_at == datetime(2026, 11, 2, 1, 15, tzinfo=UTC)

    assert result.rows[2].direction is Direction.TRANSFER
    assert result.rows[3].amount_cents == 2860


def test_alipay_xlsx_with_text_cells_parses():
    content = make_xlsx(
        [
            ["支付宝交易记录明细查询"],
            ["导出时间:[2026-12-01 09:00:00]"],
            ["交易号", "交易创建时间", "交易对方", "商品名称", "金额（元）", "收/支", "类型"],
            [
                "2026110122001412345678901234",
                "2026-11-02 09:15:00",
                "星巴克",
                "拿铁",
                "¥32.50",
                "支出",
                "即时到账交易",
            ],
        ]
    )
    result = parse_bill(content, tzinfo=TZ)

    assert result.source is Source.ALIPAY
    assert result.encoding == "xlsx"
    assert len(result.rows) == 1
    assert result.rows[0].amount_cents == 3250


def test_corrupt_xlsx_is_reported_without_crashing():
    result = parse_bill(b"PK\x03\x04broken", tzinfo=TZ)

    assert result.rows == ()
    assert result.issues[0].status is ImportRowStatus.MISSING_HEADER
    assert "XLSX" in result.issues[0].detail


def test_legacy_xls_is_rejected_with_hint():
    result = parse_bill(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1rest", tzinfo=TZ)

    assert result.rows == ()
    assert result.issues[0].status is ImportRowStatus.MISSING_HEADER
    assert ".xls" in result.issues[0].detail
