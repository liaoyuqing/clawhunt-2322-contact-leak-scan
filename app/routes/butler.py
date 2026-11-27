from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app import injection, store
from app.responses import envelope

router = APIRouter(prefix="/api/mini/butler", tags=["butler"])


@router.get("/tasks")
def list_tasks():
    items = store.butler_tasks()
    return injection.apply_override("/api/mini/butler/tasks", envelope({"items": items, "total": len(items)}))


@router.get("/tasks/{task_id}")
def get_task(task_id: str):
    row = store.butler_task(task_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "task_not_found", "task_id": task_id})
    return injection.apply_override("/api/mini/butler/tasks/{task_id}", envelope(row))
