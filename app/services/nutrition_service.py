"""Ovqatlanish rejasi va tavsiyalarini tayyorlash xizmati."""
from __future__ import annotations

from typing import List, Optional

from app.constants import DIET_TYPES
from app.utils.calculations import NutritionEstimate, estimate_nutrition


# Xavfsizlik uchun maxsus holatlar (health_notes matnidan qidiriladi)
SPECIAL_CONDITION_KEYWORDS = [
    "homilador", "homila", "homiladorlik",
    "emizish", "emizyapman", "ko'krak suti",
    "ovqatlanish buzilishi", "anoreksiya", "bulimiya",
    "diabet", "qandli diabet", "shakar kasal",
    "yurak", "gipertoniya", "qon bosim",
    "buyrak", "jigar",
]


def has_special_condition(health_notes: Optional[str]) -> bool:
    if not health_notes:
        return False
    text = health_notes.lower()
    return any(kw in text for kw in SPECIAL_CONDITION_KEYWORDS)


def _meal_options(diet_type: str) -> dict:
    """Ovqatlanish turiga qarab mahalliy taom variantlari."""
    breakfast = ["Tuxum (2 dona) + non", "Suli bo'tqasi + banan", "Tvorog + meva"]
    lunch = ["Tovuq ko'kragi + guruch + sabzavot", "Mol go'shti + grechka + salat", "Baliq + kartoshka + sabzi"]
    dinner = ["Tovuq + sabzavotli salat", "Baliq + bug'da pishgan sabzavot", "Tvorog + bodring"]
    snack = ["Olma yoki banan", "Bir hovuch yong'oq (ozgina)", "Qatiq (1 stakan)"]

    if diet_type == "vegetarian":
        breakfast = ["Suli bo'tqasi + meva", "Tvorog + non", "Sabzavotli omlet (tuxumli)"]
        lunch = ["Loviya/no'xat + guruch + sabzavot", "Tvorog + grechka", "Sabzavotli sho'rva + non"]
        dinner = ["Sabzavotli salat + tvorog", "Grechka + qatiq", "Sabzavot + tuxum"]
    elif diet_type == "lactose_free":
        breakfast = ["Tuxum (2 dona) + non", "Suli bo'tqasi (suvda) + banan"]
        snack = ["Olma yoki banan", "Bir hovuch yong'oq"]

    return {"breakfast": breakfast, "lunch": lunch, "dinner": dinner, "snack": snack}


def build_nutrition_plan(profile) -> dict:
    """Profildan taxminiy ovqatlanish rejasi (dict) tuzadi.

    Xavfsizlik:
    - Maxsus holat (homiladorlik, emizish, ovqatlanish buzilishi, jiddiy kasallik)
      bo'lsa — avtomatik defitsit BERILMAYDI, mutaxassisga yo'naltiriladi.
    - 18 yoshdan kichiklar uchun agressiv defitsit yo'q (calculations.py ichida).
    """
    special = has_special_condition(getattr(profile, "health_notes", None))

    goal = getattr(profile, "goal", "healthy_start")
    if special and goal == "weight_loss":
        # xavfsiz rejim: saqlash darajasi
        effective_goal = "maintenance"
    else:
        effective_goal = goal

    estimate: NutritionEstimate = estimate_nutrition(
        weight_kg=profile.weight_kg,
        height_cm=profile.height_cm,
        age=profile.age,
        gender=getattr(profile, "gender", "unspecified"),
        activity_level=getattr(profile, "activity_level", "medium"),
        goal=effective_goal,
    )

    diet_type = getattr(profile, "diet_type", "no_restrictions")
    meals = _meal_options(diet_type)

    warnings: List[str] = []
    if special:
        warnings.append(
            "Siz ko'rsatgan sog'liq holati (masalan, homiladorlik, emizish, "
            "ovqatlanish buzilishi tarixi yoki jiddiy kasallik) sababli avtomatik "
            "vazn kamaytirish rejasi cheklandi. Iltimos, shifokor yoki malakali "
            "dietolog bilan maslahatlashing."
        )
    if profile.age < 18:
        warnings.append(
            "18 yoshdan kichik foydalanuvchilar uchun kaloriya cheklovlari "
            "berilmaydi. Ota-onangiz va shifokor bilan maslahatlashing."
        )

    return _plan_dict(estimate, meals, diet_type, profile, warnings)


