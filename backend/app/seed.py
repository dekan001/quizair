"""Инициализация и сид БД.

Создаёт таблицы (create_all) и заполняет:
  - 5 тем (topics) из ТЗ;
  - 250 вопросов из content/questions/*.json.

Идемпотентно: темы и вопросы upsert'ятся по ключу, повторный запуск безопасен.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy import inspect, select, text
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Partner, Question, Topic

CONTENT_DIR = Path(__file__).resolve().parents[2] / "content" / "questions"

TOPICS = [
    {"slug": "ai", "title": "ИИ", "emoji": "🤖", "cpa_low": 0.50, "cpa_high": 1.00, "position": 1},
    {"slug": "crypto", "title": "Крипто", "emoji": "₿", "cpa_low": 1.00, "cpa_high": 3.00, "position": 2},
    {"slug": "psychology", "title": "Психология", "emoji": "🧠", "cpa_low": 0.30, "cpa_high": 0.70, "position": 3},
    {"slug": "football", "title": "Футбол", "emoji": "⚽", "cpa_low": 0.20, "cpa_high": 0.50, "position": 4},
    {"slug": "science", "title": "Наука", "emoji": "🌍", "cpa_low": 0.20, "cpa_high": 0.40, "position": 5},
]

# Партнёрские каналы (офферы) для раздела «Задания».
# (channel_username, topic, reward_quizzes, cpa_rate)
PARTNERS = [
    ("@agent_era_ai", "ai", 5, 0.80),
    ("@ai_tools_daily", "ai", 5, 0.60),
    ("@crypto_signals_hub", "crypto", 5, 2.00),
    ("@defi_digest", "crypto", 5, 1.50),
    ("@mind_hacks", "psychology", 5, 0.50),
    ("@psy_facts", "psychology", 5, 0.40),
    ("@footy_flash", "football", 5, 0.35),
    ("@transfer_hub", "football", 5, 0.45),
    ("@science_bites", "science", 5, 0.30),
    ("@space_daily", "science", 5, 0.35),
]


def _migrate_users_quota() -> None:
    """dev-only авто-миграция SQLite: схемы раньше был quizzes_left,
    стал daily_left + bonus_left. Добавляем колонки и переносим остаток."""
    if not engine.dialect.name.startswith("sqlite"):
        return
    with engine.connect() as conn:
        try:
            cols = {c["name"] for c in inspect(conn).get_columns("users")}
        except Exception:
            return  # таблицы ещё нет — create_all создаст по новой модели
        if "quizzes_left" in cols and "daily_left" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN daily_left INTEGER NOT NULL DEFAULT 10"))
            conn.execute(text("ALTER TABLE users ADD COLUMN bonus_left INTEGER NOT NULL DEFAULT 0"))
            conn.execute(text("UPDATE users SET daily_left = quizzes_left"))
            # убираем старую NOT NULL-колонку, иначе новые INSERT'ы падают
            conn.execute(text("ALTER TABLE users DROP COLUMN quizzes_left"))
            conn.commit()


def _migrate_users_skill() -> None:
    """dev-only авто-миграция SQLite: добавляем поля персонализации сложности
    (ТЗ v1.1, механика 1) к существующей таблице users."""
    if not engine.dialect.name.startswith("sqlite"):
        return
    with engine.connect() as conn:
        try:
            cols = {c["name"] for c in inspect(conn).get_columns("users")}
        except Exception:
            return  # таблицы ещё нет — create_all создаст по новой модели
        if "skill_level" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN skill_level VARCHAR NOT NULL DEFAULT 'easy'"))
        if "answers_since_recalc" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN answers_since_recalc INTEGER NOT NULL DEFAULT 0"))
        if "correct_total" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN correct_total INTEGER NOT NULL DEFAULT 0"))
        if "active_badge" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN active_badge VARCHAR"))
        if "last_rank" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_rank INTEGER"))
        if "last_push_at" not in cols:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_push_at DATE"))
        conn.commit()


def init_db() -> None:
    """Создать все таблицы (dev). В прод применяются SQL-миграции."""
    Base.metadata.create_all(bind=engine)
    _migrate_users_quota()
    _migrate_users_skill()


def seed_topics(db: Session) -> int:
    count = 0
    for t in TOPICS:
        existing = db.get(Topic, t["slug"])
        if existing is None:
            db.add(Topic(**t))
            count += 1
        else:
            for k, v in t.items():
                setattr(existing, k, v)
            count += 1
    db.commit()
    return count


def seed_questions(db: Session) -> int:
    # upsert по (topic, text) — диалект-зависимый (SQLite dev / Postgres prod)
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as _insert
    else:
        from sqlalchemy.dialects.sqlite import insert as _insert

    total = 0
    for path in sorted(CONTENT_DIR.glob("*.json")):
        topic = path.stem
        data = json.loads(path.read_text(encoding="utf-8"))
        for q in data:
            row = {
                "topic": topic,
                "text": q["text"],
                "option_a": q["option_a"],
                "option_b": q["option_b"],
                "option_c": q["option_c"],
                "option_d": q["option_d"],
                "correct_answer": q["correct_answer"],
                "explanation_cached": q.get("explanation"),
                "difficulty": q.get("difficulty", "medium"),
                "active": True,
            }
            stmt = _insert(Question).values(**row)
            stmt = stmt.on_conflict_do_update(
                index_elements=["topic", "text"],
                set_={
                    "option_a": stmt.excluded.option_a,
                    "option_b": stmt.excluded.option_b,
                    "option_c": stmt.excluded.option_c,
                    "option_d": stmt.excluded.option_d,
                    "correct_answer": stmt.excluded.correct_answer,
                    "explanation_cached": stmt.excluded.explanation_cached,
                    "difficulty": stmt.excluded.difficulty,
                    "active": True,
                },
            )
            db.execute(stmt)
            total += 1
    db.commit()
    return total


def seed_partners(db: Session) -> int:
    inserted = 0
    for username, topic, reward, cpa in PARTNERS:
        exists = db.execute(
            select(Partner).where(Partner.channel_username == username)
        ).scalar_one_or_none()
        if exists is None:
            db.add(
                Partner(
                    channel_username=username,
                    topic=topic,
                    reward_quizzes=reward,
                    cpa_rate=cpa,
                    active=True,
                )
            )
            inserted += 1
    db.commit()
    return inserted


def run_seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        topics_n = seed_topics(db)
        partners_n = seed_partners(db)
        questions_n = seed_questions(db)
        print(f"[seed] topics: {topics_n} | partners: {partners_n} | questions upserted: {questions_n}")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(run_seed() or 0)
