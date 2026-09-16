"""Kundalik qaydlar (ovqat, suv, vazn, o'lchovlar) repository."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    BodyMeasurement,
    NutritionLog,
    WaterLog,
    WeightLog,
)


def _day_bounds_utc(now: Optional[datetime] = None) -> tuple[datetime, datetime]:
    """Joriy UTC kunning boshi va oxiri."""
    now = now or datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start, end


# --- Ovqat ---
async def add_nutrition(
    session: AsyncSession,
    user_id: int,
    food_name: str,
    portion: Optional[str] = None,
    calories: Optional[int] = None,
    meal_type: str = "other",
) -> NutritionLog:
    log = NutritionLog(
        user_id=user_id,
        food_name=food_name,
        portion=portion,
        calories=calories,
        meal_type=meal_type,
    )
    session.add(log)
    await session.flush()
    return log


async def get_today_nutrition(
    session: AsyncSession, user_id: int
) -> Sequence[NutritionLog]:
    start, end = _day_bounds_utc()
    result = await session.execute(
        select(NutritionLog)
        .where(
            NutritionLog.user_id == user_id,
            NutritionLog.logged_at >= start,
            NutritionLog.logged_at < end,
        )
        .order_by(NutritionLog.logged_at)
    )
    return result.scalars().all()


# --- Suv ---
async def add_water(session: AsyncSession, user_id: int, amount_ml: int) -> WaterLog:
    log = WaterLog(user_id=user_id, amount_ml=amount_ml)
    session.add(log)
    await session.flush()
    return log


async def get_today_water_total(session: AsyncSession, user_id: int) -> int:
    start, end = _day_bounds_utc()
    result = await session.execute(
        select(func.coalesce(func.sum(WaterLog.amount_ml), 0)).where(
            WaterLog.user_id == user_id,
            WaterLog.logged_at >= start,
            WaterLog.logged_at < end,
        )
    )
    return int(result.scalar_one() or 0)


# --- Vazn ---
async def add_weight(session: AsyncSession, user_id: int, weight_kg: float) -> WeightLog:
    log = WeightLog(user_id=user_id, weight_kg=weight_kg)
    session.add(log)
    await session.flush()
    return log


async def get_weight_history(
    session: AsyncSession, user_id: int, limit: int = 100
) -> List[WeightLog]:
    result = await session.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user_id)
        .order_by(WeightLog.logged_at)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_latest_weight(session: AsyncSession, user_id: int) -> Optional[WeightLog]:
    result = await session.execute(
        select(WeightLog)
        .where(WeightLog.user_id == user_id)
        .order_by(WeightLog.logged_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# --- Tana o'lchovlari ---
async def add_measurement(
    session: AsyncSession,
    user_id: int,
    waist_cm: Optional[float] = None,
    hip_cm: Optional[float] = None,
    chest_cm: Optional[float] = None,
) -> BodyMeasurement:
    m = BodyMeasurement(
        user_id=user_id, waist_cm=waist_cm, hip_cm=hip_cm, chest_cm=chest_cm
    )
    session.add(m)
    await session.flush()
    return m


async def get_measurement_history(
    session: AsyncSession, user_id: int, limit: int = 100
) -> List[BodyMeasurement]:
    result = await session.execute(
        select(BodyMeasurement)
        .where(BodyMeasurement.user_id == user_id)
        .order_by(BodyMeasurement.logged_at)
        .limit(limit)
    )
    return list(result.scalars().all())
