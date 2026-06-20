from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------- topics
class TopicOut(BaseModel):
    slug: str
    title: str
    emoji: str | None = None
    position: int


# ---------------------------------------------------------------- users
class UserCreate(BaseModel):
    tg_id: int
    username: str | None = None
    first_name: str | None = None
    photo_url: str | None = None
    referred_by: int | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tg_id: int
    username: str | None = None
    first_name: str | None = None
    photo_url: str | None = None
    streak: int
    longest_streak: int
    daily_left: int
    bonus_left: int
    daily_base: int
    total_score: int
    skill_level: Literal["easy", "medium", "hard"] = "easy"
    correct_total: int = 0
    active_badge: str | None = None


# ---------------------------------------------------------------- quiz
class QuestionOut(BaseModel):
    """Вопрос без правильного ответа — клиент его не видит."""

    id: int
    topic: str
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


class AnswerRequest(BaseModel):
    tg_id: int
    question_id: int
    answer: Literal["a", "b", "c", "d"]


class AnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str | None = None
    score_awarded: int
    daily_left: int
    bonus_left: int
    streak: int
    skill_level: Literal["easy", "medium", "hard"] = "easy"
    level_up: bool = False  # уровень повысился этим ответом
    new_badges: list[str] = []
    active_badge: str | None = None
    milestone_bonus: int = 0      # +1, если этот ответ был каждым 10-м верным
    correct_total: int = 0
    limit_reached: bool = False


class QuestionLimitResponse(BaseModel):
    """Вопросы закончились — нужен оффер партнёра."""

    limit_reached: Literal[True] = True
    daily_left: int
    bonus_left: int
    message: str = "Дневной лимит вопросов исчерпан. Подпишись на канал, чтобы получить ещё."


# ---------------------------------------------------------------- tasks
class TaskOut(BaseModel):
    """Задание: подписка на канал за бонусные слоты квизов."""

    id: int
    channel_username: str
    topic: str | None = None
    reward_quizzes: int
    cpa_rate: float
    claimed: bool = False


class ClaimResult(BaseModel):
    daily_left: int
    bonus_left: int
    reward_given: int


# ---------------------------------------------------------------- leaderboard
class LeaderboardEntry(BaseModel):
    tg_id: int
    username: str | None = None
    score: int
    correct: int
    total: int
    active_badge: str | None = None
    rank: int | None = None


# ---------------------------------------------------------------- badges
class BadgeDef(BaseModel):
    """Описание значка из реестра + флаг, получен ли он пользователем."""

    key: str
    emoji: str
    title: str
    desc: str
    earned: bool = False


class ActiveBadgeRequest(BaseModel):
    badge_key: str | None = None


# ---------------------------------------------------------------- referral (механика 3)
class ReferralInfo(BaseModel):
    ref_link: str
    bot_username: str
    referrals_total: int
    referrals_active: int
