from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/support", tags=["support"])


class HandoffRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    reason: str = Field(default="member_requested", max_length=128)


@router.get("/cases")
def list_cases():
    items = store.support_cases()
    return injection.apply_override("/api/mini/support/cases", envelope({"items": items, "total": len(items)}))


@router.get("/cases/{case_id}")
def get_case(case_id: str):
    row = store.support_case(case_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "case_not_found", "case_id": case_id})
    return injection.apply_override("/api/mini/support/cases/{case_id}", envelope(row))


@router.get("/tickets")
def list_support_tickets():
    items = store.support_tickets()
    return injection.apply_override("/api/mini/support/tickets", envelope({"items": items, "total": len(items)}))


@router.post("/handoff")
def create_handoff(payload: HandoffRequest):
    if store.support_case(payload.case_id) is None:
        raise HTTPException(status_code=404, detail={"code": "case_not_found", "case_id": payload.case_id})
    body = {"case_id": payload.case_id, "handoff_state": "queued", "queue_no": 7, "reason": payload.reason}
    return injection.apply_override("/api/mini/support/handoff", envelope(body, created=True))
