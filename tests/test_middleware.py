"""Middleware integratsiyasi — DB sessiya va foydalanuvchi inyeksiyasi."""
from __future__ import annotations

from datetime import datetime

import pytest
from aiogram.types import Chat, Message, Update
from aiogram.types import User as TgUser

from app.bot.middlewares.core import DBSessionMiddleware, UserMiddleware
from app.database.repositories import user_repo

pytestmark = pytest.mark.asyncio


def _make_update(user_id: int) -> Update:
    tg_user = TgUser(id=user_id, is_bot=False, first_name="Test", username="tester")
    chat = Chat(id=user_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=tg_user,
        text="/start",
    )
    return Update(update_id=1, message=message)


async def test_middlewares_inject_session_and_user(sessionmaker):
    db_mw = DBSessionMiddleware(sessionmaker)
    user_mw = UserMiddleware()
    update = _make_update(555001)

    captured = {}

    async def final_handler(event, data):
        captured["session"] = data.get("session")
        captured["db_user"] = data.get("db_user")
        return "ok"

    async def user_stage(event, data):
        return await user_mw(final_handler, event, data)

    result = await db_mw(user_stage, update, {})

    assert result == "ok"
    assert captured["session"] is not None
    assert captured["db_user"] is not None
    assert captured["db_user"].telegram_id == 555001


async def test_user_persisted_across_updates(sessionmaker):
    """Ikkinchi update da o'sha foydalanuvchi qayta yaratilmaydi (saqlanadi)."""
    db_mw = DBSessionMiddleware(sessionmaker)
    user_mw = UserMiddleware()

    ids = []

    async def final_handler(event, data):
        ids.append(data["db_user"].id)
        return "ok"

    async def stage(event, data):
        return await user_mw(final_handler, event, data)

    await db_mw(stage, _make_update(555002), {})
    await db_mw(stage, _make_update(555002), {})

    assert ids[0] == ids[1]  # bir xil foydalanuvchi
