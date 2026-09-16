"""Ro'yxatdan o'tish jarayoni (FSM) — bosqichma-bosqich profil to'ldirish."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import inline, reply
from app.bot.states.registration import Registration
from app.constants import (
    ACTIVITY,
    DIET_TYPES,
    EXPERIENCE,
    GENDERS,
    GOALS,
    LOCATIONS,
    MEDICAL_DISCLAIMER,
)
from app.database.repositories import user_repo, workout_repo
from app.services import workout_service
from app.services.profile_service import format_profile_summary
from app.utils import validators
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="registration")


# Bosqichlar tartibi (orqaga qaytish uchun)
ORDER = [
    "name", "age", "gender", "height", "weight", "goal", "location",
    "days", "experience", "activity", "diet", "allergies", "equipment",
    "health_notes", "confirm",
]


def _prev_step(step: str) -> str:
    idx = ORDER.index(step)
    return ORDER[max(0, idx - 1)]


async def prompt_step(step: str, message: Message, state: FSMContext) -> None:
    """Berilgan bosqichga o'tadi: holatni o'rnatadi va tegishli savolni yuboradi."""
    if step == "name":
        await state.set_state(Registration.name)
        await message.answer("1️⃣ Ismingizni kiriting:", reply_markup=reply.cancel_only())
    elif step == "age":
        await state.set_state(Registration.age)
        await message.answer("2️⃣ Yoshingizni kiriting (masalan, 25):", reply_markup=reply.back_cancel())
    elif step == "gender":
        await state.set_state(Registration.gender)
        await message.answer("3️⃣ Jinsingiz (ixtiyoriy):", reply_markup=reply.remove())
        await message.answer("Tanlang:", reply_markup=inline.gender_kb())
    elif step == "height":
        await state.set_state(Registration.height)
        await message.answer("4️⃣ Bo'yingizni kiriting (sm, masalan 175):", reply_markup=reply.back_cancel())
    elif step == "weight":
        await state.set_state(Registration.weight)
        await message.answer("5️⃣ Vazningizni kiriting (kg, masalan 72.5):", reply_markup=reply.back_cancel())
    elif step == "goal":
        await state.set_state(Registration.goal)
        await message.answer("6️⃣ Maqsadingiz nima?", reply_markup=inline.goal_kb())
    elif step == "location":
        await state.set_state(Registration.location)
        await message.answer("7️⃣ Qayerda shug'ullanasiz?", reply_markup=inline.location_kb())
    elif step == "days":
        await state.set_state(Registration.days_per_week)
        await message.answer("8️⃣ Haftasiga necha kun shug'ullana olasiz?", reply_markup=inline.days_kb())
    elif step == "experience":
        await state.set_state(Registration.experience)
        await message.answer("9️⃣ Fitnes tajribangiz?", reply_markup=inline.experience_kb())
    elif step == "activity":
        await state.set_state(Registration.activity)
        await message.answer("🔟 Kundalik faolligingiz?", reply_markup=inline.activity_kb())
    elif step == "diet":
        await state.set_state(Registration.diet_type)
        await message.answer("1️⃣1️⃣ Ovqatlanish turingiz yoki cheklovlaringiz?", reply_markup=inline.diet_kb())
    elif step == "allergies":
        await state.set_state(Registration.allergies)
        await message.answer(
            "1️⃣2️⃣ Allergiyalaringiz bormi? (ixtiyoriy — yozing yoki o'tkazib yuboring)",
            reply_markup=reply.back_skip_cancel(),
        )
    elif step == "equipment":
        await state.set_state(Registration.equipment)
        await message.answer(
            "1️⃣3️⃣ Qanday jihozlaringiz bor? (masalan: gantel, gimnastika gilamchasi, "
            "rezina lentalar; yoki 'yo'q' deb yozing)",
            reply_markup=reply.back_skip_cancel(),
        )
    elif step == "health_notes":
        await state.set_state(Registration.health_notes)
        await message.answer(
            "1️⃣4️⃣ Jarohat, jismoniy cheklov yoki mashqni cheklashi mumkin bo'lgan "
            "sog'liq holatingiz bormi? (ixtiyoriy — yozing yoki o'tkazib yuboring)\n\n"
            f"{MEDICAL_DISCLAIMER}",
            reply_markup=reply.back_skip_cancel(),
        )
    elif step == "confirm":
        await _show_confirm(message, state)


async def _show_confirm(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(Registration.confirm)

    class _P:  # summary uchun soxta profil obyekti
        pass

    p = _P()
    p.name = data.get("name", "")
    p.age = data.get("age", 0)
    p.gender = data.get("gender", "unspecified")
    p.height_cm = data.get("height_cm", 0)
    p.weight_kg = data.get("weight_kg", 0)
    p.start_weight_kg = data.get("weight_kg", 0)
    p.goal = data.get("goal", "healthy_start")
    p.location = data.get("location", "home")
    p.days_per_week = data.get("days_per_week", 3)
    p.experience = data.get("experience", "beginner")
    p.activity_level = data.get("activity_level", "medium")
    p.diet_type = data.get("diet_type", "no_restrictions")
    p.allergies = data.get("allergies")
    p.equipment = data.get("equipment")
    p.health_notes = data.get("health_notes")

    summary = format_profile_summary(p)
    await message.answer(
        summary + "\n\nMa'lumotlar to'g'rimi?",
        reply_markup=inline.confirm_kb(),
    )


# --- Boshlash ---
@router.callback_query(F.data == "start:begin")
async def cb_begin(callback: CallbackQuery, state: FSMContext, session, db_user) -> None:
    await state.clear()
    # Oldingi javoblar saqlangan bo'lsa yuklaymiz (qayta ochilganda)
    profile = await user_repo.get_profile(session, db_user.id)
    if profile is not None:
        await state.update_data(
            name=profile.name, age=profile.age, gender=profile.gender,
            height_cm=profile.height_cm, weight_kg=profile.weight_kg,
            goal=profile.goal, location=profile.location,
            days_per_week=profile.days_per_week, experience=profile.experience,
            activity_level=profile.activity_level, diet_type=profile.diet_type,
            allergies=profile.allergies, equipment=profile.equipment,
            health_notes=profile.health_notes,
        )
    await callback.message.answer(
        "Ajoyib! Keling, profilingizni to'ldiramiz. Istalgan vaqtda «❌ Bekor qilish» "
        "tugmasi orqali to'xtatishingiz mumkin."
    )
    await prompt_step("name", callback.message, state)
    await callback.answer()


# --- Matnli bosqichlar ---
@router.message(Registration.name)
async def step_name(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("name", message, state)
        return
    res = validators.validate_name(message.text or "")
    if not res.ok:
        await message.answer(f"⚠️ {res.error}")
        return
    await state.update_data(name=validators.clean_name(message.text or ""))
    await prompt_step("age", message, state)


@router.message(Registration.age)
async def step_age(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("name", message, state)
        return
    res = validators.validate_age(message.text or "")
    if not res.ok:
        await message.answer(f"⚠️ {res.error}")
        return
    await state.update_data(age=int(res.value))
    await prompt_step("gender", message, state)


@router.message(Registration.height)
async def step_height(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("gender", message, state)
        return
    res = validators.validate_height(message.text or "")
    if not res.ok:
        await message.answer(f"⚠️ {res.error}")
        return
    await state.update_data(height_cm=res.value)
    await prompt_step("weight", message, state)


@router.message(Registration.weight)
async def step_weight(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("height", message, state)
        return
    res = validators.validate_weight(message.text or "")
    if not res.ok:
        await message.answer(f"⚠️ {res.error}")
        return
    await state.update_data(weight_kg=res.value)
    await prompt_step("goal", message, state)


@router.message(Registration.allergies)
async def step_allergies(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("diet", message, state)
        return
    value = None if message.text == reply.BTN_SKIP else (message.text or "").strip()[:300]
    await state.update_data(allergies=value)
    await prompt_step("equipment", message, state)


@router.message(Registration.equipment)
async def step_equipment(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("allergies", message, state)
        return
    value = None if message.text == reply.BTN_SKIP else (message.text or "").strip()[:300]
    await state.update_data(equipment=value)
    await prompt_step("health_notes", message, state)


@router.message(Registration.health_notes)
async def step_health(message: Message, state: FSMContext) -> None:
    if message.text == reply.BTN_BACK:
        await prompt_step("equipment", message, state)
        return
    value = None if message.text == reply.BTN_SKIP else (message.text or "").strip()[:300]
    await state.update_data(health_notes=value)
    await prompt_step("confirm", message, state)


# --- Inline tanlovli bosqichlar ---
@router.callback_query(Registration.gender, F.data.startswith("gender:"))
async def step_gender(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("age", callback.message, state)
    elif key == "__skip__":
        await state.update_data(gender="unspecified")
        await prompt_step("height", callback.message, state)
    elif key in GENDERS:
        await state.update_data(gender=key)
        await prompt_step("height", callback.message, state)
    await callback.answer()


@router.callback_query(Registration.goal, F.data.startswith("goal:"))
async def step_goal(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("weight", callback.message, state)
    elif key in GOALS:
        await state.update_data(goal=key)
        await prompt_step("location", callback.message, state)
    await callback.answer()


@router.callback_query(Registration.location, F.data.startswith("location:"))
async def step_location(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("goal", callback.message, state)
    elif key in LOCATIONS:
        await state.update_data(location=key)
        await prompt_step("days", callback.message, state)
    await callback.answer()


@router.callback_query(Registration.days_per_week, F.data.startswith("days:"))
async def step_days(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("location", callback.message, state)
    elif key.isdigit() and validators.validate_days_per_week(int(key)):
        await state.update_data(days_per_week=int(key))
        await prompt_step("experience", callback.message, state)
    await callback.answer()


@router.callback_query(Registration.experience, F.data.startswith("exp:"))
async def step_experience(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("days", callback.message, state)
    elif key in EXPERIENCE:
        await state.update_data(experience=key)
        await prompt_step("activity", callback.message, state)
    await callback.answer()


@router.callback_query(Registration.activity, F.data.startswith("act:"))
async def step_activity(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("experience", callback.message, state)
    elif key in ACTIVITY:
        await state.update_data(activity_level=key)
        await prompt_step("diet", callback.message, state)
    await callback.answer()


@router.callback_query(Registration.diet_type, F.data.startswith("diet:"))
async def step_diet(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key == "__back__":
        await prompt_step("activity", callback.message, state)
    elif key in DIET_TYPES:
        await state.update_data(diet_type=key)
        await prompt_step("allergies", callback.message, state)
    await callback.answer()


# --- Tasdiqlash ---
@router.callback_query(Registration.confirm, F.data == "reg:restart")
async def cb_restart(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_data({})
    await prompt_step("name", callback.message, state)
    await callback.answer("Qaytadan boshlaymiz")


@router.callback_query(Registration.confirm, F.data == "reg:confirm")
async def cb_confirm(callback: CallbackQuery, state: FSMContext, session, db_user) -> None:
    data = await state.get_data()

    # Majburiy maydonlar to'liq bo'lishini tekshiramiz
    required = ["name", "age", "height_cm", "weight_kg", "goal", "location",
                "days_per_week", "experience", "activity_level"]
    if any(data.get(k) in (None, "") for k in required):
        await callback.answer("Ma'lumotlar to'liq emas, qaytadan boshlang.", show_alert=True)
        await prompt_step("name", callback.message, state)
        return

    profile_data = {
        "name": data["name"],
        "age": data["age"],
        "gender": data.get("gender", "unspecified"),
        "height_cm": data["height_cm"],
        "weight_kg": data["weight_kg"],
        "start_weight_kg": data["weight_kg"],
        "goal": data["goal"],
        "location": data["location"],
        "days_per_week": data["days_per_week"],
        "experience": data["experience"],
        "activity_level": data["activity_level"],
        "diet_type": data.get("diet_type", "no_restrictions"),
        "allergies": data.get("allergies"),
        "equipment": data.get("equipment"),
        "health_notes": data.get("health_notes"),
        "completed": True,
    }
    # Mavjud profil bo'lsa start_weight ni saqlab qolamiz
    existing = await user_repo.get_profile(session, db_user.id)
    if existing is not None:
        profile_data["start_weight_kg"] = existing.start_weight_kg

    profile = await user_repo.save_profile(session, db_user.id, profile_data)

    # Mashg'ulot rejasini generatsiya qilamiz va saqlaymiz
    try:
        plan = workout_service.generate_plan(profile)
        await workout_repo.save_plan(session, db_user.id, plan, profile.days_per_week)
    except Exception as exc:
        logger.error("Reja generatsiyasida xato: %s", exc)

    await state.clear()
    await callback.message.answer(
        "✅ <b>Profilingiz saqlandi!</b>\n\n"
        "Sizga shaxsiy mashg'ulot rejasi tayyorladim. Uni «📋 Mashg'ulot rejam» "
        "bo'limidan, ovqatlanish tavsiyalarini esa «🍽 Ovqatlanish rejam» bo'limidan "
        "ko'rishingiz mumkin.",
        reply_markup=reply.main_menu(),
    )
    await callback.answer("Tayyor!")
