from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import SessionLocal
from .routers import badges, quiz, tasks, topics, users
from .seed import init_db, seed_partners, seed_questions, seed_topics
from .services import run_competition_push

logger = logging.getLogger("quizair")


async def _competition_loop() -> None:
    """Фоновый пересчёт недельного топа + конкурентные пуши (ТЗ v1.1, 2.3).

    Без TG_BOT_TOKEN — только обновляет last_rank (Detection заработает позже).
    """
    await asyncio.sleep(30)  # стартовая пауза, чтобы БД успела инициализироваться
    interval = max(1, settings.push_interval_hours) * 3600
    while True:
        db = SessionLocal()
        try:
            sent = await run_competition_push(db)
            if sent:
                logger.info("competition push: sent %d", sent)
        except Exception:  # фон не должен ронять приложение
            logger.exception("competition loop error")
        finally:
            db.close()
        await asyncio.sleep(interval)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # dev: создаём таблицы и заполняем БД при старте.
    # prod: таблицы создаются SQL-миграциями, сид вопросов — scripts/seed_questions.py.
    init_db()
    db = SessionLocal()
    try:
        seed_topics(db)
        seed_partners(db)
        seed_questions(db)
    finally:
        db.close()
    push_task = asyncio.create_task(_competition_loop())
    try:
        yield
    finally:
        push_task.cancel()


app = FastAPI(
    title="Quiz Mini App API",
    version="0.1.0",
    description="Бэкенд квиз-мини-аппа. Dev: SQLite. Prod: Supabase Postgres.",
    lifespan=lifespan,
)

# dev-CORS открыт; в prod ограничить доменом мини-аппа.
# allow_credentials=False — иначе wildcard-origin "*" невалиден по спецификации
# (куки/credential-режим не используется: авторизация по tg_id в теле запроса).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(topics.router)
app.include_router(tasks.router)
app.include_router(badges.router)
app.include_router(quiz.router)


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Раздача собранного фронтенда (frontend/dist), если он есть: тогда Mini App и API
# живут на одном HTTPS-адресе — это нужно для Telegram. Монтируется ПОСЛЕ API-роутов,
# поэтому /users, /question и т.д. имеют приоритет, а всё остальное отдаёт SPA.
_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="frontend")
