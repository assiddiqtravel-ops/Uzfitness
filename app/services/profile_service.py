"""Profil bilan bog'liq yordamchi biznes-logika."""
from __future__ import annotations

from app.constants import (
    ACTIVITY,
    DIET_TYPES,
    EXPERIENCE,
    GENDERS,
    GOALS,
    LOCATIONS,
)
from app.utils.calculations import bmi_category, calculate_bmi


def format_profile_summary(profile) -> str:
    """Profilni o'qish uchun qulay matn ko'rinishida qaytaradi (HTML)."""
    bmi = calculate_bmi(profile.weight_kg, profile.height_cm)
    lines = [
        "👤 <b>Sizning profilingiz</b>",
        "",
        f"• Ism: <b>{_esc(profile.name)}</b>",
        f"• Yosh: <b>{profile.age}</b>",
        f"• Jins: {GENDERS.get(profile.gender, profile.gender)}",
        f"• Bo'y: <b>{profile.height_cm:g}</b> sm",
        f"• Vazn: <b>{profile.weight_kg:g}</b> kg (boshlang'ich: {profile.start_weight_kg:g} kg)",
        f"• BMI: <b>{bmi}</b> ({bmi_category(bmi)})",
        f"• Maqsad: {GOALS.get(profile.goal, profile.goal)}",
        f"• Joy: {LOCATIONS.get(profile.location, profile.location)}",
        f"• Haftasiga: <b>{profile.days_per_week}</b> kun",
        f"• Tajriba: {EXPERIENCE.get(profile.experience, profile.experience)}",
        f"• Faollik: {ACTIVITY.get(profile.activity_level, profile.activity_level)}",
        f"• Ovqatlanish: {DIET_TYPES.get(profile.diet_type, profile.diet_type)}",
    ]
    if profile.allergies:
        lines.append(f"• Allergiya: {_esc(profile.allergies)}")
    if profile.equipment:
        lines.append(f"• Jihozlar: {_esc(profile.equipment)}")
    if profile.health_notes:
        lines.append(f"• Sog'liq eslatmalari: {_esc(profile.health_notes)}")
    return "\n".join(lines)


def _esc(text: str) -> str:
    """HTML uchun oddiy escaping."""
    if text is None:
        return ""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
