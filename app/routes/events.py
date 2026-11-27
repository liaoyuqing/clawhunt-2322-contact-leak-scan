from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/events", tags=["events"])


@router.get("")
def list_events():
    body = envelope({"items": store.events(), "total": len(store.events())}, page=1, page_size=20)
    return injection.apply_override("/api/mini/events", body)


@router.get("/{event_id}")
def get_event(event_id: str):
    row = store.event(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "event_not_found", "event_id": event_id})
    return injection.apply_override("/api/mini/events/{event_id}", envelope(row))


@router.get("/{event_id}/agenda")
def get_event_agenda(event_id: str):
    row = store.event_agenda(event_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "event_not_found", "event_id": event_id})
    return injection.apply_override("/api/mini/events/{event_id}/agenda", envelope(row))
