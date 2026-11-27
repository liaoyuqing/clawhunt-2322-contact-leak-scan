from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app import injection, store
from app.identity import MEMBER, require
from app.responses import envelope

router = APIRouter(prefix="/api/mini/me", tags=["me"])


def _questionnaire_rows() -> list[dict]:
    rows = []
    for row in store.dataset().get("questionnaires", []):
        rows.append({
            "questionnaire_id": row.get("questionnaire_id"),
            "question_id": row.get("question_id"),
            "prompt": row.get("prompt"),
            "answer_kind": row.get("answer_kind"),
        })
    return rows


@router.get("/profile")
def get_profile(_: str = Depends(require(MEMBER))):
    return injection.apply_override("/api/mini/me/profile", envelope(store.member_profile()))


@router.get("/questionnaires")
def list_questionnaires():
    items = _questionnaire_rows()
    return injection.apply_override("/api/mini/me/questionnaires", envelope({"items": items, "total": len(items)}))


@router.get("/questionnaires/{questionnaire_id}")
def get_questionnaire(questionnaire_id: str):
    items = [row for row in _questionnaire_rows() if row["questionnaire_id"] == questionnaire_id]
    if not items:
        raise HTTPException(status_code=404, detail={"code": "questionnaire_not_found", "questionnaire_id": questionnaire_id})
    return injection.apply_override(
        "/api/mini/me/questionnaires/{questionnaire_id}",
        envelope({"questionnaire_id": questionnaire_id, "questions": items}),
    )
