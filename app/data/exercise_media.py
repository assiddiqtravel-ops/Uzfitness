"""TEKSHIRILGAN mashq media havolalari.

Bu yerdagi havolalar Wikimedia Commons'dagi ERKIN LITSENZIYALI (CC BY-SA)
animatsiyalarga (GIF) ishora qiladi. Har bir havola qidiruv orqali topilgan
va Commons fayl sahifasiga olib boradi — u yerda animatsiya ko'rinadi.

MUHIM (CLAUDE.md qoidasi): faqat ochib tekshirilgan, mavjud havolalar.
Yangi mashq qo'shsangiz — avval havolani brauzerda oching va to'g'ri ekaniga
ishonch hosil qiling. Bot mavjud bo'lmagan URL o'ylab topmaydi.

Kalitlar — app/data/exercises.py dagi Exercise.key qiymatlari.
Hozircha barcha mashqlar uchun animatsiya topilmadi (masalan glute_bridge,
plank, superman, dead_bug, leg_press, db_bench_press, db_shoulder_press,
knee_pushup) — ular uchun bot faqat matnli texnika ko'rsatadi. Erkin litsenziyali
tekshirilgan havola topsangiz, shu yerga qo'shing.
"""

EXERCISE_MEDIA = {
    # O'tirib-turish (Squat) — bodyweight squat animatsiyasi
    "bodyweight_squat": "https://commons.wikimedia.org/wiki/File:Squats.gif",
    # Oldinga qadam (Lunge)
    "lunge": "https://commons.wikimedia.org/wiki/File:Lunge-CDC_strength_training_for_older_adults.gif",
    # Otjimaniya (Push-up)
    "pushup": "https://commons.wikimedia.org/wiki/File:Pushups.gif",
    # Egilib tortish (Row) — bent-over row harakati (rezina bilan, texnika bir xil)
    "db_row": "https://commons.wikimedia.org/wiki/File:Bent_over_rows_with_resistance_bands_01.gif",
    # Yuqoridan tortish (Lat pulldown)
    "lat_pulldown": "https://commons.wikimedia.org/wiki/File:Wide-grip-lat-pull-down-1.gif",
    # Bitseps (Dumbbell curl)
    "db_curl": "https://commons.wikimedia.org/wiki/File:Standing-biceps-curl-1.gif",
}
