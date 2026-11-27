from __future__ import annotations

BASE = "/api/v1"


def create_txn(client, category_id: int | None = None) -> dict:
    payload = {
        "merchant": "未知商户",
        "amount": 1200,
        "direction": "EXPENSE",
        "occurredAt": "2026-11-21T12:00:00+08:00",
    }
    if category_id is not None:
        payload["categoryId"] = category_id
    response = client.post(f"{BASE}/transactions", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ------------------------------------------------------------- 分类 CRUD


def test_category_crud(api_client):
    created = api_client.post(
        f"{BASE}/categories",
        json={"name": "咖啡", "type": "EXPENSE", "color": "#FF8BA7"},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["source"] == "USER"
    assert body["isActive"] is True
    assert body["ruleCount"] == 0
    category_id = int(body["id"])

    duplicate = api_client.post(
        f"{BASE}/categories", json={"name": "咖啡", "type": "EXPENSE"}
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUPLICATE_RESOURCE"

    patched = api_client.patch(
        f"{BASE}/categories/{category_id}",
        json={"name": "咖啡因", "color": None, "isActive": False},
    )
    assert patched.status_code == 200
    assert patched.json()["name"] == "咖啡因"
    assert patched.json()["color"] is None
    assert patched.json()["isActive"] is False

    deleted = api_client.delete(f"{BASE}/categories/{category_id}")
    assert deleted.status_code == 204
    names = [item["name"] for item in api_client.get(f"{BASE}/categories").json()]
    assert "咖啡因" not in names


def test_category_delete_conflicts_when_referenced(api_client):
    category = api_client.post(
        f"{BASE}/categories", json={"name": "宠物", "type": "EXPENSE"}
    ).json()
    create_txn(api_client, int(category["id"]))

    response = api_client.delete(f"{BASE}/categories/{category['id']}")
    assert response.status_code == 409
    assert response.json()["code"] == "CONFLICT"


def test_category_type_filter(api_client):
    expenses = api_client.get(f"{BASE}/categories", params={"type": "EXPENSE"}).json()
    incomes = api_client.get(f"{BASE}/categories", params={"type": "INCOME"}).json()
    assert expenses and incomes
    assert {item["type"] for item in expenses} == {"EXPENSE"}
    assert {item["type"] for item in incomes} == {"INCOME"}


# ------------------------------------------------------------- 分类建议


def test_category_suggest(api_client):
    hit = api_client.get(f"{BASE}/categories/suggest", params={"name": "星巴克国贸店"}).json()
    assert hit["categoryId"] is not None
    assert hit["matchedBy"] == "BUILTIN"
    assert hit["ruleKeyword"] == "星巴克"

    miss = api_client.get(f"{BASE}/categories/suggest", params={"name": "完全未知商户"}).json()
    assert miss == {
        "categoryId": None,
        "matchedBy": None,
        "keyword": None,
        "ruleKeyword": None,
    }


# ------------------------------------------------------------- 规则 CRUD


def test_rule_crud_and_dry_run(api_client):
    category = api_client.post(
        f"{BASE}/categories", json={"name": "咖啡", "type": "EXPENSE"}
    ).json()

    created = api_client.post(
        f"{BASE}/category-rules",
        json={"keyword": "咖啡因店", "categoryId": int(category["id"])},
    )
    assert created.status_code == 201
    rule = created.json()
    assert rule["isBuiltin"] is False

    duplicate = api_client.post(
        f"{BASE}/category-rules",
        json={"keyword": "咖啡因店", "categoryId": int(category["id"])},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "DUPLICATE_RESOURCE"

    dry = api_client.post(f"{BASE}/category-rules/test", json={"name": "咖啡因店消费"}).json()
    assert dry["matched"] is True
    assert dry["ruleSource"] == "RULE"
    assert dry["ruleKeyword"] == "咖啡因店"
    assert dry["categoryId"] == category["id"]

    missing = api_client.post(f"{BASE}/category-rules/test", json={"name": "毫无关系"}).json()
    assert missing["matched"] is False

    assert api_client.delete(f"{BASE}/category-rules/{rule['id']}").status_code == 204


def test_builtin_rule_is_read_only(api_client):
    rules = api_client.get(f"{BASE}/category-rules").json()
    builtin = next(item for item in rules if item["isBuiltin"])
    response = api_client.delete(f"{BASE}/category-rules/{builtin['id']}")
    assert response.status_code == 409


# --------------------------------------------------------------- 设置


def test_settings_defaults_and_update(api_client):
    initial = api_client.get(f"{BASE}/settings").json()
    assert initial == {
        "hourlyRate": None,
        "persona": "RATIONAL",
        "modules": {"wardrobe": True, "intents": True, "feedback": True},
    }

    patched = api_client.patch(
        f"{BASE}/settings",
        json={"hourlyRate": 5000, "persona": "GENTLE", "modules": {"wardrobe": False}},
    )
    assert patched.status_code == 200
    body = patched.json()
    assert body["hourlyRate"] == 5000
    assert body["persona"] == "GENTLE"
    assert body["modules"] == {"wardrobe": False, "intents": True, "feedback": True}

    cleared = api_client.patch(f"{BASE}/settings", json={"hourlyRate": None}).json()
    assert cleared["hourlyRate"] is None
    assert cleared["persona"] == "GENTLE"


def test_settings_reject_invalid_persona(api_client):
    response = api_client.patch(f"{BASE}/settings", json={"persona": "UNKNOWN"})
    assert response.status_code == 422
