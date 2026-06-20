"""Проверка подписки пользователя на канал через Telegram Bot API.

Используется механизмом «Задания» (CPA): прежде чем начислить бонусные слоты
за подписку, убеждаемся, что пользователь реально состоит в канале-партнёре.

Если токен бота не задан (dev) — считаем подписку подтверждённой, чтобы флоу
можно было тестировать без бота.
"""
from __future__ import annotations

import httpx

from .config import settings

TG_API = "https://api.telegram.org/bot{token}/{method}"

# Статусы, считающиеся «подписан» (включая владельца/админа).
_SUBSCRIBED = {"creator", "administrator", "member"}


async def is_subscriber(channel: str | int, user_tg_id: int) -> bool:
    """True, если пользователь user_tg_id подписан на channel (username или id).

    Без токена (dev) — всегда True (чтобы не блокировать тестирование).
    """
    if not settings.tg_bot_token:
        return True
    if not settings.verify_subscriptions:
        return True
    url = TG_API.format(token=settings.tg_bot_token, method="getChatMember")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(
                url, params={"chat_id": channel, "user_id": user_tg_id}
            )
            data = r.json()
    except Exception:
        return False  # лучше не начислить, чем начислить накрутку
    if not data.get("ok"):
        return False
    return data["result"]["status"] in _SUBSCRIBED
