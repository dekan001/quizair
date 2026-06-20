r"""QuizAIr Telegram-бот (Stage 4): точка входа и deep-link рефералов.

Команды:
  /start           — приветствие + кнопка «Играть» (открывает Mini App)
  /start ref_<ID>  — то же + фиксируем, кого пригласил (передаётся в бэкенд как referred_by)

Бот вызывает бэкенд по HTTP (BACKEND_URL), поэтому не зависит от его стека.
Запуск:
  set TG_BOT_TOKEN=...          (от @BotFather)
  set WEBAPP_URL=https://...     (HTTPS URL мини-аппа, например Vercel)
  set BACKEND_URL=http://127.0.0.1:8000
  ..\backend\.venv\Scripts\python.exe bot\bot.py
"""
from __future__ import annotations

import asyncio
import os
import re
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()  # подхватывает ../.env или .env из корня проекта

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

TOKEN = os.getenv("TG_BOT_TOKEN", "").strip()
WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip()
BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000").rstrip("/")

REF_RE = re.compile(r"^ref_(\d+)$")

dp = Dispatcher()


def _webapp_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="▶️ Играть", web_app=WebAppInfo(url=WEBAPP_URL))
    return kb.as_markup()


async def _ensure_user(msg: Message, referred_by: int | None) -> None:
    """Создать/обновить пользователя в бэкенде."""
    payload = {
        "tg_id": msg.from_user.id,
        "username": msg.from_user.username,
        "first_name": msg.from_user.first_name,
        "photo_url": None,
        "referred_by": referred_by,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(f"{BACKEND_URL}/users", json=payload)
    except Exception:
        pass  # бэкенд может быть недоступен — не блокируем приветствие


@dp.message(CommandStart())
async def cmd_start(msg: Message):
    if msg.from_user is None:
        return

    # /start ref_123456 → запомнить пригласившего
    parts = (msg.text or "").split(maxsplit=1)
    payload = parts[1].strip() if len(parts) > 1 else ""
    referred_by = None
    m = REF_RE.match(payload)
    if m:
        referred_by = int(m.group(1))

    await _ensure_user(msg, referred_by)

    intro = (
        "Тебя пригласил друг 🎁 Как только ответишь на 5 вопросов — "
        "пригласивший получит +3 вопроса.\n\n"
        if referred_by
        else ""
    )
    text = (
        f"{intro}🧠 <b>QuizAIr</b> — короткие квизы по ИИ, крипте, психологии, "
        f"футболу и науке. 10 бесплатных вопросов в день, значки и лидерборд."
    )

    if WEBAPP_URL:
        await msg.answer(text, reply_markup=_webapp_keyboard())
    else:
        # WEBAPP_URL не задан (dev без деплоя) — без кнопки
        await msg.answer(text + "\n\n(Mini App URL не настроен — задай WEBAPP_URL)")


@dp.message(F.text == "/help")
async def cmd_help(msg: Message):
    await msg.answer(
        "Открой меню бота или нажми «Играть». Вопросы обновляются каждый день, "
        "не теряй стрик 🔥"
    )


async def main():
    if not TOKEN:
        print("ОШИБКА: не задан TG_BOT_TOKEN. Получи токен у @BotFather.", file=sys.stderr)
        sys.exit(2)
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    print(f"QuizAIr bot: polling started (webapp={WEBAPP_URL or '—'}, backend={BACKEND_URL})")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
