"""AI suhbat tarixi repository."""
from __future__ import annotations

from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AIConversation


async def add_message(
    session: AsyncSession, user_id: int, role: str, content: str
) -> AIConversation:
    msg = AIConversation(user_id=user_id, role=role, content=content)
    session.add(msg)
    await session.flush()
    return msg


async def get_recent_messages(
    session: AsyncSession, user_id: int, limit: int = 8
) -> List[AIConversation]:
    """Oxirgi N ta xabarni (eng yangisidan) olib, xronologik tartibda qaytaradi."""
    result = await session.execute(
        select(AIConversation)
        .where(AIConversation.user_id == user_id)
        .order_by(AIConversation.created_at.desc())
        .limit(limit)
    )
    rows = list(result.scalars().all())
    rows.reverse()
    return rows
