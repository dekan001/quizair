# Контент квизов

250 вопросов: 5 тем × 50 штук. Один файл на тему в `questions/`.

## Формат вопроса (соответствует таблице `questions` в Supabase)

```json
{
  "text": "Текст вопроса",
  "option_a": "Вариант A",
  "option_b": "Вариант B",
  "option_c": "Вариант C",
  "option_d": "Вариант D",
  "correct_answer": "a",
  "explanation": "Почему ответ верный. 2-3 предложения, только факты."
}
```

## Темы

| Файл                | topic key   | CPA ориентир      |
|---------------------|-------------|-------------------|
| `questions/ai.json`       | `ai`         | $0.50–1.00/sub   |
| `questions/crypto.json`   | `crypto`     | $1–3/sub         |
| `questions/psychology.json` | `psychology` | $0.30–0.70/sub   |
| `questions/football.json` | `football`   | $0.20–0.50/sub   |
| `questions/science.json`  | `science`    | $0.20–0.40/sub   |

## Принципы контента

- Уровень: средний (не банальный, но и не академический).
- Интересные факты, не справочные даты ради дат.
- `correct_answer` — ровно одна буква из `a/b/c/d`.
- `explanation` — заранее кэшируется в `explanation_cached`, Claude не вызывается повторно.

## Валидация

```bash
python scripts/validate_questions.py
```

Проверяет: JSON-синтаксис, наличие всех 7 полей, `correct_answer` ∈ {a,b,c,d}, 50 вопросов на тему.
