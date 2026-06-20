from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Conversion, Partner, User
from ..schemas import ClaimResult, TaskOut
from ..services import AlreadyClaimedError, claim_task
from ..tg import is_subscriber

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _require_user(tg_id: int, db: Session) -> User:
    user = db.get(User, tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    return user


@router.get("", response_model=list[TaskOut], summary="Список заданий (подписки за слоты)")
def list_tasks(tg_id: int, db: Session = Depends(get_db)):
    user = _require_user(tg_id, db)
    claimed_ids = set(
        db.execute(
            select(Conversion.partner_id).where(
                Conversion.user_tg_id == user.tg_id
            )
        )
        .scalars()
        .all()
    )
    rows = (
        db.execute(
            select(Partner)
            .where(Partner.active.is_(True))
            .order_by(Partner.reward_quizzes.desc(), Partner.cpa_rate.desc())
        )
        .scalars()
        .all()
    )
    return [
        TaskOut(
            id=p.id,
            channel_username=p.channel_username,
            topic=p.topic,
            reward_quizzes=p.reward_quizzes,
            cpa_rate=float(p.cpa_rate),
            claimed=p.id in claimed_ids,
        )
        for p in rows
    ]


@router.post(
    "/{partner_id}/claim",
    response_model=ClaimResult,
    summary="Выполнить задание — получить бонусные слоты",
)
async def claim(partner_id: int, tg_id: int, db: Session = Depends(get_db)):
    user = _require_user(tg_id, db)
    partner = db.get(Partner, partner_id)
    if partner is None or not partner.active:
        raise HTTPException(status_code=404, detail="task not found")

    # проверка реальной подписки (выключена в dev, пока нет токена бота)
    channel = partner.channel_id or partner.channel_username
    if not await is_subscriber(channel, tg_id):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "not_subscribed",
                "channel": partner.channel_username,
                "message": f"Сначала подпишись на {partner.channel_username}",
            },
        )

    try:
        claim_task(db, user, partner)
    except AlreadyClaimedError:
        raise HTTPException(status_code=409, detail="already claimed")
    return ClaimResult(
        daily_left=user.daily_left,
        bonus_left=user.bonus_left,
        reward_given=partner.reward_quizzes,
    )
