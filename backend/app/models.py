from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Topic(Base):
    __tablename__ = "topics"

    slug: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    emoji: Mapped[str | None] = mapped_column(String, nullable=True)
    cpa_low: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    cpa_high: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)

    # streak
    streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_anchor_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # дневной лимит: renewable (сгорает на следующий день) + купленные/бонусные (персистентные)
    daily_base: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    daily_left: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    bonus_left: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    quizzes_reset_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # очки
    total_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # AI-персонализация сложности (ТЗ v1.1, механика 1)
    skill_level: Mapped[str] = mapped_column(String, default="easy", nullable=False)
    answers_since_recalc: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # ТЗ v1.1: всего правильных ответов (значок «Легенда» + бонус «каждые 10 → +1»)
    correct_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    # активный значок в лидерборде (пользователь выбирает сам)
    active_badge: Mapped[str | None] = mapped_column(String, nullable=True)
    # конкурентные пуши: прошлый ранг и дата последнего пуша (ТЗ v1.1, 2.3)
    last_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_push_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # рефералка
    referred_by: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.tg_id"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (
        CheckConstraint("correct_answer in ('a','b','c','d')", name="questions_correct_answer_check"),
        CheckConstraint("difficulty in ('easy','medium','hard')", name="questions_difficulty_check"),
        UniqueConstraint("topic", "text", name="questions_topic_text_uidx"),
    )

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(ForeignKey("topics.slug"), nullable=False)
    text: Mapped[str] = mapped_column(String, nullable=False)
    option_a: Mapped[str] = mapped_column(String, nullable=False)
    option_b: Mapped[str] = mapped_column(String, nullable=False)
    option_c: Mapped[str] = mapped_column(String, nullable=False)
    option_d: Mapped[str] = mapped_column(String, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String(1), nullable=False)
    explanation_cached: Mapped[str | None] = mapped_column(String, nullable=True)
    # уровень сложности (ТЗ v1.1, механика 1): easy / medium / hard
    difficulty: Mapped[str] = mapped_column(String, default="medium", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str] = mapped_column(ForeignKey("topics.slug"), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    # локальное наивное время — чтобы оконные запросы (скорость, дневной потолок)
    # считались одинаково с порогами на стороне Python
    answered_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)


class UserTopicStat(Base):
    __tablename__ = "user_topic_stats"

    user_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), primary_key=True
    )
    topic: Mapped[str] = mapped_column(ForeignKey("topics.slug"), primary_key=True)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Partner(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    channel_username: Mapped[str] = mapped_column(String, nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    topic: Mapped[str | None] = mapped_column(ForeignKey("topics.slug"), nullable=True)
    reward_quizzes: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    cpa_rate: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Conversion(Base):
    __tablename__ = "conversions"
    __table_args__ = (UniqueConstraint("user_tg_id", "partner_id", name="conversions_user_partner_uidx"),)

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False
    )
    partner_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("partners.id", ondelete="RESTRICT"), nullable=False
    )
    reward_given: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    converted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    referrer_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False
    )
    referred_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), nullable=False, unique=True
    )
    reward_quizzes: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    rewarded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class StreakLog(Base):
    __tablename__ = "streak_log"

    user_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), primary_key=True
    )
    day_date: Mapped[date] = mapped_column(Date, primary_key=True)
    kept: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Badge(Base):
    """Полученные пользователем значки (ТЗ v1.1, механика 2)."""

    __tablename__ = "badges"

    user_tg_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.tg_id", ondelete="CASCADE"), primary_key=True
    )
    badge_key: Mapped[str] = mapped_column(String, primary_key=True)
    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
