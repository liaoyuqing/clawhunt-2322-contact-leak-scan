r"""演示开关：只在本地取证时用，默认全关，且有两道闸。

两个开关都不改源码，只让被测系统在运行时呈现「漏登记接口」与「接口返回联系方式」两种形态，
供 AC1 / AC2 的日志取证。

闸一：必须同时设 LEAK_DEMO_ALLOW=1，单独设下面两个变量不会生效。
闸二：CI 环境（CI=true）一律拒绝激活，哪怕两个变量都设了。

- LEAK_DEMO_EXTRA_ROUTE=<path>：再挂一条未登记路由（AC1 用）；
- LEAK_DEMO_LEAK=<route>：让该路由返回带虚构联系方式的数据（AC2 用）。

注：这里不是测试替身，是被测系统的可控开关；两个变量都不设时，行为与生产一致。
"""
from __future__ import annotations

import os

from fastapi import FastAPI

from app import injection

ALLOW_ENV = "LEAK_DEMO_ALLOW"
EXTRA_ROUTE_ENV = "LEAK_DEMO_EXTRA_ROUTE"
LEAK_ENV = "LEAK_DEMO_LEAK"

DEMO_LEAK_BODY = {
    "data": {
        "items": [
            {
                "ticket_id": "st-1001",
                "case_id": "c-1001",
                "subject": "改签申请（虚构）",
                "state": "in_progress",
                "sla_hours": 24,
                "contact_phone": "13800138000",
            }
        ],
        "total": 1,
    }
}


def demo_enabled() -> bool:
    """两道闸都过才允许激活：显式放行 + 不在 CI 里。"""
    if os.environ.get(ALLOW_ENV, "").strip() != "1":
        return False
    if os.environ.get("CI", "").strip().lower() in {"1", "true", "yes"}:
        return False
    return True


def extra_route() -> str | None:
    if not demo_enabled():
        return None
    value = os.environ.get(EXTRA_ROUTE_ENV, "").strip()
    return value or None


def leak_route() -> str | None:
    if not demo_enabled():
        return None
    value = os.environ.get(LEAK_ENV, "").strip()
    return value or None


def register_extra_route(app: FastAPI) -> str | None:
    path = extra_route()
    if path is None:
        return None

    @app.get(path)
    def _demo_extra_route():  # pragma: no cover - 只在本地取证时挂载
        return {"data": {"demo": True}}

    return path


def register_demo_leak() -> str | None:
    path = leak_route()
    if path is None:
        return None
    injection.register(path, DEMO_LEAK_BODY)
    return path
