# Контент квизов

10 000 вопросов: 10 тем × 1000 штук. Один файл на тему в `questions/`.

## Формат вопроса (соответствует таблице `questions`)

```json
{
  "text": "Текст вопроса",
  "option_a": "Вариант A",
  "option_b": "Вариант B",
  "option_c": "Вариант C",
  "option_d": "Вариант D",
  "correct_answer": "a",
  "explanation": "Почему ответ верный. 1-2 предложения, только факты.",
  "difficulty": "easy | medium | hard"
}
```

## Темы

| Файл                        | topic key    | CPA ориентир    |
|-----------------------------|--------------|-----------------|
| `questions/ai.json`         | `ai`         | $0.50–1.00/sub  |
| `questions/crypto.json`     | `crypto`     | $1–3/sub        |
| `questions/psychology.json` | `psychology` | $0.30–0.70/sub  |
| `questions/football.json`   | `football`   | $0.20–0.50/sub  |
| `questions/science.json`    | `science`    | $0.20–0.40/sub  |
| `questions/history.json`    | `history`    | $0.30–0.60/sub  |
| `questions/movies.json`     | `movies`     | $0.30–0.70/sub  |
| `questions/music.json`      | `music`      | $0.20–0.50/sub  |
| `questions/games.json`      | `games`      | $0.40–0.90/sub  |
| `questions/geography.json`  | `geography`  | $0.20–0.40/sub  |

## Принципы контента

- Уровень: смесь easy/medium/hard (~32/40/28%), помечен в `difficulty`.
- Интересные факты, не справочные даты ради дат.
- `correct_answer` — ровно одна буква из `a/b/c/d`, распределение по буквам ~25% каждая.
- `explanation` — заранее кэшируется в `explanation_cached`, LLM в рантайме не вызывается.

## Анти-giveaway (ничто не должно выдавать ответ)

- Все 4 варианта — одного типа и сопоставимой длины; правильный не самый длинный/подробный.
- Никаких скобок/уточнений только у правильного варианта.
- Запрещены «все вышеперечисленное», «оба варианта», «ни один из» и т.п.
- Дистракторы правдоподобны: реальные сущности той же категории.

## Валидация

```bash
python scripts/validate_questions.py
```

Проверяет: JSON-синтаксис, все поля, `correct_answer` ∈ {a,b,c,d}, 1000 вопросов на тему,
дубли текстов, анти-giveaway правила, распределение букв ответов.
