# QuizAIr: один контейнер — FastAPI отдаёт API + собранный фронтенд.
# Подходит для Hugging Face Spaces (порт 7860), Koyeb, Railway, Fly и т.п.
FROM python:3.12-slim

WORKDIR /app

# 1) зависимости бэкенда (кэшируется отдельным слоем)
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 2) код, контент и собранный фронт (frontend/dist закоммичен в репо)
COPY backend/ backend/
COPY content/ content/
COPY frontend/dist/ frontend/dist/

# По умолчанию SQLite в /tmp (всегда доступен на запись; пересоздаётся при рестарте).
# Для постоянной БД задай DATABASE_URL в секретах хостинга (напр. Neon/Supabase Postgres).
ENV DATABASE_URL=sqlite:////tmp/quiz.db
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

EXPOSE 7860
CMD ["sh", "-c", "python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
