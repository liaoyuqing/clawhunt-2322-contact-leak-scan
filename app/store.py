"""接口桩的数据层：读 fixtures/dataset.json，只输出「公开投影」。

公开投影 = 只保留对外允许的键 + 自由文本过 redact_text。
联系方式字段（手机 / 座机 / 邮箱 / 微信 / QQ）一律不出现在投影里——
这正是本单扫描器要守住的性质。
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from app.redact import redact_text

DATASET_PATH = Path(__file__).resolve().parent.parent / "fixtures" / "dataset.json"


@lru_cache(maxsize=1)
def dataset() -> dict:
    with DATASET_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _table(name: str) -> list[dict]:
    return list(dataset().get(name, []))


def events() -> list[dict]:
    keys = ("event_id", "slug", "title", "starts_at", "venue_name", "capacity", "host_org")
    return [{key: row.get(key) for key in keys} for row in _table("events")]


def event(event_id: str) -> dict | None:
    for row in events():
        if row["event_id"] == event_id:
            return row
    return None


def event_agenda(event_id: str) -> dict | None:
    for row in _table("events"):
        if row["event_id"] == event_id:
            text = row.get("agenda", "")
            return {"event_id": event_id, "agenda": redact_text(text), "lines": len(text.split("；"))}
    return None


def signups() -> list[dict]:
    keys = ("signup_id", "event_id", "state", "seat_no", "checked_in", "created_at")
    return [{key: row.get(key) for key in keys} for row in _table("signups")]


def signup(signup_id: str) -> dict | None:
    for row in signups():
        if row["signup_id"] == signup_id:
            return row
    return None


def tickets() -> list[dict]:
    keys = ("ticket_key", "ticket_no", "event_id", "state", "seat_zone", "issued_at")
    return [{key: row.get(key) for key in keys} for row in _table("tickets")]


def ticket(ticket_key: str) -> dict | None:
    for row in tickets():
        if row["ticket_key"] == ticket_key:
            return row
    return None


def posts() -> list[dict]:
    keys = ("post_id", "author_display_name", "created_at", "like_count", "comment_count")
    rows = []
    for row in _table("posts"):
        item = {key: row.get(key) for key in keys}
        item["body"] = redact_text(row.get("body", ""))
        rows.append(item)
    return rows


def post(post_id: str) -> dict | None:
    for row in posts():
        if row["post_id"] == post_id:
            return row
    return None


def faq_entries() -> list[dict]:
    rows = []
    for row in _table("faq_answers"):
        rows.append({
            "faq_id": row.get("faq_id"),
            "question": row.get("question"),
            "answer": redact_text(row.get("answer", "")),
            "updated_at": row.get("updated_at"),
        })
    return rows


def faq_entry(faq_id: str) -> dict | None:
    for row in faq_entries():
        if row["faq_id"] == faq_id:
            return row
    return None


def support_cases() -> list[dict]:
    rows = []
    replies = {row["case_id"]: row for row in _table("staff_replies")}
    for row in _table("support_cases"):
        reply = replies.get(row["case_id"], {})
        rows.append({
            "case_id": row.get("case_id"),
            "subject": row.get("subject"),
            "state": row.get("state"),
            "updated_at": row.get("updated_at"),
            "handler_display_name": row.get("handler_display_name"),
            "last_reply": redact_text(reply.get("reply_body", "")),
        })
    return rows


def support_case(case_id: str) -> dict | None:
    for row in support_cases():
        if row["case_id"] == case_id:
            return row
    return None


def support_tickets() -> list[dict]:
    """客服工单列表（AC2 的注入目标接口）。工单只带业务键，不带任何联系方式。"""
    rows = []
    for index, case in enumerate(_table("support_cases"), start=1):
        rows.append({
            "ticket_id": "st-%04d" % (1000 + index),
            "case_id": case.get("case_id"),
            "subject": case.get("subject"),
            "state": case.get("state"),
            "sla_hours": 24,
            "updated_at": case.get("updated_at"),
        })
    return rows


def butler_tasks() -> list[dict]:
    keys = ("task_id", "title", "state", "due_at")
    return [{key: row.get(key) for key in keys} for row in _table("butler_tasks")]


def butler_task(task_id: str) -> dict | None:
    for row in butler_tasks():
        if row["task_id"] == task_id:
            return row
    return None


def subscriptions() -> list[dict]:
    keys = ("template_id", "title", "scene", "state", "enabled")
    return [{key: row.get(key) for key in keys} for row in _table("subscriptions")]


def member_profile() -> dict:
    member = _table("members")[0]
    return {
        "member_id": member.get("member_id"),
        "display_name": member.get("display_name"),
        "tier": member.get("tier"),
        "org_name": member.get("org_name"),
        "joined_at": member.get("joined_at"),
    }


def staff_profile(index: int = 0) -> dict:
    staff = _table("staff")[index]
    return {
        "staff_id": staff.get("staff_id"),
        "display_name": staff.get("display_name"),
        "shift": staff.get("shift"),
    }
