from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Question, User
from ..schemas import (
    AnswerRequest,
    AnswerResponse,
    LeaderboardEntry,
    QuestionOut,
)
from ..services import (
    pick_question,
    process_answer,
    remaining_today,
    reset_daily_if_needed,
    total_left,
    weekly_leaderboard,
    weekly_user_rank,
)

router = APIRouter(tags=["quiz"])

_LIMIT_MESSAGE = "Дневной лимит вопросов исчерпан. Подпишись на канал, чтобы получить ещё."
_CAP_MESSAGE = f"Дневной потолок ({settings.daily_cap} вопросов) достигнут — возвращайся завтра!"


def _require_user(tg_id: int, db: Session) -> User:
    user = db.get(User, tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="user not found")
    reset_daily_if_needed(db, user)
    return user


def _enforce_quota(db: Session, user: User) -> None:
    # жёсткий потолок ответов в день (защита CPA) имеет приоритет
    if remaining_today(db, user) <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "limit_reached": True,
                "daily_left": user.daily_left,
                "bonus_left": user.bonus_left,
                "message": _CAP_MESSAGE,
            },
        )
    if total_left(user) <= 0:
        raise HTTPException(
            status_code=402,
            detail={
                "limit_reached": True,
                "daily_left": user.daily_left,
                "bonus_left": user.bonus_left,
                "message": _LIMIT_MESSAGE,
            },
        )


@router.get("/question", response_model=QuestionOut, summary="Получить случайный вопрос по теме")
def get_question(topic: str, tg_id: int, db: Session = Depends(get_db)):
    user = _require_user(tg_id, db)
    _enforce_quota(db, user)
    q = pick_question(db, topic, user.tg_id, user.skill_level)
    if q is None:
        raise HTTPException(
            status_code=404,
            detail="Ты ответил на все вопросы этой темы 🎉 Загляни в другую!",
        )
    return q


@router.post("/answer", response_model=AnswerResponse, summary="Проверить ответ")
def submit_answer(payload: AnswerRequest, db: Session = Depends(get_db)):
    user = _require_user(payload.tg_id, db)
    _enforce_quota(db, user)

    question = db.get(Question, payload.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="question not found")

    result = process_answer(db, user, question, payload.answer)
    return AnswerResponse(**result, limit_reached=(remaining_today(db, user) <= 0 or total_left(user) <= 0))


def _append_self(db: Session, tg_id: int, topic: str | None, entries: list[LeaderboardEntry]) -> list[LeaderboardEntry]:
    """Добавляет строку текущего пользователя, если его нет в топе (ТЗ 2.2)."""
    if not tg_id or any(e.tg_id == tg_id for e in entries):
        return entries
    rank, correct, total = weekly_user_rank(db, tg_id, topic)
    if rank is None:
        return entries
    u = db.get(User, tg_id)
    entries.append(
        LeaderboardEntry(
            tg_id=tg_id,
            username=u.username if u else None,
            score=correct * 10,
            correct=correct,
            total=total,
            active_badge=u.active_badge if u else None,
            rank=rank,
        )
    )
    return entries


@router.get(
    "/leaderboard/global",
    response_model=list[LeaderboardEntry],
    summary="Общий лидерборд за 7 дней",
)
def leaderboard_global(tg_id: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Скользящее окно 7 дней по всем темам; ранг по числу верных ответов."""
    limit = max(1, min(limit, 500))
    rows = weekly_leaderboard(db, None, limit)
    entries = [
        LeaderboardEntry(
            tg_id=r.user_tg_id,
            username=r.username,
            score=int(r.correct or 0) * 10,
            correct=int(r.correct or 0),
            total=int(r.total or 0),
            active_badge=r.active_badge,
            rank=i + 1,
        )
        for i, r in enumerate(rows)
    ]
    return _append_self(db, tg_id, None, entries)


@router.get("/leaderboard", response_model=list[LeaderboardEntry], summary="Лидерборд по теме за 7 дней")
def leaderboard(topic: str, tg_id: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 500))
    rows = weekly_leaderboard(db, topic, limit)
    entries = [
        LeaderboardEntry(
            tg_id=r.user_tg_id,
            username=r.username,
            score=int(r.correct or 0) * 10,
            correct=int(r.correct or 0),
            total=int(r.total or 0),
            active_badge=r.active_badge,
            rank=i + 1,
        )
        for i, r in enumerate(rows)
    ]
    return _append_self(db, tg_id, topic, entries)
