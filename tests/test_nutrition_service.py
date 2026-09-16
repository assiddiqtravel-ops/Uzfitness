"""Ovqatlanish xizmati testlari (xavfsizlik qoidalari bilan)."""
from __future__ import annotations

from types import SimpleNamespace

from app.services import nutrition_service


def _profile(**kw):
    base = dict(
        weight_kg=85, height_cm=178, age=30, gender="male",
        activity_level="medium", goal="weight_loss",
        diet_type="no_restrictions", allergies=None, health_notes=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_special_condition_detection():
    assert nutrition_service.has_special_condition("Men homiladorman") is True
    assert nutrition_service.has_special_condition("hech qanday muammo yo'q") is False
    assert nutrition_service.has_special_condition(None) is False


def test_pregnancy_blocks_deficit():
    plan = nutrition_service.build_nutrition_plan(_profile(health_notes="homiladorman"))
    est = plan["estimate"]
    # defitsit qo'llanmaydi (saqlash rejimi) -> maqsad TDEE atrofida
    assert est.target_calories >= est.tdee - 1
    assert plan["warnings"], "maxsus holat uchun ogohlantirish bo'lishi kerak"


def test_minor_warning_present():
    plan = nutrition_service.build_nutrition_plan(_profile(age=16))
    assert any("18 yoshdan kichik" in w for w in plan["warnings"])


def test_vegetarian_meals_differ():
    veg = nutrition_service.build_nutrition_plan(_profile(diet_type="vegetarian"))
    normal = nutrition_service.build_nutrition_plan(_profile(diet_type="no_restrictions"))
    assert veg["meals"]["lunch"] != normal["meals"]["lunch"]


def test_format_contains_disclaimer():
    plan = nutrition_service.build_nutrition_plan(_profile())
    text = nutrition_service.format_nutrition_text(plan)
    assert "tibbiy" in text.lower()
    assert "kkal" in text
