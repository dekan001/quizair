"""Бизнес-логика: дневной лимит, стрик, обработка ответа.

Единый источник правды для статистики — здесь (а не в БД-триггере),
чтобы код работал одинаково на SQLite (dev) и Postgres/Supabase (prod).
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import case, desc, func, select
from sqlalchemy.orm import Session

from .config import settings
from .models import Answer, Badge, Conversion, Partner, Question, Referral, StreakLog, User, UserTopicStat


# ---------------------------------------------------------------- streak / quota
def streak_bonus(streak: int) -> int:
    """Бонус к дневному лимиту за стрик: 3 дня → +2, 7 дней → +5."""
    if streak >= settings.streak_cap:        # 7
        return settings.streak_bonus_7       # 5
    if streak >= 3:
        return settings.streak_bonus_3       # 2
    return 0


def daily_quota(user: User) -> int:
    """Сколько бесплатных квизов положено сегодня: база + бонус стрика.

    База берётся из профиля пользователя (user.daily_base) — тот же источник,
    что использует фронтенд, чтобы расчёты совпадали.
    """
    return user.daily_base + streak_bonus(user.streak)


def reset_daily_if_needed(db: Session, user: User) -> None:
    """Сброс дневного лимита до квоты (база + бонус стрика) в новый день.

    Вызывается при любом касании пользователя — в том числе при простом
    открытии приложения (так лимит всегда свежий).
    """
    today = date.today()
    if user.quizzes_reset_date == today:
        return
    # сбрасываем ТОЛЬКО возобновляемую дневную часть; bonus_left не трогаем
    user.daily_left = daily_quota(user)
    user.quizzes_reset_date = today
    db.commit()


def bump_streak(db: Session, user: User) -> None:
    """Начисляет день стрика за РЕАЛЬНЫЙ ответ, а не за открытие приложения.

    Если при этом бонус стрика вырос (3 дня → +2, 7 дней → +5), а дневной лимит
    уже сброшен на сегодня — добавляем дельту, чтобы пользователь получил
    положенные вопросы прямо сегодня.
    """
    today = date.today()
    if user.streak_anchor_date == today:
        return  # за сегодня уже начислен

    old_bonus = streak_bonus(user.streak)

    # вчера был активен → +1, иначе серия начинается заново с 1
    if user.streak_anchor_date == today - timedelta(days=1):
        user.streak = min(user.streak + 1, settings.streak_cap)
    else:
        user.streak = 1

    user.longest_streak = max(user.longest_streak, user.streak)
    user.streak_anchor_date = today

    new_bonus = streak_bonus(user.streak)
    if user.quizzes_reset_date == today and new_bonus > old_bonus:
        user.daily_left += new_bonus - old_bonus

    db.merge(StreakLog(user_tg_id=user.tg_id, day_date=today, kept=True))
    db.commit()


# ---------------------------------------------------------------- skill level
CALIBRATION_ANSWERS = 20  # первые 20 ответов — калибровка, уровень держим easy
RECALC_EVERY = 10         # после калибровки пересчитываем уровень каждые 10 ответов
LEVEL_ORDER = {"easy": 0, "medium": 1, "hard": 2}


def recalc_skill_level(db: Session, user: User) -> None:
    """Пересчёт уровня сложности по последним 20 ответам (ТЗ v1.1, механика 1).

    Первые 20 ответов — калибровка (остаётся easy). Дальше каждые 10 ответов:
    < 50% верных → easy, 50–79% → medium, ≥ 80% → hard.
    Вызывать ПОСЛЕ флаша текущего ответа, чтобы он учитывался в окне.
    """
    user.answers_since_recalc += 1

    total = db.execute(
        select(func.count()).select_from(Answer).where(Answer.user_tg_id == user.tg_id)
    ).scalar_one()
    if total < CALIBRATION_ANSWERS or user.answers_since_recalc < RECALC_EVERY:
        return

    last = (
        db.execute(
            select(Answer.is_correct)
            .where(Answer.user_tg_id == user.tg_id)
            .order_by(Answer.answered_at.desc())
            .limit(20)
        )
        .scalars()
        .all()
    )
    if not last:
        return
    pct = sum(1 for x in last if x) / len(last)
    if pct < 0.5:
        user.skill_level = "easy"
    elif pct < 0.8:
        user.skill_level = "medium"
    else:
        user.skill_level = "hard"
    user.answers_since_recalc = 0


# ---------------------------------------------------------------- badges (механика 2)
# Реестр значков. champion (топ-3 за неделю) начисляется недельным cron'ом, не здесь.
BADGES: list[dict[str, str]] = [
    {"key": "on_fire", "emoji": "🔥", "title": "On Fire", "desc": "Streak 7 дней"},
    {"key": "sniper", "emoji": "🎯", "title": "Снайпер", "desc": "10 правильных подряд"},
    {"key": "speed", "emoji": "⚡", "title": "Быстрый", "desc": "10 ответов за 3 минуты"},
    {"key": "ai_guru", "emoji": "🤖", "title": "AI-гуру", "desc": "80%+ верных по ИИ"},
    {"key": "crypto_master", "emoji": "₿", "title": "Крипто-мастер", "desc": "80%+ верных по Крипте"},
    {"key": "psych_master", "emoji": "🧠", "title": "Психолог", "desc": "80%+ верных по Психологии"},
    {"key": "football_expert", "emoji": "⚽", "title": "Эксперт поля", "desc": "80%+ верных по Футболу"},
    {"key": "science_master", "emoji": "🌍", "title": "Учёный", "desc": "80%+ верных по Науке"},
    {"key": "ambassador", "emoji": "👥", "title": "Амбассадор", "desc": "5+ активных рефералов"},
    {"key": "legend", "emoji": "💎", "title": "Легенда", "desc": "500 правильных ответов"},
    {"key": "champion", "emoji": "🏆", "title": "Чемпион", "desc": "Топ-3 глобального топа за неделю"},
]
BADGE_BY_KEY = {b["key"]: b for b in BADGES}
TOPIC_BADGE = {
    "ai": "ai_guru",
    "crypto": "crypto_master",
    "psychology": "psych_master",
    "football": "football_expert",
    "science": "science_master",
}


def _consecutive_correct(db: Session, user: User) -> int:
    rows = (
        db.execute(
            select(Answer.is_correct)
            .where(Answer.user_tg_id == user.tg_id)
            .order_by(Answer.answered_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )
    n = 0
    for r in rows:
        if r:
            n += 1
        else:
            break
    return n


def evaluate_badges(db: Session, user: User) -> set[str]:
    """Множество значков, которым пользователь удовлетворяет прямо сейчас."""
    earned: set[str] = set()
    if user.streak >= settings.streak_cap:
        earned.add("on_fire")
    if user.correct_total >= 500:
        earned.add("legend")
    if _consecutive_correct(db, user) >= 10:
        earned.add("sniper")
    # скорость: 10+ ответов за последние 3 минуты
    since = datetime.now() - timedelta(minutes=3)
    speed_n = db.execute(
        select(func.count())
        .select_from(Answer)
        .where(Answer.user_tg_id == user.tg_id, Answer.answered_at >= since)
    ).scalar_one()
    if speed_n >= 10:
        earned.add("speed")
    # тематические: 80%+ при min 10 попытках
    stats = (
        db.execute(
            select(UserTopicStat).where(UserTopicStat.user_tg_id == user.tg_id)
        )
        .scalars()
        .all()
    )
    for s in stats:
        if s.total >= 10 and s.correct / s.total >= 0.8:
            key = TOPIC_BADGE.get(s.topic)
            if key:
                earned.add(key)
    # амбассадор: 5+ рефералов
    ref_n = db.execute(
        select(func.count())
        .select_from(Referral)
        .where(Referral.referrer_tg_id == user.tg_id, Referral.rewarded.is_(True))
    ).scalar_one()
    if ref_n >= 5:
        earned.add("ambassador")
    # чемпион: входит в топ-3 глобального недельного топа
    top3_ids = [r.user_tg_id for r in weekly_leaderboard(db, None, 3)]
    if user.tg_id in top3_ids:
        earned.add("champion")
    return earned


def award_new_badges(db: Session, user: User) -> list[str]:
    """Вставляет вновь полученные значки. Возвращает ключи новых."""
    qualifying = evaluate_badges(db, user)
    have = set(
        db.execute(
            select(Badge.badge_key).where(Badge.user_tg_id == user.tg_id)
        )
        .scalars()
        .all()
    )
    new = [k for k in qualifying - have if k in BADGE_BY_KEY]
    for k in new:
        db.add(Badge(user_tg_id=user.tg_id, badge_key=k))
    if new and not user.active_badge:
        user.active_badge = new[0]
    return new


# ---------------------------------------------------------------- daily cap (потолок 25)
def answered_today_count(db: Session, user: User) -> int:
    start = datetime.combine(date.today(), time.min)
    return db.execute(
        select(func.count())
        .select_from(Answer)
        .where(Answer.user_tg_id == user.tg_id, Answer.answered_at >= start)
    ).scalar_one()


def remaining_today(db: Session, user: User) -> int:
    """Сколько ещё можно ответить сегодня с учётом жёсткого потолка."""
    return max(0, settings.daily_cap - answered_today_count(db, user))


# ---------------------------------------------------------------- weekly leaderboard + pushes (механика 2.2/2.3)
_WEEK = timedelta(days=7)


def _weekly_since() -> datetime:
    return datetime.now() - _WEEK


def weekly_leaderboard(db: Session, topic: str | None, limit: int):
    """Топ за последние 7 дней по числу правильных ответов (скользящее окно)."""
    conds = [Answer.answered_at >= _weekly_since()]
    if topic:
        conds.append(Answer.topic == topic)
    return (
        db.execute(
            select(
                Answer.user_tg_id,
                User.username,
                User.active_badge,
                func.count().label("total"),
                func.sum(case((Answer.is_correct, 1), else_=0)).label("correct"),
            )
            .join(User, User.tg_id == Answer.user_tg_id)
            .where(*conds)
            .group_by(Answer.user_tg_id, User.username, User.active_badge)
            .order_by(desc(func.sum(case((Answer.is_correct, 1), else_=0))))
            .limit(limit)
        )
        .all()
    )


def weekly_user_rank(db: Session, tg_id: int, topic: str | None) -> tuple[int | None, int, int]:
    """Ранг пользователя в недельном топе + его верные/всего за неделю."""
    conds = [Answer.answered_at >= _weekly_since(), Answer.user_tg_id == tg_id]
    if topic:
        conds.append(Answer.topic == topic)
    row = db.execute(
        select(
            func.count().label("total"),
            func.sum(case((Answer.is_correct, 1), else_=0)).label("correct"),
        ).where(*conds)
    ).one()
    correct = int(row.correct or 0)
    total = int(row.total or 0)
    if correct == 0:
        return None, correct, total
    # сколько пользователей с БОЛЬШИМ числом верных за неделю → ранг = above+1
    sub = (
        select(
            Answer.user_tg_id,
            func.sum(case((Answer.is_correct, 1), else_=0)).label("c"),
        )
        .where(Answer.answered_at >= _weekly_since())
        .group_by(Answer.user_tg_id)
    )
    if topic:
        sub = sub.where(Answer.topic == topic)
    sub = sub.subquery()
    above = db.execute(select(func.count()).select_from(sub).where(sub.c.c > correct)).scalar_one()
    return int(above) + 1, correct, total


async def send_telegram_message(tg_id: int, text: str) -> bool:
    """Отправить сообщение пользователю от имени бота (нужен TG_BOT_TOKEN)."""
    if not settings.tg_bot_token:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{settings.tg_bot_token}/sendMessage",
                json={"chat_id": tg_id, "text": text, "parse_mode": "HTML"},
            )
            return bool(r.json().get("ok"))
    except Exception:
        return False


async def run_competition_push(db: Session) -> int:
    """Пересчёт недельного топа + пуш «тебя обошли» для топ-N (макс 1/день).

    Без токена бота — только обновляет last_rank (чтобы detection заработал
    после подключения бота). Возвращает число отправленных пушей.
    """
    if not settings.competition_push:
        return 0
    rows = weekly_leaderboard(db, None, settings.push_top_n)
    today = date.today()
    sent = 0
    for rank, r in enumerate(rows, start=1):
        u = db.get(User, r.user_tg_id)
        if u is None:
            continue
        overtaken = u.last_rank is not None and rank > u.last_rank
        can_push_today = u.last_push_at is None or u.last_push_at < today
        if overtaken and can_push_today and rank <= settings.push_top_n:
            ok = await send_telegram_message(
                u.tg_id,
                f"⚡ Ты опустился на <b>{rank}</b> место в недельном топе QuizAIr. "
                f"Отыграй, чтобы вернуть позицию!",
            )
            if ok:
                u.last_push_at = today
                sent += 1
        u.last_rank = rank
    db.commit()
    return sent


# ---------------------------------------------------------------- answer
def pick_question(
    db: Session, topic: str, user_tg_id: int, level: str = "easy"
) -> Question | None:
    """Случайный активный вопрос по теме и уровню сложности пользователя.

    Исключает ВСЕ вопросы, на которые пользователь уже отвечал (верно или нет),
    чтобы они не повторялись. Фолбэк по сложности: уровень → medium → любой.
    Возвращает None, если все вопросы темы уже пройдены.
    """
    answered = (
        select(Answer.question_id)
        .where(Answer.user_tg_id == user_tg_id)
        .scalar_subquery()
    )

    def _pick(*conds) -> Question | None:
        return (
            db.execute(
                select(Question)
                .where(
                    Question.topic == topic,
                    Question.active.is_(True),
                    Question.id.notin_(answered),
                    *conds,
                )
                .order_by(func.random())
                .limit(1)
            )
            .scalars()
            .first()
        )

    q = _pick(Question.difficulty == level)
    if q is None and level != "medium":
        q = _pick(Question.difficulty == "medium")
    if q is None:
        q = _pick()  # любой уровень, но всё ещё без уже отвеченных
    return q


def total_left(user: User) -> int:
    """Сколько всего попыток доступно прямо сейчас."""
    return user.daily_left + user.bonus_left


def process_answer(db: Session, user: User, question: Question, answer: str) -> dict[str, Any]:
    """Сверяет ответ, списывает попытку, обновляет статистику. Возвращает детали."""
    bump_streak(db, user)  # стрик капает за реальный ответ, не за открытие
    correct = answer == question.correct_answer
    points = settings.correct_score if correct else 0

    # 1) списываем одну попытку: сначала возобновляемую дневную (она сгорает),
    #    затем — только когда дневная иссякла — купленные/бонусные слоты
    if user.daily_left > 0:
        user.daily_left -= 1
    elif user.bonus_left > 0:
        user.bonus_left -= 1

    # 2) записываем ответ
    db.add(
        Answer(
            user_tg_id=user.tg_id,
            question_id=question.id,
            topic=question.topic,
            is_correct=correct,
        )
    )
    db.flush()  # чтобы новый ответ учитывался в окне пересчёта уровня

    # 2.1) пересчёт уровня сложности (механика 1)
    old_level = user.skill_level
    recalc_skill_level(db, user)
    level_up = LEVEL_ORDER[user.skill_level] > LEVEL_ORDER[old_level]

    # 3) обновляем агрегаты по теме (аналог прод-триггера, но в Python)
    stat = db.get(UserTopicStat, (user.tg_id, question.topic))
    if stat is None:
        stat = UserTopicStat(
            user_tg_id=user.tg_id, topic=question.topic, score=0, correct=0, total=0
        )
        db.add(stat)
    stat.score += points
    stat.correct += 1 if correct else 0
    stat.total += 1
    stat.updated_at = datetime.now(timezone.utc)

    # 4) общий счёт + счётчик верных ответов
    milestone_bonus = 0
    if correct:
        user.total_score += points
        user.correct_total += 1
        # ТЗ v1.1: каждые 10 правильных → +1 вопрос (накапливается до bonus_cap)
        if user.correct_total % 10 == 0 and user.bonus_left < settings.bonus_cap:
            user.bonus_left += 1
            milestone_bonus = 1

    db.flush()
    # 5) значки — после того, как статистика зафлашена
    new_badges = award_new_badges(db, user)
    # 6) возможно, этот ответ — 5-й у чьего-то реферала → наградить пригласившего
    maybe_reward_referrer(db, user)

    db.commit()
    db.refresh(user)
    return {
        "correct": correct,
        "correct_answer": question.correct_answer,
        "explanation": question.explanation_cached,
        "score_awarded": points,
        "daily_left": user.daily_left,
        "bonus_left": user.bonus_left,
        "streak": user.streak,
        "skill_level": user.skill_level,
        "level_up": level_up,
        "new_badges": new_badges,
        "active_badge": user.active_badge,
        "milestone_bonus": milestone_bonus,
        "correct_total": user.correct_total,
    }


def claim_task(db: Session, user: User, partner: Partner) -> User:
    """Начисляет бонусные слоты за выполнение задания (подписку).

    Бонусные слоты НЕ сгорают при дневном сбросе — только daily_left.
    Одна конверсия на партнёра на пользователя (защита от фарма).
    """
    already = db.execute(
        select(Conversion).where(
            Conversion.user_tg_id == user.tg_id,
            Conversion.partner_id == partner.id,
        )
    ).scalar_one_or_none()
    if already is not None:
        raise AlreadyClaimedError(partner.id)

    user.bonus_left = min(settings.bonus_cap, user.bonus_left + partner.reward_quizzes)
    db.add(
        Conversion(
            user_tg_id=user.tg_id,
            partner_id=partner.id,
            reward_given=partner.reward_quizzes,
        )
    )
    db.commit()
    db.refresh(user)
    return user


class AlreadyClaimedError(Exception):
    def __init__(self, partner_id: int) -> None:
        self.partner_id = partner_id
        super().__init__(f"task {partner_id} already claimed")


# ---------------------------------------------------------------- referrals (механика 3)
def record_referral(db: Session, user: User) -> None:
    """При создании юзера с referred_by — фиксируем реферальную связь (одну, первого реферера)."""
    rid = user.referred_by
    if not rid or rid == user.tg_id:
        return
    exists = db.execute(
        select(Referral).where(Referral.referred_tg_id == user.tg_id)
    ).scalar_one_or_none()
    if exists is not None:
        return  # уже чей-то реферал — первый реферер приоритетен
    if db.get(User, rid) is None:
        return  # реферер не найден
    db.add(
        Referral(
            referrer_tg_id=rid,
            referred_tg_id=user.tg_id,
            reward_quizzes=settings.referral_reward,
            rewarded=False,
        )
    )
    db.commit()


def maybe_reward_referrer(db: Session, user: User) -> bool:
    """Когда приглашённый набирает 5+ ответов — начисляем пригласившему +3 (один раз).

    Возвращает True, если награда была выдана этим вызовом.
    """
    refl = db.execute(
        select(Referral).where(
            Referral.referred_tg_id == user.tg_id, Referral.rewarded.is_(False)
        )
    ).scalar_one_or_none()
    if refl is None:
        return False
    answered = db.execute(
        select(func.count())
        .select_from(Answer)
        .where(Answer.user_tg_id == user.tg_id)
    ).scalar_one()
    if answered < settings.referral_threshold:
        return False
    referrer = db.get(User, refl.referrer_tg_id)
    if referrer is None:
        return False
    referrer.bonus_left = min(settings.bonus_cap, referrer.bonus_left + refl.reward_quizzes)
    refl.rewarded = True
    db.commit()
    return True
