"""SQLAlchemy 2.x ORM modellari.

Barcha vaqtlar UTC da saqlanadi. Foydalanuvchi vaqt zonasi user_settings da.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Timezone-aware UTC vaqt."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class User(Base):
    """Telegram foydalanuvchisi. telegram_id — unique."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)

    profile: Mapped[Optional["UserProfile"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    settings: Mapped[Optional["UserSettings"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    workout_plans: Mapped[List["WorkoutPlan"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    nutrition_logs: Mapped[List["NutritionLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    water_logs: Mapped[List["WaterLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    weight_logs: Mapped[List["WeightLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    body_measurements: Mapped[List["BodyMeasurement"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    ai_conversations: Mapped[List["AIConversation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserProfile(Base):
    """Foydalanuvchi fitnes profili."""

    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(64), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(16), default="unspecified")
    height_cm: Mapped[float] = mapped_column(Float, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    start_weight_kg: Mapped[float] = mapped_column(Float, nullable=False)

    goal: Mapped[str] = mapped_column(String(32), nullable=False)
    location: Mapped[str] = mapped_column(String(16), nullable=False)
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    experience: Mapped[str] = mapped_column(String(16), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(16), nullable=False)

    diet_type: Mapped[str] = mapped_column(String(32), default="no_restrictions")
    allergies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    equipment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    health_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class WorkoutPlan(Base):
    """Foydalanuvchiga generatsiya qilingan mashg'ulot rejasi (JSON matn ko'rinishida)."""

    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(128), default="Shaxsiy mashg'ulot rejasi")
    days_per_week: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_json: Mapped[str] = mapped_column(Text, nullable=False)  # serialize qilingan reja
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="workout_plans")
    sessions: Mapped[List["WorkoutSession"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class WorkoutSession(Base):
    """Bitta mashg'ulot kunining bajarilishi."""

    __tablename__ = "workout_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    plan_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("workout_plans.id", ondelete="SET NULL"), nullable=True
    )
    day_index: Mapped[int] = mapped_column(Integer, default=0)  # rejadagi kun raqami
    day_title: Mapped[str] = mapped_column(String(128), default="")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    total_exercises: Mapped[int] = mapped_column(Integer, default=0)
    done_exercises: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    plan: Mapped[Optional["WorkoutPlan"]] = relationship(back_populates="sessions")
    exercises: Mapped[List["WorkoutExercise"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class WorkoutExercise(Base):
    """Mashg'ulot sessiyasidagi bitta mashq va uning bajarilishi."""

    __tablename__ = "workout_exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    sets: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reps: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)

    session: Mapped["WorkoutSession"] = relationship(back_populates="exercises")


class NutritionLog(Base):
    """Ovqatlanish qaydi."""

    __tablename__ = "nutrition_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    meal_type: Mapped[str] = mapped_column(String(32), default="other")  # nonushta/tushlik...
    food_name: Mapped[str] = mapped_column(String(256), nullable=False)
    portion: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="nutrition_logs")


class WaterLog(Base):
    """Suv ichish qaydi (ml)."""

    __tablename__ = "water_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount_ml: Mapped[int] = mapped_column(Integer, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="water_logs")


class WeightLog(Base):
    """Vazn qaydi (kg) — sana bilan."""

    __tablename__ = "weight_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="weight_logs")


class BodyMeasurement(Base):
    """Tana o'lchovlari (masalan, bel aylanasi)."""

    __tablename__ = "body_measurements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    waist_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hip_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    chest_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="body_measurements")


class UserSettings(Base):
    """Foydalanuvchi sozlamalari va reminder holati."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")

    remind_workout: Mapped[bool] = mapped_column(Boolean, default=False)
    remind_water: Mapped[bool] = mapped_column(Boolean, default=False)
    remind_weight: Mapped[bool] = mapped_column(Boolean, default=False)
    remind_weekly_report: Mapped[bool] = mapped_column(Boolean, default=False)

    # HH:MM (mahalliy vaqt) — eslatma vaqtlari
    workout_time: Mapped[str] = mapped_column(String(5), default="18:00")
    weight_time: Mapped[str] = mapped_column(String(5), default="08:00")

    user: Mapped["User"] = relationship(back_populates="settings")


class AIConversation(Base):
    """AI yordamchi bilan suhbat tarixi (kontekst uchun)."""

    __tablename__ = "ai_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(16), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="ai_conversations")


# Reminderlarning bir kunda takror yuborilmasligini kuzatish uchun
class ReminderDispatch(Base):
    """Yuborilgan eslatmalarni belgilaydi (bir kunda takror yubormaslik uchun)."""

    __tablename__ = "reminder_dispatches"
    __table_args__ = (
        UniqueConstraint("user_id", "reminder_type", "dispatch_key", name="uq_reminder_once"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reminder_type: Mapped[str] = mapped_column(String(32), nullable=False)
    dispatch_key: Mapped[str] = mapped_column(String(32), nullable=False)  # masalan "2026-09-16"
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
