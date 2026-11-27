"""测评报告问题清单的回归用例（每条问题至少一个断言）。"""

from __future__ import annotations

import logging
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import BigInteger

from app.application.periods import resolve_timezone
from app.config import Settings
from app.domain.entities import Transaction
from app.domain.enums import Direction, Source
from app.domain.money import MAX_AMOUNT_CENTS, InvalidAmountError, parse_amount_to_cents
from app.domain.services.refunds import detect_refund_pairs
from app.infrastructure.models import BudgetEventModel, BudgetModel, TransactionModel
from tests.support import ALIPAY_CSV

BASE = "/api/v1"


def create(
    client,
    merchant: str = "星巴克",
    amount: int = 3250,
    occurred_at: str = "2026-11-20T12:00:00+08:00",
    **extra,
):
    return client.post(
        f"{BASE}/transactions",
        json={
            "merchant": merchant,
            "amount": amount,
            "direction": "EXPENSE",
            "occurredAt": occurred_at,
            **extra,
        },
    )


def create_at(client, *, merchant, amount, occurred_at, direction="EXPENSE"):
    response = client.post(
        f"{BASE}/transactions",
        json={
            "merchant": merchant,
            "amount": amount,
            "occurredAt": occurred_at,
            "direction": direction,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def make_txn(
    txn_id: int, cents: int, direction: Direction, *, merchant: str, days: float = 0, note: str = ""
) -> Transaction:
    return Transaction(
        id=txn_id,
        source=Source.MANUAL,
        external_id=f"T{txn_id}",
        amount_cents=cents,
        direction=direction,
        occurred_at=datetime(2027, 3, 1, tzinfo=UTC) + timedelta(days=days),
        merchant=merchant,
        note=note,
    )


# --------------------------------------------------------------- F1 退款误判


def test_ordinary_income_is_not_treated_as_refund(api_client):
    create_at(
        api_client,
        merchant="淘宝",
        amount=10000,
        occurred_at="2027-03-02T10:00:00+08:00",
    )
    create_at(
        api_client,
        merchant="工资发放",
        amount=10000,
        occurred_at="2027-03-03T10:00:00+08:00",
        direction="INCOME",
    )

    summary = api_client.get(f"{BASE}/stats/summary", params={"month": "2027-03"}).json()
    assert summary["totalExpense"] == 10000
    assert summary["totalIncome"] == 10000
    assert summary["excludedRefundCount"] == 0


def test_refund_keyword_allows_pairing_with_different_merchant():
    expense = make_txn(1, 3250, Direction.EXPENSE, merchant="淘宝")
    refund = make_txn(2, 3250, Direction.INCOME, merchant="退款到账", days=2)
    assert len(detect_refund_pairs([expense, refund])) == 1


def test_empty_merchant_income_is_not_paired():
    expense = make_txn(1, 3250, Direction.EXPENSE, merchant="")
    income = make_txn(2, 3250, Direction.INCOME, merchant="", days=1)
    assert detect_refund_pairs([expense, income]) == []


# ------------------------------------------------------- S1 金额溢出 / S2 上限


@pytest.mark.parametrize("raw", ["1e999999999", Decimal("1e999999999"), "9" * 40])
def test_overflow_amount_is_rejected(raw):
    with pytest.raises(InvalidAmountError):
        parse_amount_to_cents(raw)


def test_overflow_amount_returns_422(api_client):
    response = create(api_client, amount=MAX_AMOUNT_CENTS + 1)
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_overflow_amount_in_csv_only_rejects_row(api_client):
    content = (
        "交易时间,金额(元),交易单号\n"
        "2027-08-01 10:00:00,1e999999999,OVF-001\n"
        "2027-08-02 10:00:00,12.00,OK-001\n"
    ).encode()
    response = api_client.post(
        f"{BASE}/imports/csv", files={"file": ("overflow.csv", content, "text/csv")}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 1
    assert body["failed"] == 1
    assert len(body["failures"]) == 1


def test_large_amount_is_stored_and_capped(api_client):
    ok = create(api_client, merchant="大额商户", amount=300_000_000_000)
    assert ok.status_code == 201
    assert ok.json()["amount"] == 300_000_000_000

    too_big = create(api_client, merchant="超大额", amount=10_000_000_000_01)
    assert too_big.status_code == 422
    assert MAX_AMOUNT_CENTS == 10**12


def test_amount_columns_are_bigint():
    assert isinstance(TransactionModel.__table__.c.amount_cents.type, BigInteger)
    assert isinstance(BudgetModel.__table__.c.amount_cents.type, BigInteger)
    assert isinstance(BudgetEventModel.__table__.c.spent_cents.type, BigInteger)


# ------------------------------------------------------------- S3 .env 生效


def test_settings_load_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "DATABASE_URL=sqlite+pysqlite:///env_should_be_used.db\n"
        "APP_TIMEZONE=Pacific/Kiritimati\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    for key in ("DATABASE_URL", "APP_TIMEZONE", "API_TOKEN", "DOTENV_PATH"):
        monkeypatch.delenv(key, raising=False)

    snapshot = dict(os.environ)
    try:
        settings = Settings.from_env()
    finally:
        os.environ.clear()
        os.environ.update(snapshot)

    assert settings.database_url.endswith("env_should_be_used.db")
    assert settings.timezone == "Pacific/Kiritimati"


# --------------------------------------------------------- S4 拒识计数不失真


def test_rejected_total_is_not_truncated(api_client):
    rows = [f"2026-11-02 09:15:00,bad{i},{42000000000000000000 + i}" for i in range(80)]
    content = ("交易时间,金额(元),交易单号\n" + "\n".join(rows) + "\n").encode()
    body = api_client.post(
        f"{BASE}/imports/csv", files={"file": ("many_bad.csv", content, "text/csv")}
    ).json()

    assert body["failed"] == 80
    assert len(body["failures"]) == 50


# --------------------------------------------------------------- S5 鉴权


def test_token_auth_protects_financial_endpoints(client_factory):
    with client_factory(api_token="s3cret-token") as client:
        assert client.get(f"{BASE}/transactions").status_code == 401
        assert client.get(f"{BASE}/health").status_code == 200

        unauthorized = client.get(f"{BASE}/transactions")
        assert unauthorized.json()["code"] == "UNAUTHORIZED"
        assert unauthorized.headers["WWW-Authenticate"] == "Bearer"

        ok = client.get(
            f"{BASE}/transactions", headers={"Authorization": "Bearer s3cret-token"}
        )
        assert ok.status_code == 200


# --------------------------------------------------------------- G1 LIKE 转义


def test_keyword_wildcards_are_literal(api_client):
    create(api_client, merchant="100%折扣店", amount=1000)
    create(api_client, merchant="普通商店", amount=2000)

    assert api_client.get(f"{BASE}/transactions", params={"q": "%"}).json()["total"] == 1
    assert api_client.get(f"{BASE}/transactions", params={"q": "_"}).json()["total"] == 0
    assert api_client.get(f"{BASE}/transactions", params={"q": "100%"}).json()["total"] == 1


# ------------------------------------------------- G2 事件不重复、可回落


def test_budget_events_are_idempotent(api_client):
    api_client.put(f"{BASE}/budget", json={"month": "2027-05", "amount": 10000})
    created = create_at(
        api_client, merchant="星巴克", amount=10000, occurred_at="2027-05-10T12:00:00+08:00"
    )

    api_client.delete(f"{BASE}/transactions/{created['id']}")
    total_after_delete = api_client.get(f"{BASE}/alerts").json()["total"]
    assert total_after_delete == 2

    # 再次越过阈值：同一行事件重新激活，不产生重复记录
    create_at(
        api_client, merchant="星巴克", amount=9000, occurred_at="2027-05-11T12:00:00+08:00"
    )
    assert api_client.get(f"{BASE}/alerts").json()["total"] == 2


# ------------------------------------------------------ G3 显式分类类型校验


def test_explicit_category_must_match_direction(api_client):
    categories = api_client.get(f"{BASE}/categories").json()
    salary = next(item for item in categories if item["name"] == "工资")

    response = create(api_client, merchant="星巴克", categoryId=int(salary["id"]))
    assert response.status_code == 422

    transfer = create(api_client, merchant="张三", direction="TRANSFER")
    assert transfer.status_code == 422


# --------------------------------------------------- G4 显式 source 优先


def test_explicit_source_overrides_detection(api_client):
    response = api_client.post(
        f"{BASE}/imports/csv",
        files={"file": ("alipay.csv", ALIPAY_CSV.read_bytes(), "text/csv")},
        data={"source": "WECHAT"},
    )
    assert response.status_code == 201
    assert response.json()["created"] == 5
    assert (
        api_client.get(f"{BASE}/transactions", params={"source": "WECHAT"}).json()["total"]
        == 5
    )


# ------------------------------------------------------------ G6 本地时间


def test_transaction_exposes_local_time(api_client):
    body = create(api_client, occurred_at="2026-11-02T12:00:00+08:00").json()
    moment = datetime.fromisoformat(body["occurredAt"])
    assert moment.utcoffset() == timedelta(hours=8)
    assert (moment.hour, moment.minute) == (12, 0)


# --------------------------------------------------- G7 统一 500 / request id


def test_unhandled_error_returns_json_with_request_id(client_factory):
    with client_factory(raise_server_exceptions=False) as client:
        def boom(*args, **kwargs):
            raise RuntimeError("boom")

        client.app.state.container.transactions.list = boom  # type: ignore[method-assign]
        response = client.get(f"{BASE}/transactions")

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["details"]["request_id"]
    assert response.headers["X-Request-ID"] == body["details"]["request_id"]
    assert "boom" not in body["message"]


def test_unknown_route_uses_unified_error_body(api_client):
    response = api_client.get(f"{BASE}/does-not-exist")
    assert response.status_code == 404
    assert response.json()["code"] == "NOT_FOUND"
    assert response.json()["details"]["request_id"]


# --------------------------------------------------------- G8 互斥参数


def test_mutually_exclusive_patch_arguments(api_client):
    created = create(api_client).json()
    response = api_client.patch(
        f"{BASE}/transactions/{created['id']}",
        json={"clearCategory": True, "recategorize": True},
    )
    assert response.status_code == 422
    assert "互斥" in str(response.json()["details"]["errors"][0]["msg"])


# --------------------------------------------------------- G9 收件箱排除转账


def test_inbox_excludes_transfers(api_client):
    content = (
        "交易时间,金额(元),交易单号,收/支,交易对方\n"
        "2026-11-20 10:00:00,100.00,TR-1,不计收支,张三\n"
    ).encode()
    api_client.post(f"{BASE}/imports/csv", files={"file": ("t.csv", content, "text/csv")})
    create(api_client, merchant="未知商户", amount=2000)

    inbox = api_client.get(f"{BASE}/transactions/inbox").json()
    assert inbox["total"] == 1
    assert inbox["items"][0]["merchant"] == "未知商户"


# --------------------------------------------------- O1/O8 上传限制与文案


def test_upload_limit_rejects_with_readable_size(client_factory):
    with client_factory(max_upload_bytes=1024) as client:
        response = client.post(
            f"{BASE}/imports/csv",
            files={"file": ("big.csv", b"a" * 2048, "text/csv")},
        )
    assert response.status_code == 422
    assert "1.0KB" in response.json()["message"]


# ------------------------------------------------------------ O2 时区告警


def test_invalid_timezone_logs_error(caplog):
    logger = logging.getLogger("test.timezone")
    with caplog.at_level(logging.ERROR, logger="test.timezone"):
        tz = resolve_timezone("Nowhere/Invalid", logger)
    assert str(tz) in ("UTC", "UTC+00:00")
    assert any("APP_TIMEZONE" in record.message for record in caplog.records)


# ---------------------------------------------------- O3 校验文案中文化


def test_validation_messages_are_chinese(api_client):
    response = api_client.post(
        f"{BASE}/transactions", json={"amount": 1000, "direction": "EXPENSE"}
    )
    assert response.status_code == 422
    errors = response.json()["details"]["errors"]
    assert any(error["msg"] == "缺少必填字段" for error in errors)


# --------------------------------------------------------- O5 批量重分类上限


def test_reclassify_batch_limit(api_client):
    response = api_client.post(
        f"{BASE}/transactions/reclassify", json={"transactionIds": list(range(501))}
    )
    assert response.status_code == 422


# ------------------------------------------------------------ O6 就绪检查


def test_ready_check_reports_schema_and_tables(api_client):
    body = api_client.get(f"{BASE}/health/ready").json()
    assert body["status"] == "ready"
    assert body["database"] == "ok"
    assert "schema_version" in body
    assert "transactions" in body
