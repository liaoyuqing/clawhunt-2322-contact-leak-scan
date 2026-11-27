"""演示开关的两道闸：必须显式放行，且在 CI 里一律拒绝。

这两个开关是取证用的，不能被误带进生产或 CI——所以单独写用例守住闸门，
而不是靠「记得别设环境变量」。
"""
from __future__ import annotations

import pytest

from app import demo_hooks


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for name in (demo_hooks.ALLOW_ENV, demo_hooks.EXTRA_ROUTE_ENV, demo_hooks.LEAK_ENV, "CI"):
        monkeypatch.delenv(name, raising=False)
    yield


def test_disabled_by_default():
    assert demo_hooks.demo_enabled() is False
    assert demo_hooks.extra_route() is None
    assert demo_hooks.leak_route() is None


def test_route_var_alone_is_not_enough(monkeypatch):
    monkeypatch.setenv(demo_hooks.EXTRA_ROUTE_ENV, "/api/mini/events/__leak_probe")
    assert demo_hooks.demo_enabled() is False, "只设路由变量不该激活"
    assert demo_hooks.extra_route() is None


def test_leak_var_alone_is_not_enough(monkeypatch):
    monkeypatch.setenv(demo_hooks.LEAK_ENV, "/api/mini/support/tickets")
    assert demo_hooks.demo_enabled() is False
    assert demo_hooks.leak_route() is None


def test_both_gates_open_then_enabled(monkeypatch):
    monkeypatch.setenv(demo_hooks.ALLOW_ENV, "1")
    monkeypatch.setenv(demo_hooks.EXTRA_ROUTE_ENV, "/api/mini/events/__leak_probe")
    assert demo_hooks.demo_enabled() is True
    assert demo_hooks.extra_route() == "/api/mini/events/__leak_probe"


@pytest.mark.parametrize("ci_value", ["1", "true", "TRUE", "yes"])
def test_ci_always_blocks_even_when_allowed(monkeypatch, ci_value):
    monkeypatch.setenv(demo_hooks.ALLOW_ENV, "1")
    monkeypatch.setenv(demo_hooks.EXTRA_ROUTE_ENV, "/api/mini/events/__leak_probe")
    monkeypatch.setenv("CI", ci_value)
    assert demo_hooks.demo_enabled() is False, "CI 环境下必须拒绝激活"
    assert demo_hooks.extra_route() is None


def test_allow_value_must_be_exactly_one(monkeypatch):
    monkeypatch.setenv(demo_hooks.ALLOW_ENV, "true")
    assert demo_hooks.demo_enabled() is False, "放行值必须逐字为 1"


def test_app_has_no_demo_route_by_default(app):
    from scan import enumerate as route_enum

    assert "/api/mini/events/__leak_probe" not in route_enum.enumerate_templates(app)
