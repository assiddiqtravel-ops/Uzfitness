"""Kundalik qaydlar: suv, vazn, ovqatlanish, faollik."""
from __future__ import annotations

import re

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.handlers._helpers import require_profile_or_prompt
from app.bot.keyboards import reply
from app.bot.states.registration import NutritionInput, WaterInput, WeightInput
from app.data import foods
from app.database.repositories import log_repo, user_repo, workout_repo
from app.services.nutrition_service import build_nutrition_plan
from app.utils import validators

router = Router(name="checkin")


# ---------------- Suv ----------------
@router.message(F.text == reply.BTN_WATER)
async def water_start(message: Message, state: FSMContext, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    await state.set_state(WaterInput.amount)
    total = await log_repo.get_today_water_total(session, db_user.id)
    await message.answer(
        f"💧 Bugun jami: <b>{total} ml</b>.\n\n"
        "Qancha suv ichdingiz? (masalan: 500 yoki 0.5 l)",
        reply_markup=reply.cancel_only(),
    )


@router.message(WaterInput.amount)
async def water_save(message: Message, state: FSMContext, session, db_user) -> None:
    res = validators.validate_water_ml(message.text or "")
    if not res.ok:
        await message.answer(f"⚠️ {res.error}")
        return
    await log_repo.add_water(session, db_user.id, int(res.value))
    total = await log_repo.get_today_water_total(session, db_user.id)
    await state.clear()
    await message.answer(
        f"✅ Qayd etildi! Bugungi jami: <b>{total} ml</b>.\n\n"
        "Suv ichish — sog'lom odat. Davom eting! 👏",
        reply_markup=reply.main_menu(),
    )


# ---------------- Vazn ----------------
@router.message(F.text == reply.BTN_WEIGHT)
async def weight_start(message: Message, state: FSMContext, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    await state.set_state(WeightInput.value)
    await message.answer(
        "⚖️ Joriy vazningizni kiriting (kg, masalan 71.5):",
        reply_markup=reply.cancel_only(),
    )


@router.message(WeightInput.value)
async def weight_save(message: Message, state: FSMContext, session, db_user) -> None:
    res = validators.validate_weight(message.text or "")
    if not res.ok:
        await message.answer(f"⚠️ {res.error}")
        return
    await log_repo.add_weight(session, db_user.id, res.value)
    await user_repo.update_profile_weight(session, db_user.id, res.value)

    profile = await user_repo.get_profile(session, db_user.id)
    await state.clear()

    text = f"✅ Vazn qayd etildi: <b>{res.value:g} kg</b>."
    if profile is not None:
        diff = round(res.value - profile.start_weight_kg, 1)
        if diff < 0:
            text += f"\nBoshlanishdan: <b>{diff:g} kg</b> ⬇️"
        elif diff > 0:
            text += f"\nBoshlanishdan: <b>+{diff:g} kg</b>"
    text += (
        "\n\nℹ️ Vaznning kunlik tebranishi normal — haftalik o'rtacha tendensiyaga qarang."
    )
    await message.answer(text, reply_markup=reply.main_menu())


# ---------------- Ovqatlanish qaydi ----------------
@router.message(F.text == reply.BTN_TODAY_NUTRITION)
async def nutrition_today(message: Message, state: FSMContext, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    logs = await log_repo.get_today_nutrition(session, db_user.id)
    lines = ["🥗 <b>Bugungi ovqatlanish qaydlari</b>", ""]
    if not logs:
        lines.append("Hozircha qayd yo'q.")
    else:
        total_cal = 0
        for log in logs:
            cal_txt = f" (~{log.calories} kkal)" if log.calories else ""
            portion_txt = f", {log.portion}" if log.portion else ""
            lines.append(f"• {log.food_name}{portion_txt}{cal_txt}")
            if log.calories:
                total_cal += log.calories
        if total_cal:
            lines.append(f"\nJami (taxminiy): <b>{total_cal} kkal</b>")

    plan = build_nutrition_plan(profile)
    lines.append(f"\nKunlik maqsad (taxminiy): <b>{plan['estimate'].target_calories} kkal</b>")
    lines.append("\nYangi taom qo'shish uchun uni yozing (masalan: <i>Tovuq 200 g</i>):")

    await state.set_state(NutritionInput.food)
    await message.answer("\n".join(lines), reply_markup=reply.cancel_only())


_PORTION_RE = re.compile(r"(\d+[\.,]?\d*)\s*(g|gr|gramm|ml|dona|ta|shtuk|stakan|kosa|porsiya)?", re.IGNORECASE)


@router.message(NutritionInput.food)
async def nutrition_save(message: Message, state: FSMContext, session, db_user) -> None:
    text = (message.text or "").strip()
    if not text:
        await message.answer("Iltimos, taom nomini yozing.")
        return

    # taxminiy porsiya va kaloriyani ajratishga urinamiz
    portion = None
    calories = None
    match = _PORTION_RE.search(text)
    grams = None
    if match and match.group(1):
        try:
            grams = float(match.group(1).replace(",", "."))
            unit = (match.group(2) or "g").lower()
            portion = f"{grams:g} {unit}"
        except ValueError:
            grams = None

    food = foods.lookup_food(text)
    if food is not None and grams is not None and food.kcal:
        # faqat gramm bo'lsa kaloriya taxmin qilamiz
        if any(u in (portion or "") for u in ("g", "gr", "gramm")):
            calories = foods.estimate_calories(food, grams)

    food_name = text[:200]
    await log_repo.add_nutrition(
        session, db_user.id, food_name=food_name, portion=portion, calories=calories
    )
    await state.clear()

    reply_text = f"✅ Qayd etildi: <b>{food_name}</b>"
    if calories:
        reply_text += f" (~{calories} kkal, taxminiy)"
    else:
        reply_text += (
            "\n\nℹ️ Kaloriya faqat yetarli ma'lumot bo'lganda taxmin qilinadi "
            "(masalan, 'Tovuq 200 g')."
        )
    await message.answer(reply_text, reply_markup=reply.main_menu())


# ---------------- Faollik ----------------
@router.message(F.text == reply.BTN_ACTIVITY)
async def activity_summary(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    water = await log_repo.get_today_water_total(session, db_user.id)
    week_workouts = await workout_repo.count_completed_sessions_week(session, db_user.id)
    text = (
        "🚶 <b>Bugungi/haftalik faolligingiz</b>\n\n"
        f"• Bu hafta bajarilgan mashg'ulotlar: <b>{week_workouts}</b>\n"
        f"• Bugun ichilgan suv: <b>{water} ml</b>\n\n"
        "Kun davomida ko'proq harakat qiling: piyoda yuring, liftdan ko'ra zinapoyani "
        "tanlang. Kichik odatlar katta natija beradi! 💪"
    )
    await message.answer(text, reply_markup=reply.main_menu())
