"""Загрузка 250 вопросов из content/questions/*.json в таблицу public.questions.

Идемпотентно: использует upsert по (topic, text), поэтому при повторном запуске
существующие строки обновляются (id сохраняется, история ответов не теряется),
а новые добавляются.

Требует:  pip install supabase
Переменные окружения (из .env или среды):
    SUPABASE_URL              — Project URL (https://xxxx.supabase.co)
    SUPABASE_SERVICE_ROLE_KEY — service_role key (обходит RLS)

Запуск:
    python scripts/seed_questions.py            # все темы
    python scripts/seed_questions.py ai crypto  # только указанные темы
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "content" / "questions"
ENV_FILE = ROOT / ".env"


def load_env(path: Path) -> None:
    """Минимальный загрузчик .env, чтобы не тянуть python-dotenv ради одного скрипта."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


def build_rows(topic: str, data: list[dict]) -> list[dict]:
    rows = []
    for q in data:
        rows.append(
            {
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
        )
    return rows


def main(argv: list[str]) -> int:
    load_env(ENV_FILE)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ОШИБКА: не заданы SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY.")
        print("Создай .env (см. .env.example) или экспортируй переменные окружения.")
        return 2

    try:
        from supabase import create_client
    except ImportError:
        print("Не установлен supabase. Выполни:  pip install supabase")
        return 2

    sb = create_client(url, key)

    topics = argv if argv else [p.stem for p in sorted(QUESTIONS_DIR.glob("*.json"))]
    total_upserted = 0
    for topic in topics:
        path = QUESTIONS_DIR / f"{topic}.json"
        if not path.exists():
            print(f"[SKIP] {topic}: файл не найден {path}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = build_rows(topic, data)

        # upsert батчами по 50 — Supabase ограничивает размер тела запроса
        for i in range(0, len(rows), 50):
            batch = rows[i : i + 50]
            (sb.table("questions")
               .upsert(batch, on_conflict="topic,text")
               .execute())
        total_upserted += len(rows)
        print(f"[ OK ] {topic:<11} — upsert {len(rows)} вопросов")

    print("-" * 50)
    print(f"Готово. Всего upsert: {total_upserted}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
