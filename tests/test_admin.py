"""Admin ruxsatlari va statistika testlari."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.config import Settings
from app.database.repositories import stats_repo, user_repo


def test_admin_ids_parsing():
    s = Settings(BOT_TOKEN="x", ADMIN_IDS="111, 222 ,333")
    assert s.admin_ids == [111, 222, 333]
    assert s.is_admin(222) is True
    assert s.is_admin(999) is False


def test_admin_ids_empty():
    s = Settings(BOT_TOKEN="x", ADMIN_IDS="")
    assert s.admin_ids == []
    assert s.is_admin(1) is False


def test_admin_ids_ignores_garbage():
    s = Settings(BOT_TOKEN="x", ADMIN_IDS="111,abc, ,222")
    assert s.admin_ids == [111, 222]


@pytest.mark.asyncio
async def test_is_admin_filter():
    from app.bot.handlers.admin import IsAdmin

    settings = Settings(BOT_TOKEN="x", ADMIN_IDS="500")
    flt = IsAdmin()
    admin_event = SimpleNamespace(from_user=SimpleNamespace(id=500))
    normal_event = SimpleNamespace(from_user=SimpleNamespace(id=501))
    assert await flt(admin_event, settings=settings) is True
    assert await flt(normal_event, settings=settings) is False
    assert await flt(admin_event, settings=None) is False


@pytest.mark.asyncio
async def test_stats_counts(session):
    for tid in (10, 11, 12):
        await user_repo.get_or_create_user(session, telegram_id=tid)
    await session.commit()
    total = await stats_repo.count_users(session)
    assert total == 3
    active = await stats_repo.count_active_users(session, days=1)
    assert active == 3


@pytest.mark.asyncio
async def test_get_all_user_ids_excludes_blocked(session):
    u1 = await user_repo.get_or_create_user(session, telegram_id=20)
    u2 = await user_repo.get_or_create_user(session, telegram_id=21)
    await session.commit()
    await stats_repo.mark_user_blocked(session, 21, True)
    await session.commit()
    ids = await stats_repo.get_all_user_ids(session)
    assert 20 in ids
    assert 21 not in ids
