"""第二轮测评报告（并发/一致性/可观测性）回归用例。"""

from __future__ import annotations

from pathlib import Path

from app.domain.money import format_cents, parse_amount_to_cents

BASE = "/api/v1"
COMPOSE = Path(__file__).resolve().parents[1] / "docker-compose.yml"


def create(client, merchant: str = "星巴克", amount: int = 3250, **extra):
    return client.post(
        f"{BASE}/transactions",
        json={
            "merchant": merchant,
            "amount": amount,
            "direction": "EXPENSE",
            "occurredAt": "2026-11-10T12:00:00+08:00",
            **extra,
        },
    )


# ------------------------------------------------------- B2 并发预算写入


def test_budget_upsert_survives_insert_race(api_client, monkeypatch):
    from app.infrastructure.repositories import SqlAlchemyBudgetRepository

    assert (
        api_client.put(f"{BASE}/budget", json={"month": "2026-12", "amount": 10000}).status_code
        == 200
    )

    original = SqlAlchemyBudgetRepository._find
    calls = {"count": 0}

    def stale_once(self, period):
        calls["count"] += 1
        if calls["count"] == 1:  # 第一次读不到，模拟并发窗口
            return None
        return original(self, period)

    monkeypatch.setattr(SqlAlchemyBudgetRepository, "_find", stale_once)

    response = api_client.put(f"{BASE}/budget", json={"month": "2026-12", "amount": 20000})
    assert response.status_code == 200
    assert response.json()["amount"] == 20000
    assert (
        api_client.get(f"{BASE}/budget", params={"month": "2026-12"}).json()["amount"] == 20000
    )


# ------------------------------------- W1 改方向后分类与统计保持一致


def test_direction_change_drops_incompatible_category(api_client):
    created = create(api_client, amount=7777).json()
    assert created["categoryId"] is not None

    patched = api_client.patch(
        f"{BASE}/transactions/{created['id']}", json={"direction": "INCOME"}
    )
    assert patched.status_code == 200
    assert patched.json()["direction"] == "INCOME"
    assert patched.json()["categoryId"] is None
    assert patched.json()["categorySource"] is None

    summary = api_client.get(f"{BASE}/stats/summary", params={"month": "2026-11"}).json()
    assert summary["totalIncome"] == 7777
    assert summary["totalExpense"] == 0


# ------------------------------------------------ W2 文档与健康信息保护


def test_docs_disabled_by_default_when_token_configured(client_factory):
    with client_factory(api_token="docs-token") as client:
        assert client.get("/docs").status_code == 404
        assert client.get("/redoc").status_code == 404
        assert client.get("/openapi.json").status_code == 404
        assert "auth" not in client.get(f"{BASE}/health").json()


def test_docs_require_token_when_explicitly_enabled(client_factory):
    with client_factory(api_token="docs-token", docs_enabled=True) as client:
        assert client.get("/docs").status_code == 401
        document = client.get("/docs", headers={"Authorization": "Bearer docs-token"})
        assert document.status_code == 200
        spec = client.get("/openapi.json", headers={"Authorization": "Bearer docs-token"}).json()
        assert spec["openapi"].startswith("3.")


# ------------------------------------------------------ W3 校验文案中文


def test_length_validation_messages_are_chinese(api_client):
    response = create(api_client, merchant="长" * 300)
    assert response.status_code == 422
    message = response.json()["details"]["errors"][0]["msg"]
    assert "长度" in message
    assert "Value" not in message and "String" not in message


# --------------------------------------------------- G2 keyword 长度上限


def test_keyword_length_is_capped(api_client):
    response = api_client.get(f"{BASE}/transactions", params={"q": "长" * 300})
    assert response.status_code == 422


# ------------------------------------------- G3 健康检查暴露实际时区


def test_health_reports_effective_timezone_on_invalid_config(client_factory):
    with client_factory(timezone="Invalid/Zone") as client:
        body = client.get(f"{BASE}/health").json()
    assert body["timezone"] == "Invalid/Zone"
    assert body["timezone_effective"] == "UTC"
    assert body["timezone_fallback"] is True


# ------------------------------------------------ G5 compose 凭据与网卡


def test_compose_uses_env_credentials_and_loopback_only():
    text = COMPOSE.read_text(encoding="utf-8")
    assert "127.0.0.1:5432:5432" in text
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD" in text
    assert "ledger/ledger" not in text
    assert '"5432:5432"' not in text


# ------------------------------------------- S1 查重置信度（空商户）


def test_duplicate_confidence_marks_missing_merchant(api_client):
    created = create(api_client).json()

    low = api_client.post(
        f"{BASE}/transactions/duplicates/check",
        json={"items": [{"merchant": "", "amount": 3250, "occurredAt": "2026-11-10T18:00:00+08:00"}]},
    ).json()["items"]
    assert low[0]["transactionId"] == created["id"]
    assert low[0]["confidence"] == "LOW"

    high = api_client.post(
        f"{BASE}/transactions/duplicates/check",
        json={
            "items": [
                {"merchant": "星巴克", "amount": 3250, "occurredAt": "2026-11-10T18:00:00+08:00"}
            ]
        },
    ).json()["items"]
    assert high[0]["confidence"] == "HIGH"


# ---------------------------------------- S2 重分类截断可感知


def test_reclassify_separates_invalid_ids_from_limit_truncation(api_client):
    created = create(api_client, merchant="未知商户A", amount=1000).json()
    response = api_client.post(
        f"{BASE}/transactions/reclassify",
        json={"transactionIds": [int(created["id"]), 999999]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["scanned"] == 1
    assert body["invalidIds"] == ["999999"]
    assert body["remaining"] == 0
    assert body["truncated"] is False


# ---------------------------------------- S3 categoryId: null 显式清空


def test_patch_with_null_category_clears_it(api_client):
    created = create(api_client).json()
    assert created["categoryId"] is not None

    cleared = api_client.patch(
        f"{BASE}/transactions/{created['id']}", json={"categoryId": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["categoryId"] is None

    conflict = api_client.patch(
        f"{BASE}/transactions/{created['id']}",
        json={"categoryId": None, "recategorize": True},
    )
    assert conflict.status_code == 422


# ------------------------------------------------ 金额工具仍保持整数分


def test_amount_helpers_are_integer_based():
    assert parse_amount_to_cents("¥1,234.56") == 123456
    assert format_cents(123456) == "1234.56"
