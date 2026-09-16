"""Sozlamalar va eslatmalar (reminderlar)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import inline, reply
from app.database.repositories import user_repo

router = Router(name="settings")


_FIELD_MAP = {
    "workout": "remind_workout",
    "water": "remind_water",
    "weight": "remind_weight",
    "weekly_report": "remind_weekly_report",
}


def _settings_text(settings) -> str:
    return (
        "⚙️ <b>Sozlamalar</b>\n\n"
        f"🕒 Vaqt zonasi: <b>{settings.timezone}</b>\n"
        f"🏋️ Mashg'ulot eslatma vaqti: <b>{settings.workout_time}</b>\n"
        f"⚖️ Vazn eslatma vaqti: <b>{settings.weight_time}</b>\n\n"
        "Quyidagi eslatmalarni yoqing yoki o'chiring 👇\n"
        "🔔 — yoqilgan, 🔕 — o'chiq"
    )


@router.message(F.text == reply.BTN_SETTINGS)
async def open_settings(message: Message, session, db_user) -> None:
    settings = await user_repo.get_settings(session, db_user.id)
    await message.answer(_settings_text(settings), reply_markup=inline.reminders_kb(settings))


@router.callback_query(F.data.startswith("rem:"))
async def toggle_reminder(callback: CallbackQuery, session, db_user) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "close":
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.message.answer("Sozlamalar yopildi.", reply_markup=reply.main_menu())
        await callback.answer()
        return

    field = _FIELD_MAP.get(key)
    if field is None:
        await callback.answer("Noma'lum sozlama.")
        return

    settings = await user_repo.get_settings(session, db_user.id)
    new_value = not getattr(settings, field)
    await user_repo.update_settings(session, db_user.id, **{field: new_value})
    settings = await user_repo.get_settings(session, db_user.id)

    try:
        await callback.message.edit_text(
            _settings_text(settings), reply_markup=inline.reminders_kb(settings)
        )
    except Exception:
        pass
    await callback.answer("🔔 Yoqildi" if new_value else "🔕 O'chirildi")
