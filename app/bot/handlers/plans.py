"""Mashg'ulot rejasi, ovqatlanish rejasi va profilni ko'rsatish."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.handlers._helpers import require_profile_or_prompt
from app.bot.keyboards import reply
from app.database.repositories import workout_repo
from app.services import nutrition_service, workout_service
from app.services.profile_service import format_profile_summary
from app.utils.text import answer_long

router = Router(name="plans")


@router.message(F.text == reply.BTN_PLAN)
async def show_workout_plan(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    plan_row = await workout_repo.get_active_plan(session, db_user.id)
    if plan_row is None:
        # profil bor, lekin reja yo'q — generatsiya qilamiz
        plan = workout_service.generate_plan(profile)
        plan_row = await workout_repo.save_plan(session, db_user.id, plan, profile.days_per_week)
    plan = workout_repo.parse_plan(plan_row)
    text = workout_service.format_plan_text(plan)
    await answer_long(message, text, reply_markup=reply.main_menu())


@router.message(F.text == reply.BTN_NUTRITION_PLAN)
async def show_nutrition_plan(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    plan = nutrition_service.build_nutrition_plan(profile)
    text = nutrition_service.format_nutrition_text(plan)
    await answer_long(message, text, reply_markup=reply.main_menu())


@router.message(F.text == reply.BTN_PROFILE)
async def show_profile(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    text = format_profile_summary(profile)
    text += "\n\nProfilni yangilash uchun /start bosing va «🚀 Boshlash» ni tanlang."
    await answer_long(message, text, reply_markup=reply.main_menu())
