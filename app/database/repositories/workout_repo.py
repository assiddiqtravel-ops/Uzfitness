"""Mashg'ulot rejalari va sessiyalari repository."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    WorkoutExercise,
    WorkoutPlan,
    WorkoutSession,
)


async def save_plan(
    session: AsyncSession,
    user_id: int,
    plan_dict: dict,
    days_per_week: int,
    title: str = "Shaxsiy mashg'ulot rejasi",
) -> WorkoutPlan:
    """Yangi reja saqlaydi va oldingilarini nofaol qiladi."""
    await session.execute(
        update(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_active == True)  # noqa: E712
        .values(is_active=False)
    )
    plan = WorkoutPlan(
        user_id=user_id,
        title=title,
        days_per_week=days_per_week,
        plan_json=json.dumps(plan_dict, ensure_ascii=False),
        is_active=True,
    )
    session.add(plan)
    await session.flush()
    return plan


async def get_active_plan(session: AsyncSession, user_id: int) -> Optional[WorkoutPlan]:
    result = await session.execute(
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id, WorkoutPlan.is_active == True)  # noqa: E712
        .order_by(WorkoutPlan.created_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


def parse_plan(plan: WorkoutPlan) -> dict:
    return json.loads(plan.plan_json)


async def create_session_from_day(
    session: AsyncSession,
    user_id: int,
    plan: WorkoutPlan,
    day_index: int,
) -> WorkoutSession:
    """Reja kunidan mashg'ulot sessiyasi yaratadi (mashqlar ro'yxati bilan)."""
    plan_data = parse_plan(plan)
    days = plan_data.get("days", [])
    if not days:
        raise ValueError("Rejada mashg'ulot kunlari yo'q")
    day_index = day_index % len(days)
    day = days[day_index]
    exercises = day.get("exercises", [])

    ws = WorkoutSession(
        user_id=user_id,
        plan_id=plan.id,
        day_index=day_index,
        day_title=day.get("title", f"{day_index + 1}-kun"),
        total_exercises=len(exercises),
        done_exercises=0,
    )
    session.add(ws)
    await session.flush()

    for i, ex in enumerate(exercises):
        session.add(
            WorkoutExercise(
                session_id=ws.id,
                order_index=i,
                name=ex.get("name", f"Mashq {i + 1}"),
                sets=ex.get("sets"),
                reps=str(ex.get("reps")) if ex.get("reps") is not None else None,
            )
        )
    await session.flush()
    return ws


async def get_session_with_exercises(
    session: AsyncSession, session_id: int
) -> Optional[WorkoutSession]:
    result = await session.execute(
        select(WorkoutSession).where(WorkoutSession.id == session_id)
    )
    ws = result.scalar_one_or_none()
    if ws is None:
        return None
    ex_result = await session.execute(
        select(WorkoutExercise)
        .where(WorkoutExercise.session_id == session_id)
        .order_by(WorkoutExercise.order_index)
    )
    ws.exercises_cache = list(ex_result.scalars().all())  # type: ignore[attr-defined]
    return ws


async def toggle_exercise_done(
    session: AsyncSession, exercise_id: int
) -> Optional[WorkoutExercise]:
    result = await session.execute(
        select(WorkoutExercise).where(WorkoutExercise.id == exercise_id)
    )
    ex = result.scalar_one_or_none()
    if ex is None:
        return None
    ex.is_done = not ex.is_done
    await session.flush()
    # sessiya statistikasini yangilaymiz
    count_result = await session.execute(
        select(func.count()).where(
            WorkoutExercise.session_id == ex.session_id,
            WorkoutExercise.is_done == True,  # noqa: E712
        )
    )
    done = int(count_result.scalar_one())
    ws_result = await session.execute(
        select(WorkoutSession).where(WorkoutSession.id == ex.session_id)
    )
    ws = ws_result.scalar_one_or_none()
    if ws is not None:
        ws.done_exercises = done
        ws.completed = done >= ws.total_exercises and ws.total_exercises > 0
    await session.flush()
    return ex


async def get_session_exercises(
    session: AsyncSession, session_id: int
) -> List[WorkoutExercise]:
    result = await session.execute(
        select(WorkoutExercise)
        .where(WorkoutExercise.session_id == session_id)
        .order_by(WorkoutExercise.order_index)
    )
    return list(result.scalars().all())


async def count_completed_sessions_week(session: AsyncSession, user_id: int) -> int:
    """Oxirgi 7 kun ichida tugallangan mashg'ulotlar soni."""
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    result = await session.execute(
        select(func.count()).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.completed == True,  # noqa: E712
            WorkoutSession.created_at >= week_ago,
        )
    )
    return int(result.scalar_one())


async def count_completed_sessions_total(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).where(
            WorkoutSession.user_id == user_id,
            WorkoutSession.completed == True,  # noqa: E712
        )
    )
    return int(result.scalar_one())
