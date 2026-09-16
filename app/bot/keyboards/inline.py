"""InlineKeyboardMarkup — tanlov, tasdiqlash va mashqlar tugmalari."""
from __future__ import annotations

from typing import Dict, List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.constants import (
    ACTIVITY,
    DIET_TYPES,
    EXPERIENCE,
    GENDERS,
    GOALS,
    LOCATIONS,
    REMINDER_TYPES,
)


def _choice_kb(
    prefix: str,
    options: Dict[str, str],
    with_back: bool = True,
    with_skip: bool = False,
    columns: int = 1,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for key, label in options.items():
        builder.button(text=label, callback_data=f"{prefix}:{key}")
    builder.adjust(columns)
    extra: List[InlineKeyboardButton] = []
    if with_skip:
        extra.append(InlineKeyboardButton(text="⏭ O'tkazib yuborish", callback_data=f"{prefix}:__skip__"))
    if with_back:
        extra.append(InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"{prefix}:__back__"))
    if extra:
        builder.row(*extra)
    builder.row(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="reg:cancel"))
    return builder.as_markup()


# --- Start menyu ---
def start_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Boshlash", callback_data="start:begin")
    builder.button(text="ℹ️ Bot haqida", callback_data="start:about")
    builder.button(text="🛡 Xavfsizlik va maxfiylik", callback_data="start:privacy")
    builder.adjust(1)
    return builder.as_markup()


# --- Ro'yxatdan o'tish tanlovlari ---
def gender_kb() -> InlineKeyboardMarkup:
    return _choice_kb("gender", GENDERS, with_back=True, with_skip=True)


def goal_kb() -> InlineKeyboardMarkup:
    return _choice_kb("goal", GOALS, with_back=True)


def location_kb() -> InlineKeyboardMarkup:
    return _choice_kb("location", LOCATIONS, with_back=True)


def days_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in (2, 3, 4, 5, 6):
        builder.button(text=f"{d} kun", callback_data=f"days:{d}")
    builder.adjust(3)
    builder.row(
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data="days:__back__"),
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="reg:cancel"),
    )
    return builder.as_markup()


def experience_kb() -> InlineKeyboardMarkup:
    return _choice_kb("exp", EXPERIENCE, with_back=True)


def activity_kb() -> InlineKeyboardMarkup:
    return _choice_kb("act", ACTIVITY, with_back=True)


def diet_kb() -> InlineKeyboardMarkup:
    return _choice_kb("diet", DIET_TYPES, with_back=True)


def confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash", callback_data="reg:confirm")
    builder.button(text="🔄 Qaytadan boshlash", callback_data="reg:restart")
    builder.button(text="❌ Bekor qilish", callback_data="reg:cancel")
    builder.adjust(1)
    return builder.as_markup()


# --- Mashg'ulot sessiyasi (mashqlarni belgilash) ---
def workout_session_kb(session_id: int, exercises) -> InlineKeyboardMarkup:
    """Har bir mashq uchun 'bajarildi' toggle tugmasi."""
    builder = InlineKeyboardBuilder()
    for ex in exercises:
        mark = "✅" if ex.is_done else "⬜"
        builder.button(
            text=f"{mark} {ex.name}",
            callback_data=f"wex:{session_id}:{ex.id}",
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🏁 Yakunlash", callback_data=f"wdone:{session_id}")
    )
    return builder.as_markup()


def exercise_demo_kb(demo_url: Optional[str]) -> Optional[InlineKeyboardMarkup]:
    """Agar tekshirilgan demo havola bo'lsa — 'Ko'rsatma (video)' tugmasi."""
    if not demo_url:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Texnikani ko'rish", url=demo_url)
    return builder.as_markup()


# --- Sozlamalar / reminderlar ---
def reminders_kb(settings) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    states = {
        "workout": settings.remind_workout,
        "water": settings.remind_water,
        "weight": settings.remind_weight,
        "weekly_report": settings.remind_weekly_report,
    }
    for key, label in REMINDER_TYPES.items():
        mark = "🔔" if states.get(key) else "🔕"
        builder.button(text=f"{mark} {label}", callback_data=f"rem:{key}")
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="rem:close"))
    return builder.as_markup()


# --- Admin broadcast tasdiqlash ---
def broadcast_confirm_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, yuborilsin", callback_data="bc:yes")
    builder.button(text="❌ Bekor qilish", callback_data="bc:no")
    builder.adjust(1)
    return builder.as_markup()
