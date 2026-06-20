from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Badge, Referral, User
from ..schemas import ActiveBadgeRequest, ReferralInfo, UserCreate, UserOut
from ..services import record_referral, reset_daily_if_needed

router = APIRouter(prefix="/users", tags=["users"])

_PROFILE_FIELDS = ("username", "first_name", "photo_url")


@router.post("", response_model=UserOut, summary="Создать или получить пользователя")
def create_or_get_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.get(User, payload.tg_id)
    if user is None:
        user = User(
            tg_id=payload.tg_id,
            username=payload.username,
            first_name=payload.first_name,
            photo_url=payload.photo_url,
            referred_by=payload.referred_by,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        record_referral(db, user)  # зафиксировать, кого он пригласил
    else:
        # актуализируем профиль из актуальных данных TG
        changed = False
        for f in _PROFILE_FIELDS:
            nv = getattr(payload, f)
            if nv and getattr(user, f) != nv:
                setattr(user, f, nv)
                changed = True
        if changed:
            db.commit()
    reset_daily_if_needed(db, user)
    db.refresh(user)
    return user


@router.get("/{tg_id}", response_model=UserOut, summary="Профиль пользователя")
def get_user(tg_id: int, db: Session = Depends(get_db)):
    user = db.get(User, tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    reset_daily_if_needed(db, user)
    db.refresh(user)
    return user


@router.post(
    "/{tg_id}/active-badge",
    response_model=UserOut,
    summary="Выбрать активный значок для лидерборда",
)
def set_active_badge(
    tg_id: int, payload: ActiveBadgeRequest, db: Session = Depends(get_db)
):
    user = db.get(User, tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    if payload.badge_key is not None:
        owned = db.execute(
            select(Badge.badge_key).where(
                Badge.user_tg_id == tg_id, Badge.badge_key == payload.badge_key
            )
        ).scalar_one_or_none()
        if owned is None:
            raise HTTPException(status_code=403, detail="badge not earned")
    user.active_badge = payload.badge_key
    db.commit()
    db.refresh(user)
    return user


@router.get(
    "/{tg_id}/referral",
    response_model=ReferralInfo,
    summary="Реферальная ссылка и статистика",
)
def get_referral(tg_id: int, db: Session = Depends(get_db)):
    user = db.get(User, tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    total = db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_tg_id == tg_id)
    ).scalar_one()
    active = db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_tg_id == tg_id, Referral.rewarded.is_(True))
    ).scalar_one()
    return ReferralInfo(
        ref_link=f"https://t.me/{settings.bot_username}?start=ref_{tg_id}",
        bot_username=settings.bot_username,
        referrals_total=int(total),
        referrals_active=int(active),
    )
