"""Раздаёт поле difficulty вопросам по темам (ТЗ v1.1, механика 1).

На каждую тему (по 50 вопросов): 16 easy + 20 medium + 14 hard
(пропорция как 80/100/70 в ТЗ, масштабированная под 50).

Назначение детерминированное по порядку в файле — повторный запуск стабилен.
Вопросы изначально написаны без учёта уровня, поэтому это грубая разметка,
чтобы механика адаптивной сложности функционировала. Для прод-сезонов вопросы
нужно генерировать с явным указанием уровня в промпте.

Запуск:  python scripts/tag_difficulty.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "content" / "questions"

# (порог индекса, уровень) — для 50 вопросов на тему
PLAN = [(16, "easy"), (36, "medium"), (50, "hard")]


def level_for(index: int) -> str:
    for limit, lvl in PLAN:
        if index < limit:
            return lvl
    return "hard"


def main() -> None:
    for path in sorted(DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for i, q in enumerate(data):
            q["difficulty"] = level_for(i)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        from collections import Counter

        c = Counter(q["difficulty"] for q in data)
        print(f"{path.name}: " + "  ".join(f"{k}={v}" for k, v in sorted(c.items())))


if __name__ == "__main__":
    main()
