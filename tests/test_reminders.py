"""Eslatmalar logikasi va takrorlanmaslik (dedup) testi."""
from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from app.database.repositories import stats_repo, user_repo
from app.services import reminder_service
from app.services.reminder_service import dispatch_key_for, due_reminders


def _settings(**kw):
    base = dict(
        remind_workout=False, remind_water=False, remind_weight=False,
        remind_weekly_report=False, workout_time="18:00", weight_time="08:00",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_workout_reminder_due_at_time():
    now = datetime(2026, 9, 16, 18, 0, tzinfo=ZoneInfo("UTC"))
    due = due_reminders(_settings(remind_workout=True, workout_time="18:00"), now)
    assert "workout" in due


def test_workout_reminder_not_due_wrong_time():
    now = datetime(2026, 9, 16, 17, 0, tzinfo=ZoneInfo("UTC"))
    due = due_reminders(_settings(remind_workout=True, workout_time="18:00"), now)
    assert "workout" not in due


def test_water_reminder_slots():
    now = datetime(2026, 9, 16, 13, 0, tzinfo=ZoneInfo("UTC"))
    due = due_reminders(_settings(remind_water=True), now)
    assert "water" in due
    now2 = datetime(2026, 9, 16, 13, 30, tzinfo=ZoneInfo("UTC"))
    assert "water" not in due_reminders(_settings(remind_water=True), now2)


def test_weekly_report_only_sunday():
    # 2026-09-20 — yakshanba
    sunday = datetime(2026, 9, 20, 20, 0, tzinfo=ZoneInfo("UTC"))
    assert sunday.weekday() == 6
    assert "weekly_report" in due_reminders(_settings(remind_weekly_report=True), sunday)
    # dushanba
    monday = datetime(2026, 9, 21, 20, 0, tzinfo=ZoneInfo("UTC"))
    assert "weekly_report" not in due_reminders(_settings(remind_weekly_report=True), monday)


def test_disabled_reminders_not_due():
    now = datetime(2026, 9, 16, 18, 0, tzinfo=ZoneInfo("UTC"))
    assert due_reminders(_settings(), now) == []


def test_dispatch_key_water_includes_slot():
    now = datetime(2026, 9, 16, 13, 0, tzinfo=ZoneInfo("UTC"))
    assert dispatch_key_for("water", now) == "2026-09-16_13:00"
    assert dispatch_key_for("workout", now) == "2026-09-16"


@pytest.mark.asyncio
async def test_dispatch_dedup(session):
    """Bir eslatma bir kunda ikki marta yozilmasin."""
    user = await user_repo.get_or_create_user(session, telegram_id=12345)
    await session.commit()
    first = await stats_repo.record_dispatch(session, user.id, "workout", "2026-09-16")
    await session.commit()
    second = await stats_repo.record_dispatch(session, user.id, "workout", "2026-09-16")
    assert first is True
    assert second is False  # takror — yuborilmaydi
