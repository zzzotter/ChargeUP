from __future__ import annotations

BASE = "/api/v1"


def create(client) -> dict:
    response = client.post(
        f"{BASE}/transactions",
        json={
            "merchant": "星巴克",
            "amount": 3250,
            "direction": "EXPENSE",
            "occurredAt": "2026-11-20T12:00:00+08:00",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_delete_is_soft(api_client):
    created = create(api_client)

    deleted = api_client.delete(f"{BASE}/transactions/{created['id']}")
    assert deleted.status_code == 204

    assert api_client.get(f"{BASE}/transactions").json()["total"] == 0
    assert api_client.get(f"{BASE}/transactions/{created['id']}").status_code == 404

    detail = api_client.get(
        f"{BASE}/transactions/{created['id']}", params={"includeDeleted": True}
    )
    assert detail.status_code == 200
    assert detail.json()["amount"] == 3250
    assert detail.json()["deletedAt"] is not None


def test_hard_delete_is_forbidden(api_client):
    created = create(api_client)
    response = api_client.delete(f"{BASE}/transactions/{created['id']}", params={"hard": True})
    assert response.status_code == 405
    assert response.json()["code"] == "HARD_DELETE_FORBIDDEN"


def test_delete_twice_returns_404(api_client):
    created = create(api_client)
    assert api_client.delete(f"{BASE}/transactions/{created['id']}").status_code == 204
    assert api_client.delete(f"{BASE}/transactions/{created['id']}").status_code == 404


def test_restore(api_client):
    created = create(api_client)
    api_client.delete(f"{BASE}/transactions/{created['id']}")

    restored = api_client.post(f"{BASE}/transactions/{created['id']}/restore")
    assert restored.status_code == 200
    assert restored.json()["deletedAt"] is None
    assert api_client.get(f"{BASE}/transactions").json()["total"] == 1


def test_soft_deleted_excluded_from_statistics(api_client):
    created = create(api_client)
    before = api_client.get(f"{BASE}/stats/summary", params={"month": "2026-11"}).json()
    assert before["totalExpense"] == 3250

    api_client.delete(f"{BASE}/transactions/{created['id']}")
    after = api_client.get(f"{BASE}/stats/summary", params={"month": "2026-11"}).json()
    assert after["totalExpense"] == 0
