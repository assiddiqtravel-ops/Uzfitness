"""Database CRUD, foydalanuvchi izolyatsiyasi va ma'lumot saqlanishi testlari."""
from __future__ import annotations

import pytest

from app.database.repositories import log_repo, user_repo, workout_repo
from app.services import workout_service

pytestmark = pytest.mark.asyncio


async def test_get_or_create_user_unique(session):
    u1 = await user_repo.get_or_create_user(session, telegram_id=111, username="a")
    await session.commit()
    u2 = await user_repo.get_or_create_user(session, telegram_id=111, username="a")
    assert u1.id == u2.id  # takroran yaratilmaydi (unique)


async def test_settings_auto_created(session):
    user = await user_repo.get_or_create_user(session, telegram_id=222)
    settings = await user_repo.get_settings(session, user.id)
    assert settings is not None
    assert settings.remind_water is False


async def test_profile_save_and_persist(session, sample_profile):
    user = await user_repo.get_or_create_user(session, telegram_id=333)
    data = {
        "name": sample_profile.name, "age": sample_profile.age,
        "gender": sample_profile.gender, "height_cm": sample_profile.height_cm,
        "weight_kg": sample_profile.weight_kg, "start_weight_kg": sample_profile.weight_kg,
        "goal": sample_profile.goal, "location": sample_profile.location,
        "days_per_week": sample_profile.days_per_week, "experience": sample_profile.experience,
        "activity_level": sample_profile.activity_level, "diet_type": sample_profile.diet_type,
        "completed": True,
    }
    await user_repo.save_profile(session, user.id, data)
    await session.commit()

    # qayta o'qiganda saqlangan bo'lishi kerak (bot qayta ishga tushgan holat)
    profile = await user_repo.get_profile(session, user.id)
    assert profile is not None
    assert profile.name == "Ali"
    assert profile.completed is True


async def test_profile_update_no_duplicate(session, sample_profile):
    user = await user_repo.get_or_create_user(session, telegram_id=444)
    data = {"name": "Ali", "age": 30, "gender": "male", "height_cm": 178,
            "weight_kg": 85, "start_weight_kg": 85, "goal": "weight_loss",
            "location": "home", "days_per_week": 3, "experience": "beginner",
            "activity_level": "medium", "completed": True}
    await user_repo.save_profile(session, user.id, data)
    await session.commit()
    # yangilash
    await user_repo.save_profile(session, user.id, {"name": "Vali", "weight_kg": 83})
    await session.commit()
    profile = await user_repo.get_profile(session, user.id)
    assert profile.name == "Vali"
    assert profile.weight_kg == 83
    assert profile.start_weight_kg == 85  # boshlang'ich saqlanadi


async def test_user_data_isolation(session):
    """Ikki foydalanuvchi ma'lumotlari bir-biridan ajratilgan bo'lishi kerak."""
    u1 = await user_repo.get_or_create_user(session, telegram_id=1001)
    u2 = await user_repo.get_or_create_user(session, telegram_id=1002)
    await session.commit()

    await log_repo.add_weight(session, u1.id, 80.0)
    await log_repo.add_weight(session, u1.id, 79.0)
    await log_repo.add_weight(session, u2.id, 100.0)
    await session.commit()

    w1 = await log_repo.get_weight_history(session, u1.id)
    w2 = await log_repo.get_weight_history(session, u2.id)
    assert len(w1) == 2
    assert len(w2) == 1
    assert w2[0].weight_kg == 100.0
    # u1 ning ma'lumotlari u2 ga aralashmasligi kerak
    assert all(w.user_id == u1.id for w in w1)


async def test_water_total_today(session):
    user = await user_repo.get_or_create_user(session, telegram_id=555)
    await log_repo.add_water(session, user.id, 500)
    await log_repo.add_water(session, user.id, 300)
    await session.commit()
    total = await log_repo.get_today_water_total(session, user.id)
    assert total == 800


async def test_nutrition_log_crud(session):
    user = await user_repo.get_or_create_user(session, telegram_id=666)
    await log_repo.add_nutrition(session, user.id, "Tovuq", portion="200 g", calories=330)
    await session.commit()
    logs = await log_repo.get_today_nutrition(session, user.id)
    assert len(logs) == 1
    assert logs[0].calories == 330


async def test_workout_plan_and_session(session, sample_profile):
    user = await user_repo.get_or_create_user(session, telegram_id=777)
    plan = workout_service.generate_plan(sample_profile)
    plan_row = await workout_repo.save_plan(session, user.id, plan, sample_profile.days_per_week)
    await session.commit()

    active = await workout_repo.get_active_plan(session, user.id)
    assert active is not None and active.id == plan_row.id

    ws = await workout_repo.create_session_from_day(session, user.id, plan_row, 0)
    await session.commit()
    exercises = await workout_repo.get_session_exercises(session, ws.id)
    assert len(exercises) == ws.total_exercises
    assert ws.total_exercises > 0


async def test_toggle_exercise_updates_session(session, sample_profile):
    user = await user_repo.get_or_create_user(session, telegram_id=888)
    plan = workout_service.generate_plan(sample_profile)
    plan_row = await workout_repo.save_plan(session, user.id, plan, 3)
    ws = await workout_repo.create_session_from_day(session, user.id, plan_row, 0)
    await session.commit()
    exercises = await workout_repo.get_session_exercises(session, ws.id)

    # barcha mashqlarni bajarilgan deb belgilaymiz
    for ex in exercises:
        await workout_repo.toggle_exercise_done(session, ex.id)
    await session.commit()

    updated = await workout_repo.get_session_with_exercises(session, ws.id)
    assert updated.done_exercises == updated.total_exercises
    assert updated.completed is True

    count = await workout_repo.count_completed_sessions_total(session, user.id)
    assert count == 1


async def test_new_plan_deactivates_old(session, sample_profile):
    user = await user_repo.get_or_create_user(session, telegram_id=999)
    plan = workout_service.generate_plan(sample_profile)
    p1 = await workout_repo.save_plan(session, user.id, plan, 3)
    p2 = await workout_repo.save_plan(session, user.id, plan, 3)
    await session.commit()
    active = await workout_repo.get_active_plan(session, user.id)
    assert active.id == p2.id
    # eski reja nofaol
    await session.refresh(p1)
    assert p1.is_active is False
