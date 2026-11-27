"""路由枚举：从 FastAPI 路由表取 11 个前缀下的全部接口模板 / 支持的方法。

刻意从 app.routes 反射取，而不是维护一份手写清单——手写清单正是「新增接口漏测」的成因。
"""
from __future__ import annotations

from fastapi import FastAPI, routing

PREFIXES = (
    "/api/mini/events",
    "/api/mini/signups",
    "/api/mini/tickets",
    "/api/mini/me",
    "/api/mini/posts",
    "/api/mini/faq",
    "/api/mini/support",
    "/api/mini/butler",
    "/api/mini/subscriptions",
    "/api/mini/privacy",
    "/api/mini/staff",
)


def route_template(route: routing.APIRoute) -> str:
    """路由模板：/api/mini/events/{event_id}。参数名保持不变，便于人工核对。"""
    return route.path


def under_prefixes(path: str, prefixes: tuple[str, ...] = PREFIXES) -> bool:
    """前缀按路径段匹配：/api/mini/me 不能把 /api/mini/member 也算进来。"""
    for prefix in prefixes:
        if path == prefix or path.startswith(prefix + "/"):
            return True
    return False


def enumerate_routes(app: FastAPI, prefixes: tuple[str, ...] = PREFIXES) -> dict[str, set[str]]:
    """返回 {路由模板: {方法, ...}}，只保留登记前缀下的接口。"""
    found: dict[str, set[str]] = {}
    for route in app.routes:
        if not isinstance(route, routing.APIRoute):
            continue
        path = route_template(route)
        if not under_prefixes(path, prefixes):
            continue
        found.setdefault(path, set()).update(sorted(route.methods or {"GET"}))
    return found


def enumerate_templates(app: FastAPI, prefixes: tuple[str, ...] = PREFIXES) -> list[str]:
    return sorted(enumerate_routes(app, prefixes))


def prefix_report(app: FastAPI, prefixes: tuple[str, ...] = PREFIXES) -> dict[str, int]:
    """每个前缀下的接口数；某前缀为 0 时由调用方决定告警而不是报错。"""
    counts = {prefix: 0 for prefix in prefixes}
    for path in enumerate_templates(app, prefixes):
        for prefix in prefixes:
            if path == prefix or path.startswith(prefix + "/"):
                counts[prefix] += 1
                break
    return counts
