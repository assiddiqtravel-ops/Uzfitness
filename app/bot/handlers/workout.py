"""Bugungi mashg'ulot — sessiya yaratish va mashqlarni belgilash."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.handlers._helpers import require_profile_or_prompt
from app.bot.keyboards import inline, reply
from app.data import exercises as ex_data
from app.database.repositories import workout_repo
from app.services import workout_service
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="workout")


def _session_header(ws) -> str:
    return (
        f"🏋️ <b>{ws.day_title}</b>\n\n"
        f"Bajarilgan: {ws.done_exercises}/{ws.total_exercises}\n\n"
        "Bajargan mashqingizni belgilang 👇"
    )


@router.message(F.text == reply.BTN_TODAY_WORKOUT)
async def start_today_workout(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return
    plan_row = await workout_repo.get_active_plan(session, db_user.id)
    if plan_row is None:
        plan = workout_service.generate_plan(profile)
        plan_row = await workout_repo.save_plan(session, db_user.id, plan, profile.days_per_week)

    # keyingi kun indeksini tanlaymiz (aylanma tarzda)
    done_total = await workout_repo.count_completed_sessions_total(session, db_user.id)
    day_index = done_total  # create_session_from_day o'zi modulo qiladi

    try:
        ws = await workout_repo.create_session_from_day(session, db_user.id, plan_row, day_index)
    except Exception as exc:
        logger.error("Sessiya yaratishda xato: %s", exc)
        await message.answer("Kechirasiz, mashg'ulotni ochishda muammo bo'ldi. Keyinroq urinib ko'ring.")
        return

    exercises = await workout_repo.get_session_exercises(session, ws.id)

    # Qizish eslatmasi
    plan = workout_repo.parse_plan(plan_row)
    warmup = "\n".join(f"  • {w}" for w in plan.get("warmup", []))
    await message.answer(f"🔥 <b>Avval qizish:</b>\n{warmup}")

    await message.answer(
        _session_header(ws),
        reply_markup=inline.workout_session_kb(ws.id, exercises),
    )


@router.callback_query(F.data.startswith("wex:"))
async def toggle_exercise(callback: CallbackQuery, session) -> None:
    try:
        _, session_id_s, exercise_id_s = callback.data.split(":")
        session_id = int(session_id_s)
        exercise_id = int(exercise_id_s)
    except (ValueError, IndexError):
        await callback.answer("Eskirgan tugma.", show_alert=False)
        return

    ex = await workout_repo.toggle_exercise_done(session, exercise_id)
    if ex is None:
        await callback.answer("Bu mashq topilmadi (eskirgan).")
        return

    ws = await workout_repo.get_session_with_exercises(session, session_id)
    if ws is None:
        await callback.answer("Sessiya topilmadi.")
        return
    exercises = await workout_repo.get_session_exercises(session, session_id)

    try:
        await callback.message.edit_text(
            _session_header(ws),
            reply_markup=inline.workout_session_kb(session_id, exercises),
        )
    except Exception:
        # xabar o'zgarmagan bo'lsa Telegram xato beradi — e'tiborsiz qoldiramiz
        pass
    await callback.answer("✅ Bajarildi" if ex.is_done else "⬜ Bekor qilindi")


@router.callback_query(F.data.startswith("wgif:"))
async def show_exercise_gif(callback: CallbackQuery) -> None:
    """Mashq texnikasi animatsiyasini (GIF) chatga yuboradi."""
    try:
        key = callback.data.split(":", 1)[1]
    except IndexError:
        await callback.answer("Eskirgan tugma.")
        return

    exercise = ex_data.get_exercise_by_key(key)
    if exercise is None:
        await callback.answer("Mashq topilmadi.")
        return

    file_url = ex_data.get_demo_file_url(exercise)
    page_url = ex_data.get_demo_url(exercise)
    await callback.answer("🎬 Animatsiya yuborilmoqda...")

    caption = f"🎬 <b>{exercise.name}</b> — texnika"
    # Avval animatsiyani to'g'ridan-to'g'ri chatga yuborishga urinamiz
    if file_url:
        try:
            await callback.message.answer_animation(animation=file_url, caption=caption)
            return
        except Exception as exc:  # noqa: BLE001 — Telegram yuklay olmasa, havolaga o'tamiz
            logger.warning("Animatsiya yuborilmadi [%s], havola yuboramiz.", type(exc).__name__)

    # Zaxira: manba havolasini matn sifatida yuboramiz
    if page_url:
        await callback.message.answer(f"{caption}\n{page_url}")
    else:
        await callback.message.answer("Bu mashq uchun animatsiya hozircha yo'q.")


@router.callback_query(F.data.startswith("wdone:"))
async def finish_workout(callback: CallbackQuery, session) -> None:
    try:
        session_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.answer("Eskirgan tugma.")
        return

    ws = await workout_repo.get_session_with_exercises(session, session_id)
    if ws is None:
        await callback.answer("Sessiya topilmadi.")
        return

    plan_row = await workout_repo.get_active_plan(session, ws.user_id)
    cooldown = ""
    if plan_row is not None:
        plan = workout_repo.parse_plan(plan_row)
        cooldown = "\n".join(f"  • {c}" for c in plan.get("cooldown", []))

    percent = int(100 * ws.done_exercises / ws.total_exercises) if ws.total_exercises else 0
    summary = (
        f"🏁 <b>Mashg'ulot yakunlandi!</b>\n\n"
        f"Bajarildi: <b>{ws.done_exercises}/{ws.total_exercises}</b> ({percent}%)\n\n"
    )
    if percent == 100:
        summary += "🎉 Barakalla! Barcha mashqlarni bajardingiz.\n\n"
    elif percent >= 50:
        summary += "👍 Yaxshi ish! Keyingi safar to'liq bajarishga harakat qiling.\n\n"
    else:
        summary += "Har qanday harakat — bu yutuq. Davom eting! 💪\n\n"

    if cooldown:
        summary += f"🧊 <b>Endi sovish:</b>\n{cooldown}"

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await callback.message.answer(summary, reply_markup=reply.main_menu())
    await callback.answer()
