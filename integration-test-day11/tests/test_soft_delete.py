"""第 11 天检查（一）：财务记录只做软删除，禁止物理删除。"""
BASE = "/api/v1"


def _create(client) -> dict:
    r = client.post(BASE + "/transactions", json={
        "merchant": "星巴克", "amount": 3250, "direction": "EXPENSE",
        "occurredAt": "2026-11-20T12:00:00+08:00",
    })
    assert r.status_code == 201
    return r.json()


def test_delete_writes_deleted_at_and_keeps_record(client):
    tx = _create(client)
    assert client.delete(f"{BASE}/transactions/{tx['id']}").status_code == 204
    # 默认接口不可见
    assert client.get(BASE + "/transactions").json()["total"] == 0
    assert client.get(f"{BASE}/transactions/{tx['id']}").status_code == 404
    # includeDeleted 仍可查到，且 deletedAt 有值、金额未丢
    hidden = client.get(f"{BASE}/transactions/{tx['id']}",
                        params={"includeDeleted": True})
    assert hidden.status_code == 200
    assert hidden.json()["deletedAt"] is not None
    assert hidden.json()["amount"] == 3250


def test_hard_delete_forbidden(client):
    tx = _create(client)
    r = client.delete(f"{BASE}/transactions/{tx['id']}", params={"hard": True})
    assert r.status_code == 405
    assert r.json()["code"] == "HARD_DELETE_FORBIDDEN"


def test_double_delete_404_and_restore(client):
    tx = _create(client)
    assert client.delete(f"{BASE}/transactions/{tx['id']}").status_code == 204
    assert client.delete(f"{BASE}/transactions/{tx['id']}").status_code == 404
    restored = client.post(f"{BASE}/transactions/{tx['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["deletedAt"] is None


def test_soft_deleted_excluded_from_statistics(client):
    tx = _create(client)
    assert client.get(BASE + "/stats/summary",
                      params={"month": "2026-11"}).json()["totalExpense"] == 3250
    client.delete(f"{BASE}/transactions/{tx['id']}")
    assert client.get(BASE + "/stats/summary",
                      params={"month": "2026-11"}).json()["totalExpense"] == 0
