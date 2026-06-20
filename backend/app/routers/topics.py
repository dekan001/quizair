from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Topic
from ..schemas import TopicOut

router = APIRouter(prefix="/topics", tags=["topics"])


@router.get("", response_model=list[TopicOut], summary="Список тем квизов")
def list_topics(db: Session = Depends(get_db)):
    return (
        db.execute(
            select(Topic)
            .where(Topic.active.is_(True))
            .order_by(Topic.position)
        )
        .scalars()
        .all()
    )
