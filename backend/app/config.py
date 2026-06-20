from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения.

    DATABASE_URL по умолчанию — SQLite (временная БД для локального теста).
    Для прод (Supabase) переопределяется через .env, напр.:
        DATABASE_URL=postgresql+psycopg://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres
    """

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # БД
    database_url: str = "sqlite:///./quiz.db"

    # игровые параметры (из ТЗ)
    daily_base_quizzes: int = 10       # базовых бесплатных квизов в день
    streak_bonus_3: int = 2            # +2 при стрике от 3 дней
    streak_bonus_7: int = 5            # +5 при стрике от 7 дней
    streak_cap: int = 7                # максимум дней в стрике
    correct_score: int = 10            # очков за верный ответ
    daily_cap: int = 50                # жёсткий потолок ответов в день (база + бонусы)
    bonus_cap: int = 50                # максимум накопленных бонусных слотов
    bot_username: str = "agent_era_ai"  # для реферальных ссылок t.me/<bot>?start=ref_ID
    referral_reward: int = 3           # бонусных слотов пригласившему, когда реферал наберёт 5+ ответов
    referral_threshold: int = 5        # сколько ответов должен дать реферал, чтобы засчитаться

    # Telegram bot (Stage 4): токен бота, URL мини-аппа, проверка подписок
    tg_bot_token: str = ""             # от @BotFather; пусто = проверка подписок выключена (dev)
    webapp_url: str = "https://t.me/agent_era_ai/app"  # куда открывать Mini App
    verify_subscriptions: bool = True  # проверять реальную подписку перед начислением за «Задание»
    # конкурентные пуши (ТЗ v1.1, 2.3)
    competition_push: bool = True     # включить пуш «тебя обошли в топе»
    push_top_n: int = 50              # только для топ-N (ниже — демотивирует, не пушим)
    push_interval_hours: int = 24     # как часто запускать пересчёт/пуши


settings = Settings()
