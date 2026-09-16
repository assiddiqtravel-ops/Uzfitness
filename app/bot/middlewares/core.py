"""Asosiy middlewarelar: DB sessiyasi va foydalanuvchini inyeksiya qilish."""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser

from app.database.repositories import user_repo
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def _extract_user(event: TelegramObject) -> TgUser | None:
    """Update yoki aniq eventdan Telegram foydalanuvchisini oladi.

    Update darajasidagi outer middleware da `event_from_user` hali o'rnatilmagan
    bo'ladi, shuning uchun uni to'g'ridan-to'g'ri Update.event dan olamiz.
    """
    actual = event
    if isinstance(event, Update):
        try:
            actual = event.event  # aniq event (message/callback_query/...)
        except Exception:
            actual = None
    return getattr(actual, "from_user", None) if actual is not None else None


class DBSessionMiddleware(BaseMiddleware):
    """Har bir update uchun AsyncSession yaratadi va handlerga `session` beradi."""

    def __init__(self, sessionmaker) -> None:
        self.sessionmaker = sessionmaker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.sessionmaker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise


class UserMiddleware(BaseMiddleware):
    """Foydalanuvchini topadi/yaratadi va `db_user` sifatida beradi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user") or _extract_user(event)
        session = data.get("session")
        if tg_user is not None and session is not None and not tg_user.is_bot:
            db_user = await user_repo.get_or_create_user(
                session, telegram_id=tg_user.id, username=tg_user.username
            )
            data["db_user"] = db_user
        return await handler(event, data)
