from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/signups", tags=["signups"])


class SignupRequest(BaseModel):
    event_id: str = Field(min_length=1, max_length=64)


@router.get("")
def list_signups():
    items = store.signups()
    return injection.apply_override("/api/mini/signups", envelope({"items": items, "total": len(items)}))


@router.post("")
def create_signup(payload: SignupRequest):
    if store.event(payload.event_id) is None:
        raise HTTPException(status_code=404, detail={"code": "event_not_found", "event_id": payload.event_id})
    body = {"signup_id": "sg-pending", "event_id": payload.event_id, "state": "confirmed", "seat_no": None}
    return injection.apply_override("/api/mini/signups", envelope(body, created=True))


@router.get("/{signup_id}")
def get_signup(signup_id: str):
    row = store.signup(signup_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "signup_not_found", "signup_id": signup_id})
    return injection.apply_override("/api/mini/signups/{signup_id}", envelope(row))
