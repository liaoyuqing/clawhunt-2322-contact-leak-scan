from __future__ import annotations

from fastapi import APIRouter, Depends, status

from app import injection, store
from app.identity import MEMBER, require
from app.responses import envelope

router = APIRouter(prefix="/api/mini/privacy", tags=["privacy"])


@router.get("/policy")
def get_policy():
    body = {
        "version": "2026.11",
        "sections": ["信息收集范围", "使用目的", "共享与转让", "保存期限", "注销与删除"],
        "support_entry": "小程序内客服工单",
    }
    return injection.apply_override("/api/mini/privacy/policy", envelope(body))


@router.get("/export")
def get_export():
    """个人信息导出：只给字段清单与下载凭据编号，不回传任何联系方式字段。"""
    body = {
        "export_id": "exp-20261127-0001",
        "fields": ["display_name", "tier", "joined_at", "signup_history", "ticket_history"],
        "format": "json",
        "expires_in_hours": 24,
    }
    return injection.apply_override("/api/mini/privacy/export", envelope(body))


@router.post("/deletion", status_code=status.HTTP_202_ACCEPTED)
def request_deletion(_: str = Depends(require(MEMBER))):
    body = {"request_id": "del-20261127-0001", "state": "pending_review", "grace_days": 15}
    return injection.apply_override("/api/mini/privacy/deletion", envelope(body, created=True))
