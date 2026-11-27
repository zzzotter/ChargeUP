from __future__ import annotations

from tests.support import ALIPAY_CSV

BASE = "/api/v1"


def import_alipay(client):
    response = client.post(
        f"{BASE}/imports/csv",
        files={"file": ("alipay.csv", ALIPAY_CSV.read_bytes(), "text/csv")},
    )
    assert response.status_code == 201
    return response.json()


def test_summary_excludes_transfer_and_refund(api_client):
    import_alipay(api_client)

    summary = api_client.get(f"{BASE}/stats/summary", params={"month": "2026-11"}).json()

    # 支出：32.50 + 199.00 + 25.60 = 257.10；退款 32.50 与原支出同时剔除 -> 224.60
    assert summary["month"] == "2026-11"
    assert summary["totalExpense"] == 22460
    assert summary["totalIncome"] == 0
    assert summary["excludedRefundCount"] == 2
    assert summary["excludedTransferCount"] == 1
    assert summary["uncategorizedCount"] == 1


def test_category_stats(api_client):
    import_alipay(api_client)
    items = api_client.get(f"{BASE}/stats/categories", params={"month": "2026-11"}).json()

    assert [item["name"] for item in items] == ["购物", "交通"]
    assert items[0]["amount"] == 19900
    assert items[0]["categoryId"] is not None
    assert abs(sum(item["ratio"] for item in items) - 1.0) < 0.001


def test_monthly_trend_contains_fixture_month(api_client):
    import_alipay(api_client)
    points = api_client.get(f"{BASE}/stats/monthly", params={"months": 12}).json()
    assert len(points) == 12
    match = next(point for point in points if point["month"] == "2026-11")
    assert match["expense"] == 22460


def test_empty_period_summary(api_client):
    summary = api_client.get(f"{BASE}/stats/summary", params={"month": "2026-02"}).json()
    assert summary["totalExpense"] == 0
    assert api_client.get(f"{BASE}/stats/categories", params={"month": "2026-02"}).json() == []


def test_invalid_period_is_rejected(api_client):
    assert (
        api_client.get(f"{BASE}/stats/summary", params={"month": "2026-13"}).status_code
        == 422
    )
