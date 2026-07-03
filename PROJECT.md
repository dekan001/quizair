# QuizAIr — Telegram Mini App (квиз)

Короткие квизы по 10 темам (ИИ, Крипто, Психология, Футбол, Наука, История, Кино, Музыка, Игры, География) внутри Telegram.
Геймификация: уровни сложности, значки, стрики, лидерборды, рефералы, CPA-задания.

**Обновлено:** 2026-07-03

---

## Ключевые координаты

| Что | Значение |
|-----|----------|
| Бот | **@QuizAIr_bot** |
| Прод (Render) | `https://quizair.onrender.com` |
| GitHub | `https://github.com/dekan001/quizair` (ветка `main`) |
| Render-сервисы | web `quizair` + Postgres `quizair-db` (Blueprint из `render.yaml`) |
| Локальный путь | `E:\AI\miniAPP` |

---

## Стек и структура

- **Backend:** Python, FastAPI, SQLAlchemy 2.0. Dev — SQLite (`backend/quiz.db`), prod — Postgres (Render).
- **Frontend:** React 19 + TypeScript + Vite + Tailwind. Роутинг — HashRouter. Telegram WebApp SDK.
- **Один origin:** FastAPI отдаёт и API, и собранный фронт (`frontend/dist`) — нужно для Telegram (Mini App + API на одном HTTPS). `frontend/dist` **коммитится** (на Render нет npm для сборки).

```
miniAPP/
├─ backend/app/
│  ├─ main.py         # FastAPI, lifespan (init_db+seed), CORS, раздача frontend/dist, фоновый цикл пушей
│  ├─ config.py       # настройки (env): DATABASE_URL, daily_cap, bonus_cap, bot_username, токен и т.д.
│  ├─ database.py     # engine; нормализация postgres:// -> postgresql+psycopg://
│  ├─ models.py       # таблицы: users, questions, answers, user_topic_stats, badges, partners,
│  │                  #          conversions, referrals, streak_log, topics
│  ├─ schemas.py      # Pydantic-схемы (UserOut, AnswerResponse, LeaderboardEntry, ReferralInfo...)
│  ├─ services.py     # ВСЯ бизнес-логика: лимиты, стрик, уровень, значки, недельный топ, рефералы
│  ├─ seed.py         # create_all + dev-миграции SQLite + сид тем/партнёров/вопросов (диалект-aware)
│  └─ routers/        # users.py, topics.py, tasks.py, badges.py, quiz.py
├─ frontend/
│  ├─ src/screens/    # Home, Quiz, Limit, Tasks, Share, Profile, Leaderboard
│  ├─ src/components/ # RingProgress, ProgressBar, icons
│  ├─ src/lib/        # api.ts, game.ts, telegram.ts, theme.ts
│  └─ dist/           # СОБРАННЫЙ фронт (коммитится, раздаётся бэкендом)
├─ content/questions/ # 10 тем × 1000 вопросов (10 000 всего), .json на тему
├─ scripts/           # validate_questions.py, seed_questions.py (Supabase), shuffle_options.py, tag_difficulty.py
├─ supabase/migrations/ # 0001_init, 0002_topics_seed, 0003_mechanics_v1_1 (для Supabase; на Render не нужны — create_all)
├─ bot/               # bot.py (aiogram) — отдельный бот для deep-link /start (сейчас НЕ задеплоен)
├─ render.yaml        # Render Blueprint (web + Postgres, авто-связка DATABASE_URL)
├─ serve_telegram.py  # локальный запуск: бэкенд + туннель localhost.run + авто-настройка кнопки бота
└─ start-telegram.bat # обёртка над serve_telegram.py (сборка фронта + запуск)
```

---

## Игровые механики

