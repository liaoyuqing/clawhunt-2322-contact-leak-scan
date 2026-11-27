"""AC2：人为让接口返回虚构手机号时，测试必须失败，并输出接口路径 + 字段路径。

用 app.injection 在运行时覆盖 /api/mini/support/tickets 的响应体（不改路由源码），
然后跑真实扫描，断言：
1. 扫描判定为泄露；
2. 报错文本里有 path=/api/mini/support/tickets；
3. 报错文本里有 field=data.items[0].contact_phone；
4. 掩码 138****1111 同样判失败；
5. 邮箱 / wxid / 座机三类各命中一条；
6. 未注入时同一接口是干净的（对照，证明失败来自注入而不是基线）。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app import injection
from scan.leak_check import scan_payload

TARGET_ROUTE = "/api/mini/support/tickets"
TARGET_URL = "/api/mini/support/tickets"


def _leaky_body(value: str, field: str = "contact_phone"):
    return {
        "data": {
            "items": [{"ticket_id": "st-1001", "subject": "改签申请（虚构）", field: value}],
            "total": 1,
        }
    }


def _scan(client) -> tuple:
    response = client.get(TARGET_URL, headers={"X-Mini-Identity": "member"})
    assert response.status_code == 200
    payload = response.json()
    return payload, scan_payload(payload, route=TARGET_ROUTE)


def test_baseline_is_clean(client):
    payload, result = _scan(client)
    assert result.ok, f"未注入时不应有命中：{[str(hit) for hit in result.hits]}"
    assert "contact_phone" not in str(payload)


def test_injected_phone_fails_the_scan(client):
    injection.register(TARGET_ROUTE, _leaky_body("13800138000"))
    _, result = _scan(client)
    assert not result.ok
    assert result.hits[0].kind.startswith("key_")
    assert result.hits[0].field_path == "data.items[0].contact_phone"


def test_failure_message_contains_route_and_field_path(client):
    injection.register(TARGET_ROUTE, _leaky_body("13800138000"))
    _, result = _scan(client)
    with pytest.raises(AssertionError) as excinfo:
        result.raise_for_leak()
    message = str(excinfo.value)
    assert "LEAK_DETECTED route=" + TARGET_ROUTE in message
    assert "path=" + TARGET_ROUTE in message
    assert "field=data.items[0].contact_phone" in message


def test_field_path_points_at_the_json_leaf(client):
    injection.register(TARGET_ROUTE, _leaky_body("13800138000"))
    _, result = _scan(client)
    assert "data.items[0].contact_phone" in [hit.field_path for hit in result.hits]


@pytest.mark.parametrize(
    "value,kind",
    [
        ("13800138000", "value_phone"),
        ("138****8000", "value_masked_phone"),
        ("****8000", "value_masked_tail"),
        ("member.one@example.com", "value_email"),
        ("wxid_probe0001", "value_wxid"),
        ("021-12345678", "value_landline"),
    ],
)
def test_each_leak_kind_is_caught(client, value, kind):
    body = {"data": {"items": [{"ticket_id": "st-1001", "note": value}]}}
    injection.register(TARGET_ROUTE, body)
    _, result = _scan(client)
    assert any(hit.kind == kind for hit in result.hits), f"{value} 应命中 {kind}"


def test_injection_does_not_leak_into_other_routes(client):
    injection.register(TARGET_ROUTE, _leaky_body("13800138000"))
    other = client.get("/api/mini/events", headers={"X-Mini-Identity": "member"})
    assert scan_payload(other.json(), route="/api/mini/events").ok


def test_override_is_cleared_between_tests(client):
    payload, result = _scan(client)
    assert result.ok
    assert injection.active() == {}
