from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/subscriptions", tags=["subscriptions"])


@router.get("")
def list_subscriptions():
    items = store.subscriptions()
    return injection.apply_override("/api/mini/subscriptions", envelope({"items": items, "total": len(items)}))


@router.post("/{template_id}/toggle")
def toggle_subscription(template_id: str):
    for row in store.subscriptions():
        if row["template_id"] == template_id:
            body = {"template_id": template_id, "enabled": not row.get("enabled", False), "state": row.get("state")}
            return injection.apply_override("/api/mini/subscriptions/{template_id}/toggle", envelope(body, updated=True))
    raise HTTPException(status_code=404, detail={"code": "template_not_found", "template_id": template_id})
