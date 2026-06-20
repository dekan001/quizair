---
title: QuizAIr
emoji: 🧠
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# QuizAIr — Telegram Mini App

Квиз-мини-апп: FastAPI (бэкенд + раздача собранного фронтенда) и React/Vite (фронт).

- **Один контейнер** отдаёт и API, и UI (см. `Dockerfile`).
- БД по умолчанию — SQLite в `/tmp` (для постоянной задай `DATABASE_URL` в секретах хостинга).
- Локальный запуск для Telegram: `start-telegram.bat`.

Подробности механик — в дополнении к ТЗ (геймификация, стрик, значки, рефералы).
