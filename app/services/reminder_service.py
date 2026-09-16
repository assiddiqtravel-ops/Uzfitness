"""Eslatmalar (reminderlar) xizmati — APScheduler asosida.

- Bot qayta ishga tushganda eslatmalar yo'qolmaydi (sozlamalar DB da saqlanadi).
- Bir eslatma bir kunda takror yuborilmaydi (ReminderDispatch orqali dedup).
- Vaqt zonasi har foydalanuvchi uchun alohida (user_settings.timezone).
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.utils.logging_config import get_logger

logger = get_logger(__name__)

# Suv eslatmasi yuboriladigan mahalliy vaqt slotlari
WATER_SLOTS = ["10:00", "13:00", "16:00", "19:00"]
# Haftalik hisobot: yakshanba (weekday()==6) shu vaqtda
WEEKLY_REPORT_DAY = 6  # Monday=0 ... Sunday=6
WEEKLY_REPORT_TIME = "20:00"


def _local_now(tz_name: str) -> datetime:
    try:
        tz = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, Exception):
        tz = ZoneInfo("UTC")
    return datetime.now(tz)


def due_reminders(settings, now_local: datetime) -> List[str]:
    """Berilgan mahalliy vaqtga ko'ra qaysi eslatmalar 'due' ekanini qaytaradi.

    Sof funksiya — test qilish oson. Dedup (kunlik) chaqiruvchi tomonida.
    Qaytadi: reminder_type larning ro'yxati ("workout", "water", "weight", "weekly_report").
    Har biriga dispatch kaliti chaqiruvchida quriladi.
    """
    hm = now_local.strftime("%H:%M")
    due: List[str] = []

    if getattr(settings, "remind_workout", False) and hm == getattr(settings, "workout_time", "18:00"):
        due.append("workout")

    if getattr(settings, "remind_weight", False) and hm == getattr(settings, "weight_time", "08:00"):
        due.append("weight")

    if getattr(settings, "remind_water", False) and hm in WATER_SLOTS:
        due.append("water")

    if (
        getattr(settings, "remind_weekly_report", False)
        and now_local.weekday() == WEEKLY_REPORT_DAY
        and hm == WEEKLY_REPORT_TIME
    ):
        due.append("weekly_report")

    return due


def dispatch_key_for(reminder_type: str, now_local: datetime) -> str:
    """Dedup kaliti. Suv uchun slot ham hisobga olinadi (kuniga bir necha marta)."""
    day = now_local.strftime("%Y-%m-%d")
    if reminder_type == "water":
        return f"{day}_{now_local.strftime('%H:%M')}"
    return day


REMINDER_MESSAGES = {
    "workout": "🏋️ Salom! Bugungi mashg'ulot vaqti keldi. «🏋️ Bugungi mashg'ulot» tugmasini bosing.",
    "water": "💧 Suv ichishni unutmang! Bir stakan suv iching va «💧 Suv ichdim» orqali qayd eting.",
    "weight": "⚖️ Vazningizni kiritish vaqti keldi. «⚖️ Vaznimni kiritish» tugmasini bosing.",
    "weekly_report": "📅 Haftalik hisobotingiz tayyor! «📅 Haftalik hisobot» bo'limiga kiring.",
}


class ReminderService:
    """APScheduler ni sozlab, har daqiqa eslatmalarni tekshiradi."""

    def __init__(self, bot, sessionmaker) -> None:
        self.bot = bot
        self.sessionmaker = sessionmaker
        self._scheduler = None

    def start(self, timezone: str = "UTC") -> None:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
        except ImportError:
            logger.warning("APScheduler o'rnatilmagan — eslatmalar o'chiq.")
            return
        self._scheduler = AsyncIOScheduler(timezone="UTC")
        # har daqiqada tekshiramiz
        self._scheduler.add_job(self._tick, "cron", minute="*", id="reminder_tick")
        # kuniga bir marta eski dispatchlarni tozalash
        self._scheduler.add_job(self._cleanup, "cron", hour=3, minute=0, id="reminder_cleanup")
        self._scheduler.start()
        logger.info("Reminder scheduler ishga tushdi.")

    def shutdown(self) -> None:
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)
            self._scheduler = None

    async def _tick(self) -> None:
        """Har daqiqada chaqiriladi: due eslatmalarni topib yuboradi."""
        from app.database.repositories import stats_repo

        try:
            async with self.sessionmaker() as session:
                pairs = await stats_repo.get_users_with_reminders(session)
        except Exception as exc:
            logger.error("Reminder tick — DB xatosi: %s", exc)
            return

        for user, settings in pairs:
            tz_name = getattr(settings, "timezone", "UTC")
            now_local = _local_now(tz_name)
            due = due_reminders(settings, now_local)
            for reminder_type in due:
                key = dispatch_key_for(reminder_type, now_local)
                await self._send_once(user, reminder_type, key)

    async def _send_once(self, user, reminder_type: str, dispatch_key: str) -> None:
        from app.database.repositories import stats_repo

        try:
            async with self.sessionmaker() as session:
                recorded = await stats_repo.record_dispatch(
                    session, user.id, reminder_type, dispatch_key
                )
                await session.commit()
        except Exception as exc:
            logger.error("Dispatch yozishda xato: %s", exc)
            return

        if not recorded:
            return  # allaqachon yuborilgan (takror emas)

        text = REMINDER_MESSAGES.get(reminder_type)
        if not text:
            return
        try:
            await self.bot.send_message(user.telegram_id, text)
        except Exception as exc:
            # foydalanuvchi botni bloklagan bo'lishi mumkin
            logger.warning("Eslatma yuborilmadi (user=%s): %s", user.telegram_id, exc.__class__.__name__)

    async def _cleanup(self) -> None:
        from app.database.repositories import stats_repo

        try:
            async with self.sessionmaker() as session:
                await stats_repo.cleanup_old_dispatches(session)
                await session.commit()
        except Exception as exc:
            logger.error("Dispatch tozalashda xato: %s", exc)
