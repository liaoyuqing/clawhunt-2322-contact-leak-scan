"""显式登记表：路由模板 -> 用例标识。

登记表是「接口已覆盖」的唯一凭据。原则：
1. 手工维护是刻意的——故意不做自动生成，新增接口必须有人显式登记；
2. 键是 FastAPI 的路由模板（带 /{param} 占位），不是具体 URL，
   所以 /api/mini/events/{event_id} 与 /api/mini/events/evt-1001 会被当成同一条；
3. 登记值是用例标识，报告里逐行打印，便于反查是哪条用例守的。
"""
from __future__ import annotations

REGISTRY: dict[str, str] = {
    # 活动
    "/api/mini/events": "tests/test_api_surface_member.py::events_list",
    "/api/mini/events/{event_id}": "tests/test_api_surface_member.py::events_detail",
    "/api/mini/events/{event_id}/agenda": "tests/test_api_surface_member.py::events_agenda",
    # 报名
    "/api/mini/signups": "tests/test_api_surface_member.py::signups_list_and_create",
    "/api/mini/signups/{signup_id}": "tests/test_api_surface_member.py::signups_detail",
    # 电子票
    "/api/mini/tickets": "tests/test_api_surface_member.py::tickets_list",
    "/api/mini/tickets/{ticket_key}": "tests/test_api_surface_member.py::tickets_detail",
    # 会员自身（问卷与档案）
    "/api/mini/me/profile": "tests/test_api_surface_member.py::me_profile",
    "/api/mini/me/questionnaires": "tests/test_api_surface_member.py::me_questionnaires",
    "/api/mini/me/questionnaires/{questionnaire_id}": "tests/test_api_surface_member.py::me_questionnaire_detail",
    # 动态（航海日志）
    "/api/mini/posts": "tests/test_api_surface_member.py::posts_list",
    "/api/mini/posts/{post_id}": "tests/test_api_surface_member.py::posts_detail",
    # FAQ
    "/api/mini/faq": "tests/test_api_surface_member.py::faq_list",
    "/api/mini/faq/{faq_id}": "tests/test_api_surface_member.py::faq_detail",
    # 客服与转人工
    "/api/mini/support/cases": "tests/test_api_surface_member.py::support_cases",
    "/api/mini/support/cases/{case_id}": "tests/test_api_surface_member.py::support_case_detail",
    "/api/mini/support/tickets": "tests/test_api_surface_member.py::support_tickets",
    "/api/mini/support/handoff": "tests/test_api_surface_member.py::support_handoff",
    # 管家
    "/api/mini/butler/tasks": "tests/test_api_surface_member.py::butler_tasks",
    "/api/mini/butler/tasks/{task_id}": "tests/test_api_surface_member.py::butler_task_detail",
    # 订阅消息
    "/api/mini/subscriptions": "tests/test_api_surface_member.py::subscriptions_list",
    "/api/mini/subscriptions/{template_id}/toggle": "tests/test_api_surface_member.py::subscriptions_toggle",
    # 隐私与注销
    "/api/mini/privacy/policy": "tests/test_api_surface_member.py::privacy_policy",
    "/api/mini/privacy/export": "tests/test_api_surface_member.py::privacy_export",
    "/api/mini/privacy/deletion": "tests/test_api_surface_member.py::privacy_deletion",
    # 员工端
    "/api/mini/staff/profile": "tests/test_api_surface_member.py::staff_profile",
    "/api/mini/staff/cases": "tests/test_api_surface_member.py::staff_cases",
    "/api/mini/staff/shifts": "tests/test_api_surface_member.py::staff_shifts",
}


def registered_templates() -> set[str]:
    return set(REGISTRY.keys())


def undeclared(found: set[str]) -> list[str]:
    return sorted(found - registered_templates())


def stale(found: set[str]) -> list[str]:
    """登记了但路由表里已经不存在的模板（已下线接口）。由测试显式告警，不参与失败判定。"""
    return sorted(registered_templates() - found)
