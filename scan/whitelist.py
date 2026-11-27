"""数字串白名单：票号等「必须返回」的纯数字串在此显式登记。

设计口径：
1. 白名单按 (路由模板, 字段路径后缀, 正则) 三元组登记，粒度到字段，不做「整条规则关掉」；
2. 命中白名单的字段仍在报告里单列一节，评审能看见放过了什么、为什么放过；
3. 未登记的长数字串一律按可疑处理——如果它长得像手机号，就会被手机号正则抓到。
"""
from __future__ import annotations

import re

PHONE = re.compile(r"1[3-9]\d{9}")
LANDLINE = re.compile(r"0\d{2,3}-?\d{7,8}")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
WXID = re.compile(r"wxid_[0-9a-zA-Z]+")
MASKED_PHONE = re.compile(r"1[3-9]\d\*{2,}\d{4}")
MASKED_TAIL = re.compile(r"\*{3,}\d{4}")
MASKED_HEAD = re.compile(r"1[3-9]\d\*{3,}")


class AllowRule:
    __slots__ = ("route", "field_suffix", "pattern", "reason")

    def __init__(self, route: str, field_suffix: str, pattern: str, reason: str) -> None:
        self.route = route
        self.field_suffix = field_suffix
        self.pattern = re.compile(pattern)
        self.reason = reason

    def matches(self, route: str, field_path: str, value: str) -> bool:
        if route != self.route:
            return False
        if not field_path.endswith(self.field_suffix):
            return False
        return bool(self.pattern.fullmatch(value))


ALLOW_RULES: tuple[AllowRule, ...] = (
    AllowRule(
        route="/api/mini/tickets",
        field_suffix="ticket_no",
        pattern=r"\d{16}",
        reason="电子票票号：16 位纯数字，签发时生成，不含任何手机号片段",
    ),
    AllowRule(
        route="/api/mini/tickets/{ticket_key}",
        field_suffix="ticket_no",
        pattern=r"\d{16}",
        reason="电子票票号（详情接口同源同格式）",
    ),
    AllowRule(
        route="/api/mini/support/tickets",
        field_suffix="ticket_id",
        pattern=r"st-\d{4}",
        reason="客服工单号：st- 前缀 + 4 位序号，非手机号",
    ),
    AllowRule(
        route="/api/mini/privacy/export",
        field_suffix="export_id",
        pattern=r"exp-\d{8}-\d{4}",
        reason="个人信息导出凭据编号：exp- 前缀 + 日期 + 4 位序号，纯业务标识",
    ),
    AllowRule(
        route="/api/mini/privacy/deletion",
        field_suffix="request_id",
        pattern=r"del-\d{8}-\d{4}",
        reason="注销申请单号：del- 前缀 + 日期 + 4 位序号，纯业务标识",
    ),
)


def allowlisted(route: str, field_path: str, value: str) -> AllowRule | None:
    if not isinstance(value, str):
        return None
    for rule in ALLOW_RULES:
        if rule.matches(route, field_path, value):
            return rule
    return None


def describe() -> list[dict[str, str]]:
    return [
        {
            "route": rule.route,
            "field_suffix": rule.field_suffix,
            "pattern": rule.pattern.pattern,
            "reason": rule.reason,
        }
        for rule in ALLOW_RULES
    ]
