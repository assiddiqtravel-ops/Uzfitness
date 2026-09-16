"""Ro'yxatdan o'tish (registration) FSM holatlari."""
from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()
    height = State()
    weight = State()
    goal = State()
    location = State()
    days_per_week = State()
    experience = State()
    activity = State()
    diet_type = State()
    allergies = State()
    equipment = State()
    health_notes = State()
    confirm = State()


class AIChat(StatesGroup):
    chatting = State()


class WaterInput(StatesGroup):
    amount = State()


class WeightInput(StatesGroup):
    value = State()


class NutritionInput(StatesGroup):
    food = State()


class MeasurementInput(StatesGroup):
    waist = State()


class AdminBroadcast(StatesGroup):
    message = State()
    confirm = State()


class SettingsTime(StatesGroup):
    workout_time = State()
    weight_time = State()
