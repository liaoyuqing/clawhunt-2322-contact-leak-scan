"""演示开关：只用环境变量触发，供 AC1 / AC2 的「人为制造故障」日志取证。

两个开关都从环境变量读，默认全关；CI 不设这两个变量，所以 CI 上恒为真实基线。

- LEAK_DEMO_EXTRA_ROUTE=<path>：往 app 里再挂一条未登记的路由，用来演示
  「新增接口漏登记时测试变红」（AC1）；
- LEAK_DEMO_LEAK=<route>：让该路由返回带虚构手机号的响应，用来演示
  「接口泄露联系方式时测试变红，并打印接口路径与字段路径」（AC2）。

注：这不是测试替身，而是被测系统的可控故障注入点，删掉两个环境变量即恢复。
"""
from __future__ import annotations

import os

from fastapi import FastAPI

from app import injection

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


def extra_route() -> str | None:
    value = os.environ.get(EXTRA_ROUTE_ENV, "").strip()
    return value or None


def leak_route() -> str | None:
    value = os.environ.get(LEAK_ENV, "").strip()
    return value or None


def register_extra_route(app: FastAPI) -> str | None:
    path = extra_route()
    if path is None:
        return None

    @app.get(path)
    def _demo_extra_route():  # pragma: no cover - 只在演示时挂载
        return {"data": {"demo": True}}

    return path


def register_demo_leak() -> str | None:
    path = leak_route()
    if path is None:
        return None
    injection.register(path, DEMO_LEAK_BODY)
    return path
