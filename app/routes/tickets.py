from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/tickets", tags=["tickets"])


@router.get("")
def list_tickets():
    items = store.tickets()
    return injection.apply_override("/api/mini/tickets", envelope({"items": items, "total": len(items)}))


@router.get("/{ticket_key}")
def get_ticket(ticket_key: str):
    row = store.ticket(ticket_key)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "ticket_not_found", "ticket_key": ticket_key})
    return injection.apply_override("/api/mini/tickets/{ticket_key}", envelope(row))
