"""Foydalanuvchi, profil va sozlamalar bilan ishlash (repository)."""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User, UserProfile, UserSettings, utcnow


async def get_or_create_user(
    session: AsyncSession, telegram_id: int, username: Optional[str] = None
) -> User:
    """telegram_id bo'yicha foydalanuvchini topadi yoki yaratadi (unique constraint)."""
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=telegram_id, username=username)
        session.add(user)
        await session.flush()
        # Default sozlamalarni yaratamiz
        settings = UserSettings(user_id=user.id)
        session.add(settings)
        await session.flush()
    else:
        # username va faollikni yangilaymiz
        if username and user.username != username:
            user.username = username
        user.last_active_at = utcnow()
    return user


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def get_profile(session: AsyncSession, user_id: int) -> Optional[UserProfile]:
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def save_profile(session: AsyncSession, user_id: int, data: dict) -> UserProfile:
    """Profilni yaratadi yoki yangilaydi (upsert). Ma'lumot yo'qolmaydi."""
    profile = await get_profile(session, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id, **data)
        # start_weight_kg birinchi marta = weight_kg
        if "start_weight_kg" not in data and "weight_kg" in data:
            profile.start_weight_kg = data["weight_kg"]
        session.add(profile)
    else:
        for key, value in data.items():
            setattr(profile, key, value)
    await session.flush()
    return profile


async def get_settings(session: AsyncSession, user_id: int) -> UserSettings:
    result = await session.execute(
        select(UserSettings).where(UserSettings.user_id == user_id)
    )
    settings = result.scalar_one_or_none()
    if settings is None:
        settings = UserSettings(user_id=user_id)
        session.add(settings)
        await session.flush()
    return settings


async def update_settings(session: AsyncSession, user_id: int, **fields) -> UserSettings:
    settings = await get_settings(session, user_id)
    for key, value in fields.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    await session.flush()
    return settings


async def update_profile_weight(
    session: AsyncSession, user_id: int, weight_kg: float
) -> None:
    """Profildagi joriy vaznni yangilaydi (start_weight o'zgarmaydi)."""
    profile = await get_profile(session, user_id)
    if profile is not None:
        profile.weight_kg = weight_kg
        await session.flush()
