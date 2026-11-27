from __future__ import annotations

from datetime import UTC, datetime

BASE = "/api/v1"


def parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def create(client, merchant="星巴克", amount=3250, occurred_at="2026-11-20T12:00:00+08:00", **extra):
    payload = {
        "merchant": merchant,
        "amount": amount,
        "direction": "EXPENSE",
        "occurredAt": occurred_at,
        **extra,
    }
    return client.post(f"{BASE}/transactions", json=payload)


def category_id(client, name: str) -> int:
    items = client.get(f"{BASE}/categories").json()
    return int(next(item["id"] for item in items if item["name"] == name))


def test_create_defaults(api_client):
    response = create(api_client)
    assert response.status_code == 201, response.text
    body = response.json()

    assert body["amount"] == 3250  # 整数分
    assert "amountCents" not in body
    assert body["source"] == "MANUAL"
    assert body["externalId"].startswith("MAN-")
    assert body["categoryId"] is not None
    assert body["categorySource"] == "BUILTIN"
    assert parse_dt(body["occurredAt"]) == datetime(2026, 11, 20, 4, 0, tzinfo=UTC)
    assert body["occurredAt"].endswith("+08:00")


def test_unmatched_merchant_goes_to_inbox(api_client):
    response = create(api_client, merchant="某个完全不认识的商户", amount=990)
    assert response.status_code == 201
    assert response.json()["categoryId"] is None
    assert response.json()["categorySource"] is None

    inbox = api_client.get(f"{BASE}/transactions/inbox").json()
    assert inbox["total"] == 1
    assert inbox["page"] == 1
    assert inbox["pageSize"] == 20
    assert inbox["items"][0]["merchant"] == "某个完全不认识的商户"


def test_invalid_amount_is_rejected(api_client):
    assert create(api_client, amount=0).status_code == 422
    assert create(api_client, amount=-1).status_code == 422
    assert create(api_client, merchant="").status_code == 422


def test_list_filters_and_pagination(api_client):
    create(api_client, merchant="星巴克", amount=3250, occurred_at="2026-11-20T12:00:00+08:00")
    create(api_client, merchant="京东", amount=4900, occurred_at="2026-11-21T12:00:00+08:00")
    create(
        api_client,
        merchant="公司",
        amount=800000,
        occurred_at="2026-11-21T12:00:00+08:00",
        direction="INCOME",
    )

    everyone = api_client.get(f"{BASE}/transactions", params={"month": "2026-11"}).json()
    assert everyone["total"] == 3
    assert everyone["page"] == 1
    assert everyone["pageSize"] == 20

    by_keyword = api_client.get(f"{BASE}/transactions", params={"q": "星巴克"}).json()
    assert by_keyword["total"] == 1

    income = api_client.get(f"{BASE}/transactions", params={"direction": "INCOME"}).json()
    assert income["total"] == 1
    assert income["items"][0]["direction"] == "INCOME"

    paged = api_client.get(
        f"{BASE}/transactions", params={"page": 2, "pageSize": 2}
    ).json()
    assert paged["total"] == 3
    assert len(paged["items"]) == 1
    assert paged["pageSize"] == 2

    source = api_client.get(f"{BASE}/transactions", params={"source": "MANUAL"}).json()
    assert source["total"] == 3


def test_list_sort(api_client):
    create(api_client, merchant="A", amount=100, occurred_at="2026-11-20T12:00:00+08:00")
    create(api_client, merchant="B", amount=200, occurred_at="2026-11-21T12:00:00+08:00")

    asc = api_client.get(
        f"{BASE}/transactions", params={"sort": "amount"}
    ).json()["items"]
    assert [item["amount"] for item in asc] == [100, 200]

    desc = api_client.get(
        f"{BASE}/transactions", params={"sort": "-amount"}
    ).json()["items"]
    assert [item["amount"] for item in desc] == [200, 100]

    assert api_client.get(
        f"{BASE}/transactions", params={"sort": "unknown"}
    ).status_code == 422


def test_explicit_category_marks_source_user(api_client):
    cid = category_id(api_client, "餐饮")
    body = create(api_client, categoryId=cid).json()
    assert body["categoryId"] == str(cid)
    assert body["categorySource"] == "USER"


def test_patch_clear_and_recategorize(api_client):
    created = create(api_client).json()
    txn_id = created["id"]

    cleared = api_client.patch(
        f"{BASE}/transactions/{txn_id}", json={"amount": 4000, "categoryId": None}
    )
    assert cleared.status_code == 200
    assert cleared.json()["amount"] == 4000
    assert cleared.json()["categoryId"] is None
    assert cleared.json()["categorySource"] is None

    again = api_client.patch(f"{BASE}/transactions/{txn_id}", json={"recategorize": True})
    assert again.status_code == 200
    assert again.json()["categoryId"] == created["categoryId"]
    assert again.json()["categorySource"] == "BUILTIN"


def test_patch_rejects_unknown_category(api_client):
    created = create(api_client).json()
    response = api_client.patch(
        f"{BASE}/transactions/{created['id']}", json={"categoryId": 999999}
    )
    assert response.status_code == 404


def test_detail_not_found(api_client):
    assert api_client.get(f"{BASE}/transactions/123456").status_code == 404


def test_screenshot_candidates(api_client):
    response = api_client.post(
        f"{BASE}/imports/screenshot-candidates",
        json={
            "rows": [
                {
                    "clientId": "c1",
                    "merchant": "全家便利店",
                    "amount": 1200,
                    "occurredAt": "2026-11-22T20:00:00+08:00",
                },
                {
                    "clientId": "c2",
                    "merchant": "未知商户",
                    "amount": 500,
                    "occurredAt": "2026-11-22T21:00:00+08:00",
                },
            ],
            "skippedClientIds": ["c3"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["created"] == 2
    assert body["skipped"] == 1
    assert body["failed"] == 0

    listed = api_client.get(f"{BASE}/transactions").json()
    assert listed["total"] == 2
    assert {item["source"] for item in listed["items"]} == {"SCREENSHOT"}
    assert all(item["externalId"].startswith("SCR-") for item in listed["items"])


def test_batch_classify(api_client):
    first = create(api_client, merchant="未知商户A", amount=1000).json()
    second = create(api_client, merchant="未知商户B", amount=2000).json()
    cid = category_id(api_client, "餐饮")

    response = api_client.post(
        f"{BASE}/transactions/batch-classify",
        json={
            "ids": [int(first["id"]), int(second["id"]), 999999],
            "categoryId": cid,
            "createRule": {"keyword": "未知商户"},
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["updated"] == 2
    assert body["ruleCreated"] is True
    assert body["failed"][0]["id"] == "999999"

    rules = api_client.get(f"{BASE}/category-rules").json()
    assert any(rule["keyword"] == "未知商户" for rule in rules)


def test_weak_fingerprint_duplicate_check(api_client):
    created = create(api_client).json()

    response = api_client.post(
        f"{BASE}/transactions/duplicates/check",
        json={
            "items": [
                {
                    "merchant": "星巴克(国贸店)",
                    "amount": 3250,
                    "occurredAt": "2026-11-20T18:00:00+08:00",
                }
            ]
        },
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) == 1
    assert items[0]["transactionId"] == created["id"]


def test_reclassify_inbox(api_client):
    create(api_client, merchant="瑞幸咖啡", amount=1500)
    response = api_client.post(f"{BASE}/transactions/reclassify", json={})
    assert response.status_code == 200
    assert response.json()["scanned"] == 0  # 已被内置词库自动分类
