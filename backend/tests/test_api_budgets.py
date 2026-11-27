from __future__ import annotations

BASE = "/api/v1"


def create(client, amount: int, merchant: str = "星巴克", day: str = "2026-11-10"):
    response = client.post(
        f"{BASE}/transactions",
        json={
            "merchant": merchant,
            "amount": amount,
            "direction": "EXPENSE",
            "occurredAt": f"{day}T12:00:00+08:00",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def set_budget(client, amount: int = 100000, month: str = "2026-11", **extra):
    payload = {"month": month, "amount": amount}
    if "warn_threshold" in extra:
        payload["warnThreshold"] = extra.pop("warn_threshold")
    if "alert_threshold" in extra:
        payload["alertThreshold"] = extra.pop("alert_threshold")
    payload.update(extra)
    return client.put(f"{BASE}/budget", json=payload)


def test_budget_roundtrip_and_thresholds(api_client):
    created = set_budget(api_client)
    assert created.status_code == 200
    body = created.json()
    assert body == {
        "month": "2026-11",
        "amount": 100000,
        "warnThreshold": 0.8,
        "alertThreshold": 1.0,
    }

    fetched = api_client.get(f"{BASE}/budget", params={"month": "2026-11"}).json()
    assert fetched == body


def test_thresholds_trigger_once_each(api_client):
    set_budget(api_client)

    create(api_client, 30000)
    assert api_client.get(f"{BASE}/alerts").json()["total"] == 0

    create(api_client, 50000)
    alerts = api_client.get(f"{BASE}/alerts").json()
    assert alerts["total"] == 1
    assert alerts["items"][0]["level"] == "WARN"
    assert alerts["items"][0]["threshold"] == 0.8
    assert alerts["items"][0]["read"] is False

    create(api_client, 20000)
    alerts = api_client.get(f"{BASE}/alerts").json()
    assert alerts["total"] == 2
    assert [item["level"] for item in alerts["items"]] == ["ALERT", "WARN"]
    assert alerts["items"][0]["threshold"] == 1.0

    # 继续消费不重复触发
    create(api_client, 10000)
    assert api_client.get(f"{BASE}/alerts").json()["total"] == 2


def test_alerts_filter_and_mark_read(api_client):
    set_budget(api_client)
    create(api_client, 90000)
    alerts = api_client.get(f"{BASE}/alerts", params={"level": "WARN"}).json()
    assert alerts["total"] == 1
    alert_id = alerts["items"][0]["id"]

    unread = api_client.get(f"{BASE}/alerts", params={"read": "false"}).json()
    assert unread["total"] == 1

    patched = api_client.patch(f"{BASE}/alerts/{alert_id}", json={"read": True})
    assert patched.status_code == 200
    assert patched.json()["read"] is True

    read = api_client.get(f"{BASE}/alerts", params={"read": "true"}).json()
    assert read["total"] == 1


def test_setting_budget_after_spending_backfills_events(api_client):
    create(api_client, 90000)
    set_budget(api_client, 100000)
    alerts = api_client.get(f"{BASE}/alerts").json()
    assert [item["level"] for item in alerts["items"]] == ["WARN"]


def test_missing_budget_returns_404(api_client):
    assert api_client.get(f"{BASE}/budget", params={"month": "2025-01"}).status_code == 404


def test_invalid_thresholds_are_rejected(api_client):
    response = set_budget(api_client, warn_threshold=1.0, alert_threshold=0.8)
    assert response.status_code == 422

    response = set_budget(api_client, month="2026-13")
    assert response.status_code == 422