def _plan_dict(estimate, meals, diet_type, profile, warnings):
    return {
        "estimate": estimate,
        "meals": meals,
        "diet_type": DIET_TYPES.get(diet_type, diet_type),
        "allergies": getattr(profile, "allergies", None),
        "warnings": warnings,
        "budget_tip": (
            "Byudjetga mos alternativalar: qimmat go'sht o'rniga tovuq son/qanoti, "
            "tvorog, tuxum va loviya — arzon oqsil manbalari. Mavsumiy sabzavot va "
            "mevalar hamyonbop."
        ),
        "water_tip": (
            "Suv: kuniga taxminan {} ml atrofida ichishga harakat qiling. Bu umumiy "
            "tavsiya — issiq havoda yoki mashg'ulot kunlarida ko'proq iching. "
            "Sog'liq holatiga qarab shifokoringiz boshqacha tavsiya bergan bo'lsa, "
            "uni ustun qo'ying."
        ).format(estimate.water_ml),
        "portion_tip": (
            "Porsiya: bir kaftingiz — oqsil (go'sht/baliq), bir mushtingiz — uglevod "
            "(guruch/grechka), bosh barmoq — yog' (yog'/yong'oq), qolgani sabzavot."
        ),
    }


def _esc(text) -> str:
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_nutrition_text(plan: dict) -> str:
    """Ovqatlanish rejasini HTML matnga aylantiradi."""
    est = plan["estimate"]
    lines = ["🍽 <b>Ovqatlanish tavsiyalari</b>", ""]
    lines.append(f"• BMR (tinch holat): <b>{est.bmr}</b> kkal/kun (taxminiy)")
    lines.append(f"• Kunlik ehtiyoj (TDEE): <b>{est.tdee}</b> kkal (taxminiy)")
    lines.append(f"• Tavsiya etilgan maqsad: <b>{est.target_calories}</b> kkal/kun")
    lines.append(f"• Oqsil: <b>{est.protein_g} g</b> · Yog': <b>{est.fat_g} g</b> · Uglevod: <b>{est.carbs_g} g</b>")
    lines.append("")
    lines.append(f"ℹ️ {_esc(est.note)}")
    if est.assumptions and est.assumptions != "Qo'shimcha taxminlar yo'q.":
        lines.append(f"📌 Taxminlar: {_esc(est.assumptions)}")
    lines.append("")

    meals = plan["meals"]
    lines.append("🌅 <b>Nonushta variantlari:</b>")
    for m in meals["breakfast"]:
        lines.append(f"  • {_esc(m)}")
    lines.append("🌞 <b>Tushlik variantlari:</b>")
    for m in meals["lunch"]:
        lines.append(f"  • {_esc(m)}")
    lines.append("🌙 <b>Kechki ovqat variantlari:</b>")
    for m in meals["dinner"]:
        lines.append(f"  • {_esc(m)}")
    lines.append("🍎 <b>Tamaddi variantlari:</b>")
    for m in meals["snack"]:
        lines.append(f"  • {_esc(m)}")
    lines.append("")
    lines.append(f"💧 {_esc(plan['water_tip'])}")
    lines.append("")
    lines.append(f"🥄 {_esc(plan['portion_tip'])}")
    lines.append("")
    lines.append(f"💰 {_esc(plan['budget_tip'])}")

    if plan.get("allergies"):
        lines.append("")
        lines.append(f"⚠️ Allergiyangiz ({_esc(plan['allergies'])}) ni hisobga oling — "
                     "mos kelmaydigan mahsulotlarni almashtiring.")
    for w in plan.get("warnings", []):
        lines.append("")
        lines.append(f"⚠️ {_esc(w)}")

    from app.constants import MEDICAL_DISCLAIMER
    lines.append("")
    lines.append(MEDICAL_DISCLAIMER)
    return "\n".join(lines)
