from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings


def _normalize_db_url(url: str) -> str:
    """Приводит URL Postgres к виду, который понимает SQLAlchemy + драйвер psycopg.

    Render/Heroku отдают DATABASE_URL как postgres://... — добавляем драйвер psycopg.
    SQLite оставляем как есть.
    """
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DB_URL = _normalize_db_url(settings.database_url)
_is_sqlite = DB_URL.startswith("sqlite")

connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    DB_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
    pool_pre_ping=not _is_sqlite,  # для облачного Postgres: проверять «живость» соединения
)

# SQLite: включаем внешние ключи (по умолчанию отключены)
if _is_sqlite:

    @event.listens_for(engine, "connect")
    def _enable_sqlite_fk(dbapi_conn, _record):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator:
    """FastAPI-зависимость: сессия БД на запрос."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
