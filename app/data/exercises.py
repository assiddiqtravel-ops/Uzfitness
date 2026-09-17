"""Mashqlar katalogi (config-driven).

MUHIM: Bu yerda TASDIQLANMAGAN havolalar YARATILMAGAN. Har bir mashqning
`demo_url` maydoni odatda None. Agar siz mashq texnikasini ko'rsatuvchi
ISHONCHLI va TEKSHIRILGAN video/rasm havolasini qo'shmoqchi bo'lsangiz,
uni shu yerga (yoki app/data/exercise_media.py fayliga) qo'lda kiriting.
Bot mavjud bo'lmagan URL o'ylab topmaydi.

Har bir mashq:
  key: ichki identifikator
  name: o'zbekcha nom
  muscle: asosiy mushak guruhi
  location: "home" | "gym" | "both"
  equipment: kerakli jihoz ("bodyweight" = jihozsiz)
  level: "beginner" | "intermediate"
  technique: qisqa texnika tavsifi (o'zbekcha)
  safer_alternative: murakkabroq mashq uchun xavfsizroq variant (key yoki matn)
  demo_url: TEKSHIRILGAN havola yoki None
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class Exercise:
    key: str
    name: str
    muscle: str
    location: str  # home | gym | both
    equipment: str
    level: str  # beginner | intermediate
    technique: str
    default_sets: int = 3
    default_reps: str = "10-12"
    rest_seconds: int = 60
    safer_alternative: Optional[str] = None
    demo_url: Optional[str] = None  # TEKSHIRILGAN havola bo'lmasa None


# Optional tashqi media xaritasi (admin to'ldirishi mumkin).
# Kalit -> URL. Bo'sh bo'lsa hech qanday havola ko'rsatilmaydi.
try:
    from app.data.exercise_media import EXERCISE_MEDIA  # type: ignore
except Exception:  # fayl bo'lmasligi mumkin
    EXERCISE_MEDIA: Dict[str, str] = {}


CATALOG: List[Exercise] = [
    # ---- Oyoq / dumba ----
    Exercise(
        key="bodyweight_squat",
        name="O'tirib-turish (Squat)",
        muscle="legs",
        location="both",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Oyoqlar yelka kengligida. Kurak to'g'ri, ko'krak ochiq. Dumbani orqaga "
            "olib, tizzani oyoq uchidan oshirmasdan pastga o'tiring. Tovon yerdan "
            "ko'tarilmasin. Sekin turing."
        ),
        default_sets=3,
        default_reps="12-15",
        rest_seconds=60,
    ),
    Exercise(
        key="lunge",
        name="Oldinga qadam (Lunge)",
        muscle="legs",
        location="both",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Bir oyoq bilan oldinga qadam tashlang, ikkala tizza ~90° gacha bukiladi. "
            "Old tizza oyoq uchidan oshmasin. Ortga qaytib, oyoqni almashtiring."
        ),
        default_sets=3,
        default_reps="10 (har oyoq)",
        rest_seconds=60,
    ),
    Exercise(
        key="glute_bridge",
        name="Ko'prik (Glute bridge)",
        muscle="legs",
        location="home",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Chalqancha yoting, tizzalar bukilgan, tovonlar yerda. Dumbani siqib, "
            "chanoqni yuqoriga ko'taring — tana to'g'ri chiziq hosil qilsin. Sekin tushiring."
        ),
        default_sets=3,
        default_reps="15",
        rest_seconds=45,
    ),
    Exercise(
        key="leg_press",
        name="Leg press (trenajyor)",
        muscle="legs",
        location="gym",
        equipment="machine",
        level="beginner",
        technique=(
            "Platformaga oyoqlarni yelka kengligida qo'ying. Tizzani to'liq qulflamang. "
            "Nazorat bilan pastga tushiring, keyin itaring."
        ),
        default_sets=3,
        default_reps="10-12",
        rest_seconds=90,
    ),
    # ---- Ko'krak / itarish ----
    Exercise(
        key="pushup",
        name="Otjimaniya (Push-up)",
        muscle="chest",
        location="both",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Tana to'g'ri chiziqda, qo'llar yelkadan biroz keng. Tirsakni bukib ko'krakni "
            "yerga yaqinlashtiring, keyin itaring. Bel osilib qolmasin."
        ),
        default_sets=3,
        default_reps="8-12",
        rest_seconds=60,
        safer_alternative="knee_pushup",
    ),
    Exercise(
        key="knee_pushup",
        name="Tizzada otjimaniya",
        muscle="chest",
        location="both",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Tizzalarga tayanib otjimaniya. Yangi boshlovchilar uchun xavfsizroq variant. "
            "Tana tizzadan yelkagacha to'g'ri chiziqda bo'lsin."
        ),
        default_sets=3,
        default_reps="10-12",
        rest_seconds=45,
    ),
    Exercise(
        key="db_bench_press",
        name="Gantel bilan yotib itarish",
        muscle="chest",
        location="gym",
        equipment="dumbbell",
        level="intermediate",
        technique=(
            "Skameykada chalqancha yoting. Gantellarni ko'krak ustida nazorat bilan "
            "yuqoriga itaring, keyin sekin tushiring. Yelkani orqaga tortib ushlang."
        ),
        default_sets=3,
        default_reps="8-12",
        rest_seconds=90,
        safer_alternative="pushup",
    ),
    # ---- Orqa / tortish ----
    Exercise(
        key="db_row",
        name="Gantel bilan egilib tortish (Row)",
        muscle="back",
        location="both",
        equipment="dumbbell",
        level="beginner",
        technique=(
            "Bir qo'l va tizzani skameykaga qo'ying (yoki oldinga engashing). Gantelni "
            "belga tomon torting, kurakni siqing. Sekin tushiring."
        ),
        default_sets=3,
        default_reps="10-12",
        rest_seconds=60,
    ),
    Exercise(
        key="superman",
        name="Superman (bel mushaklari)",
        muscle="back",
        location="home",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Qorin bilan yoting. Qo'l va oyoqlarni bir vaqtda yerdan ko'taring, 2 soniya "
            "ushlab turing, keyin tushiring. Bo'yinni neytral ushlang."
        ),
        default_sets=3,
        default_reps="12",
        rest_seconds=45,
    ),
    Exercise(
        key="lat_pulldown",
        name="Yuqoridan tortish (Lat pulldown)",
        muscle="back",
        location="gym",
        equipment="machine",
        level="beginner",
        technique=(
            "Tutqichni yelkadan keng ushlang. Ko'krakka tomon torting, kurakni pastga va "
            "orqaga. Nazorat bilan qaytaring."
        ),
        default_sets=3,
        default_reps="10-12",
        rest_seconds=75,
    ),
    # ---- Yelka / qo'l ----
    Exercise(
        key="db_shoulder_press",
        name="Gantel bilan yelka press",
        muscle="shoulders",
        location="both",
        equipment="dumbbell",
        level="intermediate",
        technique=(
            "O'tirgan yoki turgan holda gantellarni yelka balandligidan boshga tomon "
            "itaring. Belni bukmang, qorin siqilgan bo'lsin."
        ),
        default_sets=3,
        default_reps="10-12",
        rest_seconds=60,
    ),
    Exercise(
        key="db_curl",
        name="Bitseps (Gantel curl)",
        muscle="arms",
        location="both",
        equipment="dumbbell",
        level="beginner",
        technique=(
            "Tirsakni tanaga yaqin ushlab, gantelni yuqoriga ko'taring. Yelka qimirlamasin. "
            "Sekin tushiring."
        ),
        default_sets=3,
        default_reps="10-12",
        rest_seconds=45,
    ),
    # ---- Qorin / kor ----
    Exercise(
        key="plank",
        name="Plank (taxta)",
        muscle="core",
        location="both",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Tirsak va oyoq uchida tayaning. Tana to'g'ri chiziqda, qorin va dumba siqilgan. "
            "Bel osilmasin. Belgilangan vaqt ushlang."
        ),
        default_sets=3,
        default_reps="20-40 soniya",
        rest_seconds=45,
    ),
    Exercise(
        key="dead_bug",
        name="Dead bug (qorin, xavfsiz)",
        muscle="core",
        location="home",
        equipment="bodyweight",
        level="beginner",
        technique=(
            "Chalqancha yoting, qo'l va oyoq yuqoriga. Qarama-qarshi qo'l va oyoqni sekin "
            "cho'zing, bel yerga bosilgan bo'lsin. Qaytaring."
        ),
        default_sets=3,
        default_reps="10 (har tomon)",
        rest_seconds=45,
    ),
]


# ---- Qizish va sovish ----
WARMUP: List[str] = [
    "5 daqiqa yengil yurish yoki joyida yugurish (qon aylanishini oshirish).",
    "Qo'l va yelka aylanishlari — 10 marta har tomonga.",
    "Chanoq aylanishlari va yengli cho'kkalashlar — 10 marta.",
    "Dinamik cho'zilish: oyoq tebranishlari — 10 marta har oyoq.",
]

COOLDOWN: List[str] = [
    "3-5 daqiqa sekin yurish — yurak urishini tinchlantirish.",
    "Oyoq mushaklarini cho'zish (har biri 20-30 soniya).",
    "Ko'krak va yelka cho'zilishi (20-30 soniya).",
    "Chuqur nafas olish — 5 marta.",
]


def get_demo_url(exercise: Exercise) -> Optional[str]:
    """Tashqi media xaritasidan yoki mashqning o'zidan tekshirilgan havolani qaytaradi."""
    return EXERCISE_MEDIA.get(exercise.key) or exercise.demo_url


