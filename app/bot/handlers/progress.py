"""Natijalar va haftalik hisobot (grafik bilan)."""
from __future__ import annotations

from aiogram import F, Router
from aiogram.types import BufferedInputFile, Message

from app.bot.handlers._helpers import require_profile_or_prompt
from app.bot.keyboards import reply
from app.database.repositories import log_repo, workout_repo
from app.services import progress_service
from app.utils.logging_config import get_logger

logger = get_logger(__name__)
router = Router(name="progress")


@router.message(F.text == reply.BTN_RESULTS)
async def show_results(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return

    weights = await log_repo.get_weight_history(session, db_user.id)
    latest = await log_repo.get_latest_weight(session, db_user.id)
    measurements = await log_repo.get_measurement_history(session, db_user.id)
    week_workouts = await workout_repo.count_completed_sessions_week(session, db_user.id)
    total_workouts = await workout_repo.count_completed_sessions_total(session, db_user.id)

    latest_waist = None
    for m in reversed(measurements):
        if m.waist_cm is not None:
            latest_waist = m.waist_cm
            break

    report = progress_service.build_progress_report(
        start_weight=profile.start_weight_kg,
        latest_weight=latest.weight_kg if latest else profile.weight_kg,
        weight_count=len(weights),
        completed_workouts_week=week_workouts,
        completed_workouts_total=total_workouts,
        latest_waist=latest_waist,
    )

    # Grafik generatsiyasi (xato bo'lsa matnli hisobot)
    chart_bytes = None
    if len(weights) >= 2:
        dates = [w.logged_at for w in weights]
        values = [w.weight_kg for w in weights]
        chart_bytes = progress_service.generate_weight_chart(dates, values)

    if chart_bytes:
        photo = BufferedInputFile(chart_bytes, filename="weight_chart.png")
        await message.answer_photo(photo, caption="📈 Vazn o'zgarishi grafigi")
        await message.answer(report, reply_markup=reply.main_menu())
    else:
        if len(weights) < 2:
            report += "\n\nℹ️ Grafik uchun kamida 2 ta vazn qaydi kerak. «⚖️ Vaznimni kiritish» orqali qo'shing."
        await message.answer(report, reply_markup=reply.main_menu())


@router.message(F.text == reply.BTN_WEEKLY)
async def weekly_report(message: Message, session, db_user) -> None:
    profile = await require_profile_or_prompt(message, session, db_user)
    if profile is None:
        return

    week_workouts = await workout_repo.count_completed_sessions_week(session, db_user.id)
    water_today = await log_repo.get_today_water_total(session, db_user.id)
    latest = await log_repo.get_latest_weight(session, db_user.id)

    lines = ["📅 <b>Haftalik hisobot</b>", ""]
    lines.append(f"• Bu hafta bajarilgan mashg'ulotlar: <b>{week_workouts}</b> / {profile.days_per_week} reja")
    if latest:
        diff = round(latest.weight_kg - profile.start_weight_kg, 1)
        arrow = "⬇️" if diff < 0 else ("⬆️" if diff > 0 else "➡️")
        lines.append(f"• Oxirgi vazn: <b>{latest.weight_kg:g} kg</b> ({diff:+g} kg {arrow})")
    lines.append(f"• Bugungi suv: <b>{water_today} ml</b>")
    lines.append("")

    if week_workouts >= profile.days_per_week:
        lines.append("🎉 Haftalik maqsadga erishdingiz! Ajoyib intizom.")
    elif week_workouts > 0:
        lines.append("👍 Yaxshi boshladingiz. Keyingi hafta rejaga to'liq amal qilishga harakat qiling.")
    else:
        lines.append("Bu hafta hali mashg'ulot yo'q. Kichik qadamdan boshlang — bugun 1 mashg'ulot! 💪")

    await message.answer("\n".join(lines), reply_markup=reply.main_menu())
