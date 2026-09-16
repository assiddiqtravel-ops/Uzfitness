"""Mashg'ulot rejasini generatsiya qilish xizmati.

AI ishlamasa ham ishlaydigan, oldindan belgilangan qoidalarga asoslangan reja.
Boshlovchilar uchun yuklama ehtiyotkor, texnikaga ustuvorlik beriladi.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from app.data import exercises as ex_data
from app.data.exercises import Exercise


# Haftalik split sxemalari: kunlar sonига qarab mushak guruhlari taqsimoti
SPLITS: Dict[int, List[Dict[str, object]]] = {
    2: [
        {"title": "1-kun · Butun tana A", "muscles": ["legs", "chest", "core"]},
        {"title": "2-kun · Butun tana B", "muscles": ["back", "shoulders", "core"]},
    ],
    3: [
        {"title": "1-kun · Butun tana", "muscles": ["legs", "chest", "back"]},
        {"title": "2-kun · Pastki tana + qorin", "muscles": ["legs", "core"]},
        {"title": "3-kun · Yuqori tana", "muscles": ["chest", "back", "shoulders", "arms"]},
    ],
    4: [
        {"title": "1-kun · Yuqori tana (itarish)", "muscles": ["chest", "shoulders", "arms"]},
        {"title": "2-kun · Pastki tana", "muscles": ["legs", "core"]},
        {"title": "3-kun · Yuqori tana (tortish)", "muscles": ["back", "arms"]},
        {"title": "4-kun · Pastki tana + qorin", "muscles": ["legs", "core"]},
    ],
    5: [
        {"title": "1-kun · Ko'krak + qorin", "muscles": ["chest", "core"]},
        {"title": "2-kun · Orqa", "muscles": ["back"]},
        {"title": "3-kun · Oyoq", "muscles": ["legs"]},
        {"title": "4-kun · Yelka + qo'l", "muscles": ["shoulders", "arms"]},
        {"title": "5-kun · Butun tana + qorin", "muscles": ["legs", "back", "core"]},
    ],
    6: [
        {"title": "1-kun · Itarish", "muscles": ["chest", "shoulders"]},
        {"title": "2-kun · Tortish", "muscles": ["back", "arms"]},
        {"title": "3-kun · Oyoq", "muscles": ["legs", "core"]},
        {"title": "4-kun · Itarish", "muscles": ["chest", "shoulders", "arms"]},
        {"title": "5-kun · Tortish", "muscles": ["back", "core"]},
        {"title": "6-kun · Oyoq + qorin", "muscles": ["legs", "core"]},
    ],
}


def _parse_equipment(equipment_text: Optional[str]) -> List[str]:
    """Profildagi jihoz matnidan jihoz kalitlarini chiqaradi."""
    if not equipment_text:
        return []
    text = equipment_text.lower()
    result = []
    if any(w in text for w in ("gantel", "dumbbell", "gantelka")):
        result.append("dumbbell")
    if any(w in text for w in ("trenajyor", "mashina", "zal", "machine")):
        result.append("machine")
    return result


def _adjust_for_experience(exercise: Exercise, experience: str) -> Dict[str, object]:
    """Tajribaga qarab set/takror va dam olishni moslashtiradi."""
    sets = exercise.default_sets
    reps = exercise.default_reps
    rest = exercise.rest_seconds

    if experience == "beginner":
        # boshlovchi: kamroq set, ko'proq dam, texnikaga urg'u
        sets = max(2, exercise.default_sets - 1)
        rest = exercise.rest_seconds + 15
    elif experience in ("6_12m", "1y_plus"):
        # tajribaliroq: standart yoki biroz ko'proq
        pass

    return {
        "name": exercise.name,
        "sets": sets,
        "reps": reps,
        "rest_seconds": rest,
        "technique": exercise.technique,
        "muscle": exercise.muscle,
        "safer_alternative": exercise.safer_alternative,
        "demo_url": ex_data.get_demo_url(exercise),
        "level": exercise.level,
    }


def generate_plan(profile) -> dict:
    """Profil obyektidan haftalik mashg'ulot rejasini yaratadi.

    profile — UserProfile (yoki shunga o'xshash) obyekt:
        .days_per_week, .location, .experience, .equipment, .goal
    """
    days_per_week = profile.days_per_week
    if days_per_week not in SPLITS:
        days_per_week = 3

    location = profile.location if profile.location in ("gym", "home", "both") else "home"
    equipment_list = _parse_equipment(getattr(profile, "equipment", None))
    experience = getattr(profile, "experience", "beginner")

    # mos mashqlar to'plami
    available = ex_data.filter_exercises(location, equipment_list, experience)

    split = SPLITS[days_per_week]
    days_out: List[dict] = []

    # boshlovchilar uchun har kun mashqlar sonini cheklaymiz
    max_exercises = 4 if experience == "beginner" else 6

    for day_def in split:
        muscles = day_def["muscles"]  # type: ignore[index]
        chosen: List[Exercise] = []
        used_keys = set()
        # har mushak guruhidan mashq tanlaymiz
        per_muscle = max(1, max_exercises // max(1, len(muscles)))  # type: ignore[arg-type]
        for muscle in muscles:  # type: ignore[union-attr]
            muscle_exs = ex_data.get_by_muscle(available, muscle)
            count = 0
            for ex in muscle_exs:
                if ex.key in used_keys:
                    continue
                chosen.append(ex)
                used_keys.add(ex.key)
                count += 1
                if count >= per_muscle or len(chosen) >= max_exercises:
                    break
            if len(chosen) >= max_exercises:
                break

        # agar hech narsa topilmasa (jihoz cheklovi), tana vazni mashqlariga qaytamiz
        if not chosen:
            for ex in ex_data.filter_exercises("home", [], experience):
                chosen.append(ex)
                if len(chosen) >= max_exercises:
                    break

        exercises_out = [_adjust_for_experience(ex, experience) for ex in chosen[:max_exercises]]
        days_out.append(
            {
                "title": day_def["title"],
                "exercises": exercises_out,
            }
        )

    return {
        "goal": getattr(profile, "goal", "healthy_start"),
        "location": location,
        "experience": experience,
        "days_per_week": days_per_week,
        "warmup": ex_data.WARMUP,
        "cooldown": ex_data.COOLDOWN,
        "days": days_out,
        "progression": (
            "Yuklamani bosqichma-bosqich oshiring: har 1-2 haftada takrorlar sonini "
            "1-2 taga yoki og'irlikni biroz ko'paytiring. Texnika buzilsa — oshirmang. "
            "Har hafta kamida 1-2 kun to'liq dam oling."
        ),
    }


def rest_days_text(days_per_week: int) -> str:
    rest = 7 - days_per_week
    return f"Haftada {rest} kun dam olish tavsiya etiladi. Dam olish — muskul o'sishining bir qismi."


def _esc(text) -> str:
    if text is None:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_plan_text(plan: dict) -> str:
    """Rejani o'qish uchun qulay HTML matnga aylantiradi."""
    lines = ["📋 <b>Shaxsiy mashg'ulot rejangiz</b>", ""]
    lines.append("🔥 <b>Qizish (har mashg'ulotdan oldin):</b>")
    for w in plan.get("warmup", []):
        lines.append(f"  • {_esc(w)}")
    lines.append("")

    for day in plan.get("days", []):
        lines.append(f"<b>{_esc(day.get('title'))}</b>")
        for i, ex in enumerate(day.get("exercises", []), 1):
            sets = ex.get("sets")
            reps = ex.get("reps")
            rest = ex.get("rest_seconds")
            head = f"  {i}. <b>{_esc(ex.get('name'))}</b>"
            if sets and reps:
                head += f" — {sets}×{_esc(reps)}"
            lines.append(head)
            if rest:
                lines.append(f"     ⏱ Dam olish: {rest} soniya")
            if ex.get("technique"):
                lines.append(f"     💡 {_esc(ex['technique'])}")
            if ex.get("safer_alternative"):
                lines.append(f"     🛟 Xavfsizroq variant mavjud ({_esc(ex['safer_alternative'])}).")
            if ex.get("demo_url"):
                lines.append(f"     🎬 Texnika: {_esc(ex['demo_url'])}")
        lines.append("")

    lines.append("🧊 <b>Sovish (har mashg'ulotdan keyin):</b>")
    for c in plan.get("cooldown", []):
        lines.append(f"  • {_esc(c)}")
    lines.append("")
    lines.append(f"📈 {_esc(plan.get('progression', ''))}")
    lines.append(rest_days_text(plan.get("days_per_week", 3)))
    return "\n".join(lines)
