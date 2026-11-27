"""AC1：人为新增一个未登记用例的接口时，测试必须失败（并把路径报出来）。

三组对照：
1. 塞一个新路由 -> 枚举器报出它属于 UNDECLARED_ENDPOINT；
2. 登记表补上它 -> 同一份判定变绿（证明不是硬编码跳过）；
3. 已下线接口（登记表里有、路由表里没有）只告警不失败。
"""
from __future__ import annotations

import pytest
from fastapi import APIRouter

from scan import enumerate as route_enum
from scan.registry import REGISTRY, stale, undeclared

PROBE_PATH = "/api/mini/events/__leak_probe"


def _mount_probe(app, path: str = PROBE_PATH) -> None:
    router = APIRouter()

    @router.get(path)
    def _probe():  # pragma: no cover - 只被测试挂载
        return {"data": {"probe": True}}

    app.include_router(router)


def test_undeclared_route_is_detected(app):
    _mount_probe(app)
    found = set(route_enum.enumerate_templates(app))
    missing = undeclared(found)
    assert PROBE_PATH in missing, "新路由没有出现在未登记清单里，枚举器失效"
    assert missing == [PROBE_PATH]


def test_guard_message_is_verbatim(app):
    _mount_probe(app)
    found = set(route_enum.enumerate_templates(app))
    missing = undeclared(found)
    message = "UNDECLARED_ENDPOINT: " + ", ".join(missing)
    assert message == "UNDECLARED_ENDPOINT: " + PROBE_PATH


def test_guard_fails_the_way_ci_fails(app):
    """模拟 CI：守卫用例失败时 pytest.fail 抛出，消息里必须带接口路径。"""
    _mount_probe(app)
    found = set(route_enum.enumerate_templates(app))
    missing = undeclared(found)
    with pytest.raises(BaseException) as excinfo:
        if missing:
            pytest.fail("UNDECLARED_ENDPOINT: " + ", ".join(missing))
    assert PROBE_PATH in str(excinfo.value)


def test_registering_the_probe_turns_the_guard_green(app, monkeypatch):
    _mount_probe(app)
    monkeypatch.setitem(REGISTRY, PROBE_PATH, "tests/test_registry_guard.py::probe")
    found = set(route_enum.enumerate_templates(app))
    assert undeclared(found) == []


def test_probe_removed_after_use(app):
    """负面对照：不加探针时守卫必须是绿的，否则说明基线本身是脏的。"""
    found = set(route_enum.enumerate_templates(app))
    assert undeclared(found) == []


def test_offline_endpoint_only_warns():
    fake_found = set(REGISTRY) - {"/api/mini/staff/shifts"}
    gone = stale(fake_found)
    assert gone == ["/api/mini/staff/shifts"]
    assert undeclared(fake_found) == []


def test_route_template_with_path_parameter_matches(app):
    """参数化路径按模板比对：/api/mini/events/{event_id} 不因具体 id 变化而失配。"""
    found = set(route_enum.enumerate_templates(app))
    assert "/api/mini/events/{event_id}" in found
    assert "/api/mini/events/evt-1001" not in found