def get_demo_file_url(exercise: Exercise) -> Optional[str]:
    """Animatsiyani chatga to'g'ridan-to'g'ri yuborish uchun media fayl havolasi.

    Wikimedia Commons 'File:' sahifasidan 'Special:FilePath' (to'g'ridan-to'g'ri
    faylga redirect) havolasini yasaydi — Telegram uni GIF/animatsiya sifatida
    yuklab, chatda ko'rsata oladi. Agar havola allaqachon to'g'ridan-to'g'ri media
    bo'lsa (.gif/.mp4/.webm), o'zini qaytaradi. Aks holda (masalan YouTube) None —
    bunda faqat havola ko'rsatiladi, chatga animatsiya yuborilmaydi.
    """
    url = get_demo_url(exercise)
    if not url:
        return None
    marker = "/wiki/File:"
    if "commons.wikimedia.org" in url and marker in url:
        filename = url.split(marker, 1)[1]
        return "https://commons.wikimedia.org/wiki/Special:FilePath/" + filename
    if url.lower().split("?")[0].endswith((".gif", ".mp4", ".webm")):
        return url
    return None


# Nom/kalit bo'yicha tez qidiruv (sessiya mashqida faqat 'name' saqlanadi).
_BY_KEY: Dict[str, Exercise] = {e.key: e for e in CATALOG}
_BY_NAME: Dict[str, Exercise] = {e.name: e for e in CATALOG}


def get_exercise_by_key(key: str) -> Optional[Exercise]:
    return _BY_KEY.get(key)


def get_exercise_by_name(name: str) -> Optional[Exercise]:
    return _BY_NAME.get(name)


def filter_exercises(
    location: str,
    equipment_list: Optional[List[str]] = None,
    level: Optional[str] = None,
) -> List[Exercise]:
    """Joy, jihoz va darajaga mos mashqlarni tanlaydi."""
    result: List[Exercise] = []
    for ex in CATALOG:
        # joy mosligi
        if location != "both" and ex.location not in (location, "both"):
            continue
        # jihoz mosligi (bodyweight har doim mumkin)
        if equipment_list is not None and ex.equipment != "bodyweight":
            if ex.equipment not in equipment_list and "machine" not in equipment_list:
                # gantel/mashina yo'q bo'lsa o'tkazamiz
                if ex.equipment in ("dumbbell", "machine"):
                    continue
        result.append(ex)
    return result


def get_by_muscle(exercises: List[Exercise], muscle: str) -> List[Exercise]:
    return [e for e in exercises if e.muscle == muscle]
