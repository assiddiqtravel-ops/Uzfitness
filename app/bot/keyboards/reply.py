"""ReplyKeyboardMarkup — asosiy menyu va matn kiritish tugmalari."""
from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Asosiy menyu tugmalari (matnlari handlerlarda ham ishlatiladi)
BTN_TODAY_WORKOUT = "🏋️ Bugungi mashg'ulot"
BTN_TODAY_NUTRITION = "🥗 Bugungi ovqatlanish"
BTN_WATER = "💧 Suv ichdim"
BTN_ACTIVITY = "🚶 Faolligim"
BTN_WEIGHT = "⚖️ Vaznimni kiritish"
BTN_RESULTS = "📊 Natijalarim"
BTN_WEEKLY = "📅 Haftalik hisobot"
BTN_PROFILE = "👤 Profilim"
BTN_PLAN = "📋 Mashg'ulot rejam"
BTN_NUTRITION_PLAN = "🍽 Ovqatlanish rejam"
BTN_AI = "🤖 AI Murabbiy"
BTN_SETTINGS = "⚙️ Sozlamalar"

# Matn kiritish bosqichlaridagi maxsus tugmalar
BTN_CANCEL = "❌ Bekor qilish"
BTN_BACK = "⬅️ Orqaga"
BTN_SKIP = "⏭ O'tkazib yuborish"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_TODAY_WORKOUT), KeyboardButton(text=BTN_TODAY_NUTRITION)],
            [KeyboardButton(text=BTN_WATER), KeyboardButton(text=BTN_WEIGHT)],
            [KeyboardButton(text=BTN_RESULTS), KeyboardButton(text=BTN_WEEKLY)],
            [KeyboardButton(text=BTN_PLAN), KeyboardButton(text=BTN_NUTRITION_PLAN)],
            [KeyboardButton(text=BTN_AI), KeyboardButton(text=BTN_PROFILE)],
            [KeyboardButton(text=BTN_SETTINGS)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang yoki savol yozing...",
    )


def cancel_only() -> ReplyKeyboardMarkup:
    """Matn kiritishda faqat bekor qilish tugmasi."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def cancel_skip() -> ReplyKeyboardMarkup:
    """Ixtiyoriy savol uchun: o'tkazib yuborish + bekor qilish."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_SKIP)], [KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def back_cancel() -> ReplyKeyboardMarkup:
    """Matn kiritishda: orqaga + bekor qilish."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)], [KeyboardButton(text=BTN_CANCEL)]],
        resize_keyboard=True,
    )


def back_skip_cancel() -> ReplyKeyboardMarkup:
    """Ixtiyoriy matn kiritishda: o'tkazib yuborish + orqaga + bekor qilish."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_SKIP)],
            [KeyboardButton(text=BTN_BACK), KeyboardButton(text=BTN_CANCEL)],
        ],
        resize_keyboard=True,
    )


def remove() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
