from __future__ import annotations

from tests.support import ALIPAY_CSV, BROKEN_CSV, WECHAT_CSV

BASE = "/api/v1"


def upload(client, filename: str, content: bytes, **extra):
    return client.post(
        f"{BASE}/imports/csv",
        files={"file": (filename, content, "text/csv")},
        data=extra or None,
    )


def test_import_is_idempotent(api_client):
    content = ALIPAY_CSV.read_bytes()

    first = upload(api_client, "alipay.csv", content)
    assert first.status_code == 201
    body = first.json()
    assert body["recognized"] == 5
    assert body["created"] == 5
    assert body["duplicated"] == 0
    assert body["failed"] == 0
    assert body["importId"].isdigit()
    assert body["durationMs"] >= 0

    second = upload(api_client, "alipay.csv", content)
    assert second.status_code == 201
    assert second.json()["created"] == 0
    assert second.json()["duplicated"] == 5
    assert second.json()["recognized"] == 5

    listed = api_client.get(f"{BASE}/transactions").json()
    assert listed["total"] == 5  # 重复导入不产生重复流水


def test_import_history_and_report(api_client):
    first = upload(api_client, "alipay.csv", ALIPAY_CSV.read_bytes()).json()

    history = api_client.get(f"{BASE}/imports").json()
    assert history["total"] == 1
    assert history["items"][0]["id"] == first["importId"]
    assert history["items"][0]["created"] == 5

    report = api_client.get(f"{BASE}/imports/{first['importId']}/report").json()
    assert report["importId"] == first["importId"]
    assert report["created"] == 5


def test_import_wechat_gbk(api_client):
    content = WECHAT_CSV.read_text(encoding="utf-8").encode("gb18030")
    response = upload(api_client, "wechat.csv", content)
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 4

    transfers = api_client.get(
        f"{BASE}/transactions", params={"direction": "TRANSFER"}
    ).json()
    assert transfers["total"] == 1


def test_bad_rows_are_reported_not_fatal(api_client):
    response = upload(api_client, "broken.csv", BROKEN_CSV.read_bytes())
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 1
    assert body["failed"] == 4
    assert len(body["failures"]) == 4
    assert all("42000000000000000002" not in (item.get("raw") or "") for item in body["failures"])


def test_missing_header_is_reported(api_client):
    response = upload(api_client, "unknown.csv", b"foo,bar\n1,2\n")
    assert response.status_code == 201
    body = response.json()
    assert body["created"] == 0
    assert "表头" in body["failures"][0]["reason"]


def test_rejects_non_csv_filename(api_client):
    response = upload(api_client, "bill.xlsx", b"whatever")
    assert response.status_code == 422


def test_rejects_manual_source(api_client):
    response = upload(api_client, "alipay.csv", ALIPAY_CSV.read_bytes(), source="MANUAL")
    assert response.status_code == 422
