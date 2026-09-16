"""Handlerlar uchun umumiy yordamchilar."""
from __future__ import annotations

from typing import Optional

from app.bot.keyboards import inline, reply
from app.database.repositories import user_repo


async def get_completed_profile(session, db_user):
    """To'ldirilgan profilni qaytaradi yoki None."""
    profile = await user_repo.get_profile(session, db_user.id)
    if profile is None or not profile.completed:
        return None
    return profile


async def require_profile_or_prompt(message, session, db_user):
    """Profil bo'lmasa foydalanuvchini ro'yxatdan o'tishga taklif qiladi."""
    profile = await get_completed_profile(session, db_user)
    if profile is None:
        await message.answer(
            "Avval profilingizni to'ldiring. /start bosing va «🚀 Boshlash» tugmasini tanlang.",
            reply_markup=inline.start_menu(),
        )
        return None
    return profile
