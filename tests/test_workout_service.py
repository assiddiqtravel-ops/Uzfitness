"""Mashg'ulot rejasini generatsiya qilish testlari."""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import workout_service


def _profile(**kw):
    base = dict(
        days_per_week=3, location="home", experience="beginner",
        equipment="gantel", goal="weight_loss",
    )
    base.update(kw)
    return SimpleNamespace(**base)


@pytest.mark.parametrize("days", [2, 3, 4, 5, 6])
def test_plan_matches_days(days):
    plan = workout_service.generate_plan(_profile(days_per_week=days))
    assert plan["days_per_week"] == days
    assert len(plan["days"]) == days
    for day in plan["days"]:
        assert day["exercises"], "har kunda kamida bitta mashq bo'lishi kerak"


def test_invalid_days_falls_back_to_3():
    plan = workout_service.generate_plan(_profile(days_per_week=99))
    assert plan["days_per_week"] == 3


def test_beginner_limited_exercises():
    plan = workout_service.generate_plan(_profile(experience="beginner"))
    for day in plan["days"]:
        assert len(day["exercises"]) <= 4


def test_plan_has_warmup_cooldown_progression():
    plan = workout_service.generate_plan(_profile())
    assert plan["warmup"] and plan["cooldown"]
    assert plan["progression"]


def test_home_plan_has_no_machine_without_equipment():
    plan = workout_service.generate_plan(_profile(location="home", equipment="yo'q"))
    for day in plan["days"]:
        for ex in day["exercises"]:
            # jihozsiz uyda mashina mashqlari bo'lmasligi kerak
            assert "trenajyor" not in ex["name"].lower()


def test_each_exercise_has_technique():
    plan = workout_service.generate_plan(_profile())
    for day in plan["days"]:
        for ex in day["exercises"]:
            assert ex["technique"], "har mashqda texnika tushuntirishi bo'lishi kerak"
            assert ex["sets"] and ex["reps"]


def test_no_fabricated_demo_urls():
    """Tekshirilmagan havolalar yaratilmasligi kerak (default None)."""
    plan = workout_service.generate_plan(_profile())
    for day in plan["days"]:
        for ex in day["exercises"]:
            # demo_url yo None, yo tashqi konfiguratsiyadan (bu testda bo'sh)
            assert ex["demo_url"] is None


def test_format_plan_text_produces_string():
    plan = workout_service.generate_plan(_profile())
    text = workout_service.format_plan_text(plan)
    assert isinstance(text, str) and "Shaxsiy mashg'ulot rejangiz" in text
