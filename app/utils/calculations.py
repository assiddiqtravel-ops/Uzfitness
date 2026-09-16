"""Kaloriya va makronutrient hisob-kitoblari.

Manba metodologiyasi:
- BMR: Mifflin-St Jeor tenglamasi (1990) — klinik amaliyotda keng qo'llaniladigan,
  ishonchli formula.
- TDEE: BMR * faollik koeffitsienti (umumiy qabul qilingan koeffitsientlar).
Barcha natijalar TAXMINIY. Bu tibbiy maslahat emas.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

# Faollik koeffitsientlari (kundalik faollik darajasiga qarab)
ACTIVITY_FACTORS: Dict[str, float] = {
    "low": 1.375,        # kam harakat (asosan o'tirib ishlash)
    "medium": 1.55,      # o'rtacha harakat
    "high": 1.725,       # faol
}

# Xavfsiz kaloriya defitsiti/profitsiti chegaralari (kkal/kun)
SAFE_DEFICIT = 400        # ehtiyotkor defitsit (vazn kamaytirish)
SAFE_SURPLUS = 250        # ehtiyotkor profitsit (massa yig'ish)

# Sog'liq uchun minimal kaloriya poli (kattalar uchun umumiy ehtiyotkor chegara)
MIN_CALORIES_FEMALE = 1200
MIN_CALORIES_MALE = 1500


@dataclass(frozen=True)
class NutritionEstimate:
    bmr: int
    tdee: int
    target_calories: int
    protein_g: int
    fat_g: int
    carbs_g: int
    water_ml: int
    note: str
    assumptions: str
    is_capped: bool  # kaloriya minimal polga tushirilganmi


def calculate_bmr(weight_kg: float, height_cm: float, age: int, gender: Optional[str]) -> float:
    """Mifflin-St Jeor BMR (kkal/kun).

    Erkak:  10*kg + 6.25*sm - 5*yosh + 5
    Ayol:   10*kg + 6.25*sm - 5*yosh - 161
    Jins noma'lum bo'lsa ikkisining o'rtachasi olinadi (taxmin ochiq ko'rsatiladi).
    """
    if weight_kg <= 0 or height_cm <= 0 or age <= 0:
        raise ValueError("weight_kg, height_cm va age musbat bo'lishi kerak")

    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    g = (gender or "").lower()
    if g in ("male", "erkak", "m"):
        return base + 5
    if g in ("female", "ayol", "f"):
        return base - 161
    # jins noma'lum -> +5 va -161 ning o'rtachasi = -78
    return base - 78


def calculate_tdee(bmr: float, activity_level: str) -> float:
    factor = ACTIVITY_FACTORS.get((activity_level or "").lower(), ACTIVITY_FACTORS["medium"])
    return bmr * factor


def _macro_split(target_calories: int, weight_kg: float, goal: str) -> Dict[str, int]:
    """Makronutrientlarni hisoblaydi.

    Oqsil: tana vazniga bog'liq (1.6–2.0 g/kg), qolgani yog' va uglevodga taqsimlanadi.
    1 g oqsil = 4 kkal, 1 g uglevod = 4 kkal, 1 g yog' = 9 kkal.
    """
    goal = (goal or "").lower()
    if goal == "muscle_gain":
        protein_per_kg = 2.0
    elif goal == "weight_loss":
        protein_per_kg = 1.8  # defitsitda mushakni saqlash uchun yuqoriroq
    else:
        protein_per_kg = 1.6

    protein_g = round(protein_per_kg * weight_kg)
    protein_kcal = protein_g * 4

    # Yog' — umumiy kaloriyaning ~25%
    fat_kcal = target_calories * 0.25
    fat_g = round(fat_kcal / 9)

    # Qolgani uglevoddan
    carbs_kcal = max(0, target_calories - protein_kcal - fat_kcal)
    carbs_g = round(carbs_kcal / 4)

    return {"protein_g": protein_g, "fat_g": fat_g, "carbs_g": carbs_g}


def recommend_water_ml(weight_kg: float, activity_level: str) -> int:
    """Umumiy suv tavsiyasi (ml). Bu qat'iy tibbiy me'yor emas, umumiy yo'riqnoma.

    Taxminan 30–35 ml/kg, faollikka qarab biroz oshiriladi.
    """
    base = 33 * weight_kg
    if (activity_level or "").lower() == "high":
        base += 400
    ml = int(round(base / 100.0) * 100)  # 100 ml gacha yaxlitlash
    return max(1500, min(ml, 4000))


def estimate_nutrition(
    *,
    weight_kg: float,
    height_cm: float,
    age: int,
    gender: Optional[str],
    activity_level: str,
    goal: str,
) -> NutritionEstimate:
    """Foydalanuvchi uchun taxminiy ovqatlanish rejasini hisoblaydi.

    Xavfsizlik qoidalari:
    - 18 yoshgacha: agressiv defitsit BERILMAYDI (tejamkor rejim TDEE atrofida).
    - Kaloriya hech qachon minimal poldan pastga tushmaydi.
    """
    bmr = calculate_bmr(weight_kg, height_cm, age, gender)
    tdee = calculate_tdee(bmr, activity_level)
    goal = (goal or "").lower()

    assumptions_parts = []
    if not gender or gender.lower() not in ("male", "ayol", "erkak", "female", "m", "f"):
        assumptions_parts.append("Jins ko'rsatilmagani uchun o'rtacha qiymat olindi")

    is_minor = age < 18

    if goal == "weight_loss":
        if is_minor:
            target = tdee  # o'smirlarga defitsit bermaymiz
            note = (
                "18 yoshdan kichik bo'lganingiz uchun vazn kamaytirish rejasi "
                "avtomatik berilmaydi. Iltimos, ota-onangiz yoki malakali "
                "shifokor/dietolog bilan maslahatlashing."
            )
        else:
            target = tdee - SAFE_DEFICIT
            note = "Ehtiyotkor kaloriya defitsiti (~400 kkal) qo'llanildi."
    elif goal == "muscle_gain":
        target = tdee + SAFE_SURPLUS
        note = "Massa yig'ish uchun ehtiyotkor kaloriya profitsiti (~250 kkal) qo'shildi."
    else:  # maintenance / healthy_start
        target = tdee
        note = "Vaznni saqlash uchun taxminiy kunlik ehtiyoj (TDEE)."

    # Minimal kaloriya poli
    g = (gender or "").lower()
    floor = MIN_CALORIES_MALE if g in ("male", "erkak", "m") else MIN_CALORIES_FEMALE
    is_capped = False
    if target < floor:
        target = floor
        is_capped = True
        note += " Kaloriya sog'liq uchun xavfsiz minimal darajada ushlab turildi."

    target = int(round(target / 10.0) * 10)  # 10 kkal gacha yaxlitlash
    macros = _macro_split(target, weight_kg, goal)
    water = recommend_water_ml(weight_kg, activity_level)

    assumptions = "; ".join(assumptions_parts) if assumptions_parts else "Qo'shimcha taxminlar yo'q."

    return NutritionEstimate(
        bmr=int(round(bmr)),
        tdee=int(round(tdee)),
        target_calories=target,
        protein_g=macros["protein_g"],
        fat_g=macros["fat_g"],
        carbs_g=macros["carbs_g"],
        water_ml=water,
        note=note,
        assumptions=assumptions,
        is_capped=is_capped,
    )


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Tana massasi indeksi (BMI)."""
    if height_cm <= 0:
        raise ValueError("height_cm musbat bo'lishi kerak")
    h_m = height_cm / 100.0
    return round(weight_kg / (h_m * h_m), 1)


def bmi_category(bmi: float) -> str:
    if bmi < 18.5:
        return "Vazn yetishmovchiligi"
    if bmi < 25:
        return "Normal vazn"
    if bmi < 30:
        return "Ortiqcha vazn"
    return "Semizlik"