**Лимиты вопросов:**
- Дневная база `daily_base = 10` + бонус за стрик: +2 при стрике ≥3 дней, +5 при ≥7 (cap стрика 7). Сгорает за день.
- `bonus_left` — бонусные слоты (за подписки/рефералов/каждые 10 верных), НЕ сгорают, потолок `bonus_cap = 50`.
- Жёсткий дневной потолок ответов `daily_cap = 50` (защита CPA).
- Каждые 10 правильных ответов → +1 бонусный вопрос (`correct_total % 10`).

**AI-персонализация сложности (ТЗ v1.1):**
- `skill_level` ∈ easy/medium/hard. Первые 20 ответов — калибровка (easy). Дальше пересчёт каждые 10 ответов по последним 20: <50%→easy, 50–79%→medium, ≥80%→hard.
- Вопросы фильтруются по уровню (`questions.difficulty`), фолбэк: уровень → medium → любой. Контент размечен ~32/40/28% (easy/medium/hard) на тему.

**Без повторов:** `pick_question` исключает ВСЕ уже отвеченные вопросы; когда тема пройдена — «Ты ответил на все вопросы темы». Подтверждено интеграционным тестом (все вопросы темы выдаются ровно по одному разу). NB: на бесплатном Render Postgres пересоздаётся ~раз в 30 дней — прогресс (и «пройденность») обнуляется.

**Значки (16):** on_fire, sniper, speed, 10 тематических (ai_guru, crypto_master, psych_master, football_expert, science_master, history_buff, movie_expert, music_guru, gamer, geo_master), ambassador, legend, champion. Начисляются после ответа; `active_badge` пользователь выбирает в профиле, он виден в лидерборде.

**Контент и анти-giveaway:** 10 000 вопросов (10×1000) сгенерированы конвейером (генерация по подтемам → фактчек-аудит каждого блока → merge). Правила: 4 варианта одного типа и сопоставимой длины, без скобок/уточнений только у правильного, без «все вышеперечисленное», буквы correct_answer сбалансированы ~25/25/25/25. Контроль — `scripts/validate_questions.py`.

**Сид вопросов:** bulk-upsert чанками по 500 + чексумма контента в `seed_meta` (повторный старт с неизменным контентом не перезаливает БД); вопросы, убранные из файлов, деактивируются.

**Лидерборд:** скользящее окно 7 дней по числу верных ответов. Вкладки: Общий + по темам. Своя позиция дозаписывается, если не в топе. Показывается active_badge.

**Задания (CPA):** партнёрские каналы (`seed.py PARTNERS`), claim → +5 бонусных слотов (одна конверсия на пару user+partner). Выполненные уходят вниз списка. Реальная проверка подписки — через `tg.py` (нужен TG_BOT_TOKEN), без токена в dev = всегда успех.

**Рефералы:** ссылка `https://t.me/QuizAIr_bot?startapp=ref_<tg_id>`. Фронт читает `start_param` → `referred_by` в createUser. Пригласившему +3 вопроса, когда приглашённый ответит на 5+. Один реферер на пользователя, фиксируется при первом входе.

---

## Конфиг / переменные окружения (`backend/app/config.py`)

- `DATABASE_URL` — на Render связывается автоматически (Postgres). Dev по умолчанию SQLite.
- `TG_BOT_TOKEN` — опционально; включает проверку подписок на каналы и пуши. Без него мини-апп работает.
- `bot_username = "QuizAIr_bot"`, `daily_cap = 50`, `bonus_cap = 50`, `daily_base_quizzes = 10`, `correct_score = 10`, `referral_reward = 3`, `referral_threshold = 5`.
- Локально токен кладётся в `miniAPP/.env` (gitignore): `TG_BOT_TOKEN=...`.

---

## Деплой и обновление (Render)

Render привязан к GitHub и **авто-деплоит** при пуше в `main`.

**Цикл обновления:**
1. Правка кода. Если меняли фронт — `cd frontend && npm run build` (Render раздаёт собранный `dist`, не собирает сам).
2. `git add -A && git commit -m "..." && git push origin main`.
3. Render сам пересобирает (~2–5 мин). Обновить апп в боте.

