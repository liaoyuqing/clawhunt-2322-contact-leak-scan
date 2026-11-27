"""会员小程序后端接口桩：11 个路由前缀，全部返回虚构数据。

本单交付的是「扫描器 + 回归测试 + CI」，不是会员小程序后端本身；
路由桩的作用是让扫描器有一个真实可枚举的 FastAPI 路由表可以跑。
对接点：客户把 app/routes/* 换成自家实现时，只要路由前缀与响应外壳不变，
scan/ 与 tests/ 原样可用（README 的「对接点」一节写了替换步骤）。
"""
from __future__ import annotations

from fastapi import Depends, FastAPI

from app import demo_hooks
from app.identity import identity_from_header
from app.routes import (
    butler,
    events,
    faq,
    me,
    posts,
    privacy,
    signups,
    staff,
    subscriptions,
    support,
    tickets,
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="会员小程序接口桩（虚构数据）",
        version="0.1.0",
        description="仅供联系方式泄露回归测试使用；所有数据均为虚构样例。",
    )
    # 每个路由都先解析身份：未知身份一律 400。
    # 对接点：把 identity_from_header 换成解析微信登录态 / 员工 token 的实现即可，
    # 路由本身不需要改。
    guards = [Depends(identity_from_header)]
    for module in (events, signups, tickets, me, posts, faq, support, butler, subscriptions, privacy, staff):
        app.include_router(module.router, dependencies=guards)
    # 演示开关（默认全关）：AC1 / AC2 的故障注入日志靠这两个环境变量复现。
    demo_hooks.register_extra_route(app)
    demo_hooks.register_demo_leak()
    return app


app = create_app()
