from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Badge, User
from ..schemas import BadgeDef
from ..services import BADGES

router = APIRouter(prefix="/badges", tags=["badges"])


@router.get("", response_model=list[BadgeDef], summary="Все значки + статус получения")
def list_badges(tg_id: int, db: Session = Depends(get_db)):
    user = db.get(User, tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    earned = set(
        db.execute(
            select(Badge.badge_key).where(Badge.user_tg_id == tg_id)
        )
        .scalars()
        .all()
    )
    return [
        BadgeDef(
            key=b["key"],
            emoji=b["emoji"],
            title=b["title"],
            desc=b["desc"],
            earned=b["key"] in earned,
        )
        for b in BADGES
    ]
