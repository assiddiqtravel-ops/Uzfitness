"""Admin statistikasi va reminder dispatch repository."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ReminderDispatch,
    User,
    UserProfile,
    UserSettings,
)


# --- Admin statistikasi ---
async def count_users(session: AsyncSession) -> int:
    result = await session.execute(select(func.count()).select_from(User))
    return int(result.scalar_one())


async def count_completed_profiles(session: AsyncSession) -> int:
    result = await session.execute(
        select(func.count()).where(UserProfile.completed == True)  # noqa: E712
    )
    return int(result.scalar_one())


async def count_active_users(session: AsyncSession, days: int = 1) -> int:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    result = await session.execute(
        select(func.count()).where(User.last_active_at >= since)
    )
    return int(result.scalar_one())


async def get_all_user_ids(session: AsyncSession) -> List[int]:
    """Ommaviy xabar uchun barcha (bloklanmagan) telegram ID lar."""
    result = await session.execute(
        select(User.telegram_id).where(User.is_blocked == False)  # noqa: E712
    )
    return [int(r) for r in result.scalars().all()]


async def find_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Optional[User]:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def mark_user_blocked(session: AsyncSession, telegram_id: int, blocked: bool = True) -> None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is not None:
        user.is_blocked = blocked
        await session.flush()


# --- Reminder rejalari uchun ---
async def get_users_with_reminders(session: AsyncSession) -> List[tuple[User, UserSettings]]:
    """Eslatmalari yoqilgan foydalanuvchilar (User + Settings)."""
    result = await session.execute(
        select(User, UserSettings)
        .join(UserSettings, UserSettings.user_id == User.id)
        .where(
            User.is_blocked == False,  # noqa: E712
            (
                (UserSettings.remind_workout == True)  # noqa: E712
                | (UserSettings.remind_water == True)  # noqa: E712
                | (UserSettings.remind_weight == True)  # noqa: E712
                | (UserSettings.remind_weekly_report == True)  # noqa: E712
            ),
        )
    )
    return [(row[0], row[1]) for row in result.all()]


async def already_dispatched(
    session: AsyncSession, user_id: int, reminder_type: str, dispatch_key: str
) -> bool:
    result = await session.execute(
        select(func.count()).where(
            ReminderDispatch.user_id == user_id,
            ReminderDispatch.reminder_type == reminder_type,
            ReminderDispatch.dispatch_key == dispatch_key,
        )
    )
    return int(result.scalar_one()) > 0


async def record_dispatch(
    session: AsyncSession, user_id: int, reminder_type: str, dispatch_key: str
) -> bool:
    """Dispatch yozadi. Takror bo'lsa (unique) False qaytaradi."""
    from sqlalchemy.exc import IntegrityError

    dispatch = ReminderDispatch(
        user_id=user_id, reminder_type=reminder_type, dispatch_key=dispatch_key
    )
    session.add(dispatch)
    try:
        await session.flush()
        return True
    except IntegrityError:
        await session.rollback()
        return False


async def cleanup_old_dispatches(session: AsyncSession, keep_days: int = 14) -> None:
    """Eski dispatch yozuvlarini tozalaydi."""
    from sqlalchemy import delete

    cutoff = datetime.now(timezone.utc) - timedelta(days=keep_days)
    await session.execute(
        delete(ReminderDispatch).where(ReminderDispatch.created_at < cutoff)
    )
