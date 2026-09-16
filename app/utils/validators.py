"""Foydalanuvchi kiritgan ma'lumotlarni tekshirish."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    value: Optional[float] = None
    error: Optional[str] = None


# Aqlga to'g'ri keladigan chegaralar (xavfsizlik uchun)
AGE_MIN, AGE_MAX = 10, 100
HEIGHT_MIN, HEIGHT_MAX = 120, 230        # sm
WEIGHT_MIN, WEIGHT_MAX = 30, 300         # kg
WATER_MIN, WATER_MAX = 50, 5000          # ml (bitta qayd)
NAME_MIN, NAME_MAX = 2, 40


def _parse_number(raw: str) -> Optional[float]:
    """'70', '70.5', '70,5' kabi kiritmalarni float ga aylantiradi."""
    if raw is None:
        return None
    cleaned = raw.strip().replace(",", ".")
    # faqat bitta o'nlik nuqta va raqamlar bo'lsin
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def validate_name(raw: str) -> ValidationResult:
    name = (raw or "").strip()
    if len(name) < NAME_MIN:
        return ValidationResult(False, error="Ism juda qisqa. Iltimos, ismingizni to'liqroq kiriting.")
    if len(name) > NAME_MAX:
        return ValidationResult(False, error=f"Ism juda uzun (maksimum {NAME_MAX} belgi).")
    return ValidationResult(True, error=None)


def clean_name(raw: str) -> str:
    """Ismni boshqaruv belgilaridan tozalab, bir qatorli qiladi."""
    name = (raw or "").strip().replace("\n", " ").replace("\t", " ")
    return " ".join(name.split())[:NAME_MAX]


def validate_age(raw: str) -> ValidationResult:
    num = _parse_number(raw)
    if num is None or num != int(num):
        return ValidationResult(False, error="Yoshni butun son bilan kiriting. Masalan: 25")
    age = int(num)
    if age < AGE_MIN or age > AGE_MAX:
        return ValidationResult(
            False,
            error=f"Yosh {AGE_MIN} dan {AGE_MAX} gacha bo'lishi kerak. Iltimos, qayta kiriting.",
        )
    return ValidationResult(True, value=float(age))


def validate_height(raw: str) -> ValidationResult:
    num = _parse_number(raw)
    if num is None:
        return ValidationResult(False, error="Bo'yni raqam bilan kiriting (sm). Masalan: 175")
    if num < HEIGHT_MIN or num > HEIGHT_MAX:
        return ValidationResult(
            False,
            error=f"Bo'y {HEIGHT_MIN}–{HEIGHT_MAX} sm oralig'ida bo'lishi kerak. Qayta kiriting.",
        )
    return ValidationResult(True, value=round(num, 1))


def validate_weight(raw: str) -> ValidationResult:
    num = _parse_number(raw)
    if num is None:
        return ValidationResult(False, error="Vaznni raqam bilan kiriting (kg). Masalan: 72.5")
    if num < WEIGHT_MIN or num > WEIGHT_MAX:
        return ValidationResult(
            False,
            error=f"Vazn {WEIGHT_MIN}–{WEIGHT_MAX} kg oralig'ida bo'lishi kerak. Qayta kiriting.",
        )
    return ValidationResult(True, value=round(num, 1))


def validate_water_ml(raw: str) -> ValidationResult:
    """Suv miqdorini ml da qaytaradi. '0.5 l', '500', '500 ml' ni tushunadi."""
    if raw is None:
        return ValidationResult(False, error="Suv miqdorini kiriting. Masalan: 500 yoki 0.5 l")
    text = raw.strip().lower()
    is_liters = ("l" in text and "ml" not in text)
    # harflarni olib tashlab, raqamni ajratamiz
    number_part = text.replace("ml", "").replace("l", "").replace("литр", "").strip()
    num = _parse_number(number_part)
    if num is None:
        return ValidationResult(False, error="Suv miqdorini raqam bilan kiriting. Masalan: 500 (ml) yoki 0.5 l")
    ml = num * 1000 if is_liters else num
    ml = round(ml)
    if ml < WATER_MIN or ml > WATER_MAX:
        return ValidationResult(
            False,
            error=f"Bitta qaydda {WATER_MIN}–{WATER_MAX} ml oralig'ida kiriting.",
        )
    return ValidationResult(True, value=float(ml))


def validate_days_per_week(value: int) -> bool:
    return value in (2, 3, 4, 5, 6)
