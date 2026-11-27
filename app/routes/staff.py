from __future__ import annotations

from fastapi import APIRouter, Depends

from app import injection, store
from app.identity import STAFF, require
from app.responses import envelope

router = APIRouter(prefix="/api/mini/staff", tags=["staff"])


@router.get("/profile")
def get_staff_profile(_: str = Depends(require(STAFF))):
    return injection.apply_override("/api/mini/staff/profile", envelope(store.staff_profile(0)))


@router.get("/cases")
def list_staff_cases(_: str = Depends(require(STAFF))):
    items = [
        {
            "case_id": row["case_id"],
            "subject": row["subject"],
            "state": row["state"],
            "updated_at": row["updated_at"],
            "handler_display_name": row["handler_display_name"],
        }
        for row in store.support_cases()
    ]
    return injection.apply_override("/api/mini/staff/cases", envelope({"items": items, "total": len(items)}))


@router.get("/shifts")
def list_staff_shifts(_: str = Depends(require(STAFF))):
    items = [
        {"shift_id": "sh-01", "name": "早班", "starts_at": "08:30", "ends_at": "17:30", "headcount": 3},
        {"shift_id": "sh-02", "name": "晚班", "starts_at": "13:00", "ends_at": "21:00", "headcount": 2},
    ]
    return injection.apply_override("/api/mini/staff/shifts", envelope({"items": items, "total": len(items)}))
