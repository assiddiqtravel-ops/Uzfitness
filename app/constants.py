"""Butun ilova bo'ylab ishlatiladigan doimiy qiymatlar va o'zbekcha yorliqlar."""
from __future__ import annotations

# --- Maqsad (goal) ---
GOALS = {
    "weight_loss": "Ortiqcha vaznni kamaytirish",
    "muscle_gain": "Mushaklarni rivojlantirish",
    "maintenance": "Vaznni saqlash",
    "healthy_start": "Sog'lom turmush tarzini boshlash",
}

# --- Shug'ullanish joyi ---
LOCATIONS = {
    "gym": "Sport zalida",
    "home": "Uyda",
    "both": "Ikkalasida ham",
}

# --- Jins ---
GENDERS = {
    "male": "Erkak",
    "female": "Ayol",
    "unspecified": "Aytmaslikni afzal ko'raman",
}

# --- Tajriba darajasi ---
EXPERIENCE = {
    "beginner": "Yangi boshlovchi",
    "1_6m": "1–6 oy",
    "6_12m": "6–12 oy",
    "1y_plus": "1 yildan ortiq",
}

# --- Kundalik faollik ---
ACTIVITY = {
    "low": "Kam harakat",
    "medium": "O'rtacha harakat",
    "high": "Faol",
}

# --- Ovqatlanish turi ---
DIET_TYPES = {
    "no_restrictions": "Cheklovsiz",
    "no_pork": "Cho'chqa go'shtisiz (halol)",
    "vegetarian": "Vegetarian",
    "lactose_free": "Sut mahsulotlarisiz",
}

# --- Reminder turlari ---
REMINDER_TYPES = {
    "workout": "Mashg'ulot eslatmasi",
    "water": "Suv ichish eslatmasi",
    "weight": "Vazn kiritish eslatmasi",
    "weekly_report": "Haftalik hisobot",
}

# Xavfsizlik ogohlantirishi (har joyda ishlatiladi)
MEDICAL_DISCLAIMER = (
    "⚠️ <b>Eslatma:</b> UzFit AI tibbiy xizmat yoki shifokor o'rnini bosmaydi. "
    "Bu umumiy ma'lumot va tavsiyalar. Sog'lig'ingiz bilan bog'liq jiddiy "
    "savollarda malakali mutaxassisga murojaat qiling."
)

# Shoshilinch (emergency) belgilari — matndan qidiriladi
EMERGENCY_KEYWORDS = [
    "ko'krak og'rig", "kokrak ogri", "ko'krak og'riq",
    "hushdan ket", "hushimdan ket",
    "nafas qis", "nafasim qis", "nafas yet",
    "kuchli og'riq", "kuchli ogriq", "to'satdan og'riq",
    "yurak sanch", "yurak og'ri",
    "hushsiz", "es-hush",
]

EMERGENCY_MESSAGE = (
    "🚑 <b>Diqqat!</b> Siz tasvirlagan holat jiddiy bo'lishi mumkin.\n\n"
    "Iltimos, <b>mashg'ulotni darhol to'xtating</b>. Agar ko'krak og'rig'i, "
    "hushdan ketish, kuchli nafas qisilishi yoki to'satdan kuchli og'riq bo'lsa — "
    "<b>zudlik bilan shoshilinch tibbiy yordamga (103) murojaat qiling</b> yoki "
    "yaqiningizdan yordam so'rang.\n\n"
    "Sog'lig'ingiz eng muhim. Men tibbiy tashxis qo'ya olmayman."
)
