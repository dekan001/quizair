"""Валидация контента квизов.

Проверяет все файлы в content/questions/:
- валидный JSON
- нет дублирующих ключей в объектах
- ровно 7 обязательных полей на вопрос
- correct_answer ∈ {a, b, c, d}
- ровно 50 вопросов на тему
- корректные типы и непустые строки
- нет нетипичных символов (например, CJK артефактов)

Запуск:  python scripts/validate_questions.py
"""
from __future__ import annotations

import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUESTIONS_DIR = ROOT / "content" / "questions"
EXPECTED_COUNT = 50
REQUIRED_FIELDS = {
    "text",
    "option_a",
    "option_b",
    "option_c",
    "option_d",
    "correct_answer",
    "explanation",
}
OPTIONAL_FIELDS = {"difficulty"}  # уровень сложности: easy/medium/hard (ТЗ v1.1)
VALID_ANSWERS = {"a", "b", "c", "d"}
VALID_DIFFICULTY = {"easy", "medium", "hard"}
OPTION_FIELDS = ["option_a", "option_b", "option_c", "option_d"]

# Диапазоны Unicode, которых не должно быть в русском тексте вопросов
SUSPECT_RANGES = [
    (0x4E00, 0x9FFF),   # CJK Unified Ideographs
    (0x3040, 0x30FF),   # Japanese kana
    (0xAC00, 0xD7AF),   # Korean Hangul
]


class DupKeyError(ValueError):
    pass


def _pairs_hook(pairs):
    seen = set()
    obj = {}
    for key, value in pairs:
        if key in seen:
            raise DupKeyError(f"дублирующий ключ: {key!r}")
        seen.add(key)
        obj[key] = value
    return obj


def _has_suspect_chars(text: str) -> bool:
    for ch in text:
        cp = ord(ch)
        for lo, hi in SUSPECT_RANGES:
            if lo <= cp <= hi:
                return True
    return False


def validate_file(path: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_text(encoding="utf-8")

    try:
        data = json.loads(raw, object_pairs_hook=_pairs_hook)
    except DupKeyError as exc:
        errors.append(f"JSON: {exc}")
        return errors
    except json.JSONDecodeError as exc:
        errors.append(f"JSON невалиден: {exc}")
        return errors

    if not isinstance(data, list):
        errors.append("корень файла должен быть массивом вопросов")
        return errors

    if len(data) != EXPECTED_COUNT:
        errors.append(f"ожидалось {EXPECTED_COUNT} вопросов, найдено {len(data)}")

    for i, q in enumerate(data, start=1):
        prefix = f"вопрос #{i}: "
        if not isinstance(q, dict):
            errors.append(prefix + "не является объектом")
            continue

        missing = REQUIRED_FIELDS - set(q)
        extra = set(q) - REQUIRED_FIELDS - OPTIONAL_FIELDS
        if missing:
            errors.append(prefix + f"нет полей {sorted(missing)}")
        if extra:
            errors.append(prefix + f"лишние поля {sorted(extra)}")

        if "difficulty" in q and q["difficulty"] not in VALID_DIFFICULTY:
            errors.append(prefix + f"difficulty={q['difficulty']!r} (должно быть easy/medium/hard)")

        for field in REQUIRED_FIELDS:
            val = q.get(field)
            if not isinstance(val, str) or not val.strip():
                errors.append(prefix + f"поле {field!r} пустое или не строка")

        answer = q.get("correct_answer")
        if answer not in VALID_ANSWERS:
            errors.append(prefix + f"correct_answer={answer!r} (должно быть a/b/c/d)")

        # проверка: текст вопроса не совпадает с вариантами-пустышками
        options = [q.get(f, "") for f in OPTION_FIELDS]
        if len(set(options)) != len(options):
            errors.append(prefix + "есть одинаковые варианты ответа")

        # подозрительные символы (CJK и т.п. артефакты генерации)
        for field in REQUIRED_FIELDS:
            val = q.get(field, "")
            if isinstance(val, str) and _has_suspect_chars(val):
                errors.append(prefix + f"поле {field!r} содержит подозрительные символы")
                break

    # дубли текста внутри темы — нарушили бы unique (topic, text) при upsert
    texts = [q.get("text", "") for q in data if isinstance(q, dict)]
    seen_dup: set[str] = set()
    dup_texts = []
    for t in texts:
        if t in seen_dup and t not in dup_texts:
            dup_texts.append(t)
        seen_dup.add(t)
    if dup_texts:
        errors.append(f"дублирующие тексты вопросов: {len(dup_texts)} шт., например: {dup_texts[0][:60]!r}")

    return errors


def main() -> int:
    if not QUESTIONS_DIR.exists():
        print(f"Каталог не найден: {QUESTIONS_DIR}")
        return 2

    files = sorted(QUESTIONS_DIR.glob("*.json"))
    if not files:
        print("JSON-файлы не найдены")
        return 2

    total_errors = 0
    total_questions = 0
    for path in files:
        topic = path.stem
        errors = validate_file(path)
        # считаем вопросы даже при ошибках, если массив распарсился
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            total_questions += len(data) if isinstance(data, list) else 0
        except Exception:
            pass

        if errors:
            total_errors += len(errors)
            print(f"[FAIL] {topic} — {len(errors)} проблем:")
            for e in errors:
                print(f"   - {e}")
        else:
            print(f"[ OK ] {topic} — {EXPECTED_COUNT} вопросов, всё чисто")

    print("-" * 50)
    status = "УСПЕХ" if total_errors == 0 else f"ОШИБОК: {total_errors}"
    print(f"Проверено файлов: {len(files)} | Вопросов: {total_questions}/{len(files) * EXPECTED_COUNT} | {status}")
    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