> Прямой пуш из Claude Code работает (GitHub-доступ закеширован в Windows Credential Manager после первого `git push`). Отдельная интеграция не нужна.

**Привязка к боту (один раз):** @BotFather → @QuizAIr_bot →
- **Menu Button** → URL `https://quizair.onrender.com` (открыть кнопкой меню).
- **Configure Mini App** → тот же URL (нужно, чтобы `?startapp=ref_...` открывал апп с параметром реферала).

---

## Запуск локально

**Backend:** `cd backend && .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000` (без `--reload` — стабильнее).
**Frontend (dev, с HMR):** `cd frontend && npm run dev` → `http://127.0.0.1:5173` (читает `VITE_API_URL`, по умолчанию `http://127.0.0.1:8000`).
**Прод-сборка фронта:** `npm run build` (использует `.env.production` → API относительный, same-origin).

**Локальный запуск «как в Telegram» (туннель):** `start-telegram.bat` — поднимает бэкенд (:8080), туннель localhost.run (с SSH-ключом `~/.ssh/id_ed25519`), сам прописывает кнопку меню боту из `.env`. Минус бесплатных туннелей: адрес меняется/рвётся — поэтому для постоянного теста используем Render.

---

## Известные проблемы / TODO

- **БЕЗОПАСНОСТЬ (до публичного запуска!):** бэкенд доверяет `tg_id` из запроса БЕЗ проверки подписи Telegram `initData`. Любой может подделать чужой аккаунт (накрутка очков/наград/топа). Нужно валидировать HMAC `initData` ботовым токеном и брать tg_id оттуда.
- **CORS:** сейчас `allow_origins=["*"]` (dev). В прод ограничить доменом.
- **Render free:** сервис засыпает после 15 мин простоя (первое открытие ~30–60с); бесплатный Postgres живёт ~30 дней, потом пересоздать (вопросы зальются сами, прогресс игроков обнулится). Для постоянной БД → Supabase (миграции готовы в `supabase/migrations`).
- **Значки champion/тематические** оцениваются на каждом ответе (лишние запросы) — при росте вынести в крон.
- **bot/bot.py** (aiogram deep-link `/start ref_`) пока не задеплоен; рефералы работают через `?startapp=` + фронт, бот для этого не обязателен.

---

## Хронология работ

1. **Ревью** исходного мини-аппа (FastAPI + React квиз), проверка сборки/типов/логики.
2. **Редизайн UI:** тёмная тема, aurora-фон, glass-карточки, плавающая навигация, анимации, круговой прогресс.
3. **Общий лидерборд** (в дополнение к темам) — позже переведён на 7-дневное окно.
4. **ТЗ v1.1 — три механики** (часть сделал другой ИИ, затем ревью+фиксы): AI-сложность, значки, рефералы, бонус «каждые 10 верных», потолок. Починено: прод-миграция Supabase 0003, `psycopg` в requirements, диалект-aware сид, `python-dotenv` в bot, удалён неиспользуемый импорт.
5. **UI-доводка:** формулировка лимита (не «исчерпан», когда есть бонусы); кольцо лимита (двойное → одинарное «X из 50», cap 50); разделы на главной — строками; экран ответа заменяет варианты (без скролла) + показ правильного ответа; прогресс бонуса убран в профиль; экран «Поделиться» = чистая реф-ссылка.
6. **Деплой:** локальные туннели не подошли (cloudflared — блок порта 7844; pinggy/ngrok/serveo — заглушка ломает Mini App; localhost.run — нестабилен). Выбрали **Render (облако)**.
7. **Render:** совместимость с Postgres (нормализация URL, psycopg, диалект-aware сид), коммит `frontend/dist`, `render.yaml` Blueprint. Успешно задеплоено на `https://quizair.onrender.com`.
8. **Рефералы (фикс):** настоящий бот @QuizAIr_bot, deep-link `?startapp=ref_<id>`, фронт ловит `start_param` и передаёт `referred_by`.
