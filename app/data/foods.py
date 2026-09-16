"""Mahalliy oziq-ovqat mahsulotlari uchun TAXMINIY kaloriya/makro ma'lumotlari.

Qiymatlar 100 gramm uchun va UMUMIY oziqlanish ma'lumotnomalariga
(masalan, USDA FoodData Central kabi ochiq manbalarga) asoslangan taxminlar.
Ular ANIQ o'lchov emas — mahsulot navi, pishirish usuli va porsiyaga qarab
farq qiladi. Bot bularni taxmin sifatida ko'rsatadi.

Struktura: kalit -> (o'zbekcha nom, kkal, oqsil_g, yog'_g, uglevod_g)  [100 g uchun]
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class Food:
    name: str
    kcal: int
    protein: float
    fat: float
    carbs: float


# 100 gramm uchun taxminiy qiymatlar
FOODS: Dict[str, Food] = {
    "egg": Food("Tuxum", 155, 13.0, 11.0, 1.1),
    "chicken_breast": Food("Tovuq ko'kragi (pishgan)", 165, 31.0, 3.6, 0.0),
    "beef_lean": Food("Mol go'shti (yog'siz)", 187, 26.0, 9.0, 0.0),
    "fish": Food("Baliq (o'rtacha)", 140, 20.0, 6.0, 0.0),
    "rice_cooked": Food("Guruch (pishgan)", 130, 2.7, 0.3, 28.0),
    "buckwheat_cooked": Food("Grechka (pishgan)", 110, 4.0, 1.0, 20.0),
    "potato_boiled": Food("Kartoshka (qaynatilgan)", 87, 2.0, 0.1, 20.0),
    "yogurt": Food("Qatiq (o'rtacha)", 60, 3.5, 3.0, 4.7),
    "tvorog": Food("Tvorog (5%)", 121, 17.0, 5.0, 3.0),
    "apple": Food("Olma", 52, 0.3, 0.2, 14.0),
    "banana": Food("Banan", 96, 1.3, 0.3, 22.0),
    "carrot": Food("Sabzi", 41, 0.9, 0.2, 10.0),
    "cucumber": Food("Bodring", 15, 0.7, 0.1, 3.6),
    "tomato": Food("Pomidor", 18, 0.9, 0.2, 3.9),
    "bread": Food("Non (o'rtacha)", 265, 9.0, 3.2, 49.0),
    "oats": Food("Suli (quruq)", 380, 13.0, 6.5, 67.0),
}


def lookup_food(text: str) -> Optional[Food]:
    """Foydalanuvchi kiritgan matndan mahsulotni topishga urinadi (soddalashtirilgan)."""
    text = (text or "").strip().lower()
    if not text:
        return None
    # nomlar bo'yicha qidiramiz
    for food in FOODS.values():
        if food.name.lower() in text or text in food.name.lower():
            return food
    # kalitlar bo'yicha
    for key, food in FOODS.items():
        if key in text:
            return food
    return None


def estimate_calories(food: Food, grams: float) -> int:
    """Berilgan grammga taxminiy kaloriya."""
    return int(round(food.kcal * grams / 100.0))
