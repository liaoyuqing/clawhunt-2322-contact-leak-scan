from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/posts", tags=["posts"])


@router.get("")
def list_posts():
    items = store.posts()
    return injection.apply_override("/api/mini/posts", envelope({"items": items, "total": len(items)}))


@router.get("/{post_id}")
def get_post(post_id: str):
    row = store.post(post_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "post_not_found", "post_id": post_id})
    return injection.apply_override("/api/mini/posts/{post_id}", envelope(row))
