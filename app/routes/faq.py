from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/faq", tags=["faq"])


@router.get("")
def list_faq():
    items = store.faq_entries()
    return injection.apply_override("/api/mini/faq", envelope({"items": items, "total": len(items)}))


@router.get("/{faq_id}")
def get_faq(faq_id: str):
    row = store.faq_entry(faq_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "faq_not_found", "faq_id": faq_id})
    return injection.apply_override("/api/mini/faq/{faq_id}", envelope(row))
