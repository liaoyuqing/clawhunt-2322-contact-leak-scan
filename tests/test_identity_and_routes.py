"""身份矩阵与接口行为：会员能看的员工不能看，反之亦然；不存在的身份一律 400。"""
from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "method,path",
    [
        ("GET", "/api/mini/me/profile"),
        ("POST", "/api/mini/privacy/deletion"),
    ],
)
def test_member_only_endpoints_reject_staff(client, method, path):
    json_body = {} if method == "POST" else None
    response = client.request(method, path, headers={"X-Mini-Identity": "staff"}, json=json_body)
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "identity_not_allowed"


@pytest.mark.parametrize(
    "path",
    ["/api/mini/staff/profile", "/api/mini/staff/cases", "/api/mini/staff/shifts"],
)
def test_staff_only_endpoints_reject_member(client, path):
    response = client.get(path, headers={"X-Mini-Identity": "member"})
    assert response.status_code == 403


@pytest.mark.parametrize("identity", ["member", "staff"])
def test_shared_endpoints_accept_both_identities(client, identity):
    response = client.get("/api/mini/events", headers={"X-Mini-Identity": identity})
    assert response.status_code == 200
    assert response.json()["data"]["total"] >= 1


def test_missing_identity_header_defaults_to_member(client):
    response = client.get("/api/mini/faq")
    assert response.status_code == 200


def test_unknown_identity_is_400(client):
    response = client.get("/api/mini/faq", headers={"X-Mini-Identity": "visitor"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unknown_identity"


def test_ticket_list_returns_number_for_whitelist_path(client):
    response = client.get("/api/mini/tickets", headers={"X-Mini-Identity": "member"})
    ticket_no = response.json()["data"]["items"][0]["ticket_no"]
    assert len(ticket_no) == 16 and ticket_no.isdigit()


def test_post_body_contains_redacted_text_not_phone(client):
    response = client.get("/api/mini/posts", headers={"X-Mini-Identity": "member"})
    body = response.json()["data"]["items"][0]["body"]
    assert "13800001111" not in body
    assert "【联系方式已隐藏】" in body
