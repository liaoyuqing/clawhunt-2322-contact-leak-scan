"""AC 主表：枚举 11 个前缀下的全部接口，每个接口 × 每种身份跑一遍泄露扫描。

用例数 = 接口数 × 2（member / staff），由 parametrize 从路由表现算，不手写清单。
任何一个接口漏登记，test_registry_guard.py 会单独失败；这里只管「扫到的内容不能有联系方式」。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.identity import IDENTITIES
from scan import enumerate as route_enum
from scan.leak_check import scan_payload
from scan.registry import REGISTRY
from scan.report import BODIES, concrete_path


def _matrix(app):
    routes = route_enum.enumerate_routes(app)
    cases = []
    for template in sorted(routes):
        for method in sorted(routes[template]):
            for identity in IDENTITIES:
                cases.append((method, template, identity))
    return cases


def test_matrix_is_not_empty(app):
    cases = _matrix(app)
    assert len(cases) >= 44, "接口 × 身份 的用例矩阵少于 44 条，说明枚举漏了前缀"


def test_every_template_is_registered(app):
    found = set(route_enum.enumerate_templates(app))
    missing = sorted(found - set(REGISTRY))
    assert missing == [], "UNDECLARED_ENDPOINT: " + ", ".join(missing)


@pytest.mark.parametrize("method,template,identity", _matrix(__import__("app.main", fromlist=["create_app"]).create_app()))
def test_endpoint_has_no_contact_leak(app, method, template, identity):
    client = TestClient(app)
    response = client.request(
        method,
        concrete_path(template),
        headers={"X-Mini-Identity": identity},
        json=BODIES.get((method, template)),
    )
    if response.status_code in (401, 403):
        # 身份不允许访问：这一行在报告里记为 NOT_ALLOWED，不参与泄露判定
        assert response.status_code == 403
        return
    assert response.status_code < 400, f"{method} {template} 以 {identity} 身份返回 {response.status_code}"
    payload = response.json()
    result = scan_payload(payload, route=template)
    result.raise_for_leak()


@pytest.mark.parametrize("prefix", route_enum.PREFIXES)
def test_each_prefix_has_at_least_one_route(app, prefix):
    counts = route_enum.prefix_report(app)
    assert counts[prefix] >= 1, f"前缀 {prefix} 下没有任何接口（需求要求 11 个前缀全部纳入）"


def test_prefix_count_is_eleven():
    assert len(route_enum.PREFIXES) == 11


def test_unknown_identity_is_rejected(client):
    response = client.get("/api/mini/events", headers={"X-Mini-Identity": "visitor"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "unknown_identity"
