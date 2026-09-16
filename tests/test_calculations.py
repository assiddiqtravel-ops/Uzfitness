"""Kaloriya/makro formulalari va chegaraviy holatlar testi."""
from __future__ import annotations

import pytest

from app.utils.calculations import (
    MIN_CALORIES_FEMALE,
    MIN_CALORIES_MALE,
    bmi_category,
    calculate_bmi,
    calculate_bmr,
    calculate_tdee,
    estimate_nutrition,
    recommend_water_ml,
)


def test_bmr_male_known_value():
    # Mifflin-St Jeor: 10*80 + 6.25*180 - 5*30 + 5 = 800+1125-150+5 = 1780
    bmr = calculate_bmr(80, 180, 30, "male")
    assert bmr == pytest.approx(1780, abs=0.5)


def test_bmr_female_known_value():
    # 10*60 + 6.25*165 - 5*25 - 161 = 600+1031.25-125-161 = 1345.25
    bmr = calculate_bmr(60, 165, 25, "female")
    assert bmr == pytest.approx(1345.25, abs=0.5)


def test_bmr_unspecified_is_between():
    male = calculate_bmr(70, 170, 28, "male")
    female = calculate_bmr(70, 170, 28, "female")
    unspecified = calculate_bmr(70, 170, 28, None)
    assert female < unspecified < male


def test_bmr_rejects_nonpositive():
    with pytest.raises(ValueError):
        calculate_bmr(0, 170, 30, "male")
    with pytest.raises(ValueError):
        calculate_bmr(70, 0, 30, "male")


def test_tdee_activity_factors():
    bmr = 1500
    low = calculate_tdee(bmr, "low")
    med = calculate_tdee(bmr, "medium")
    high = calculate_tdee(bmr, "high")
    assert low < med < high


def test_weight_loss_applies_deficit():
    est = estimate_nutrition(
        weight_kg=90, height_cm=180, age=30, gender="male",
        activity_level="medium", goal="weight_loss",
    )
    assert est.target_calories < est.tdee
    assert est.protein_g > 0 and est.fat_g > 0 and est.carbs_g >= 0


def test_muscle_gain_applies_surplus():
    est = estimate_nutrition(
        weight_kg=70, height_cm=175, age=25, gender="male",
        activity_level="high", goal="muscle_gain",
    )
    assert est.target_calories > est.tdee


def test_minor_no_aggressive_deficit():
    """17 yoshli foydalanuvchiga vazn kamaytirish defitsiti berilmaydi."""
    est = estimate_nutrition(
        weight_kg=70, height_cm=170, age=17, gender="male",
        activity_level="medium", goal="weight_loss",
    )
    # defitsit yo'q — maqsad TDEE atrofida (kamida undan past emas)
    assert est.target_calories >= est.tdee - 1
    assert "18 yoshdan kichik" in est.note


def test_calorie_floor_enforced():
    """Juda kichik odam uchun kaloriya minimal poldan pastga tushmaydi."""
    est = estimate_nutrition(
        weight_kg=45, height_cm=150, age=60, gender="female",
        activity_level="low", goal="weight_loss",
    )
    assert est.target_calories >= MIN_CALORIES_FEMALE
    assert est.is_capped is True


def test_macros_sum_reasonable():
    est = estimate_nutrition(
        weight_kg=80, height_cm=180, age=30, gender="male",
        activity_level="medium", goal="maintenance",
    )
    kcal_from_macros = est.protein_g * 4 + est.fat_g * 9 + est.carbs_g * 4
    # taxminan target atrofida (yaxlitlash sababli farq bo'lishi mumkin)
    assert abs(kcal_from_macros - est.target_calories) < 120


def test_water_recommendation_bounds():
    assert 1500 <= recommend_water_ml(80, "medium") <= 4000
    assert recommend_water_ml(100, "high") >= recommend_water_ml(60, "low")


def test_bmi_and_category():
    assert calculate_bmi(80, 178) == pytest.approx(25.2, abs=0.1)
    assert bmi_category(17) == "Vazn yetishmovchiligi"
    assert bmi_category(22) == "Normal vazn"
    assert bmi_category(27) == "Ortiqcha vazn"
    assert bmi_category(32) == "Semizlik"


def test_bmi_rejects_zero_height():
    with pytest.raises(ValueError):
        calculate_bmi(70, 0)
