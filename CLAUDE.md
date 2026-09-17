# CLAUDE.md — UzFit AI

O'zbek tilidagi shaxsiy fitnes Telegram bot (aiogram 3 + SQLAlchemy 2 async).

## Muhim tamoyillar
- **Interfeys tili:** o'zbek (lotin). Foydalanuvchiga ko'rinadigan barcha matn
  o'zbekcha bo'lsin. Kod nomlari/izohlar aralash bo'lishi mumkin, lekin Kirill
  yozuvidan foydalanmang.
- **Xavfsizlik birinchi o'rinda:** tibbiy tashxis qo'yilmaydi, agressiv
  defitsit yoki og'riqni e'tiborsiz qoldirish tavsiya etilmaydi. Yangi
  funksiyalar `MEDICAL_DISCLAIMER` va shoshilinch holat qoidalariga rioya qilsin.
- **Soxta ma'lumot yo'q:** mavjud bo'lmagan URL, kutubxona funksiyasi yoki
  tekshirilmagan havola yaratmang. Mashq media havolalari faqat
  `app/data/exercise_media.py` (config) orqali qo'shiladi.
- **Maxfiylik:** tokenlar/kalitlar faqat `.env` da; kodda saqlamang, log qilmang.

## Arxitektura
- `app/main.py` — kirish nuqtasi (polling/webhook), middleware va router wiring.
- `app/config.py` — Pydantic Settings (`.env`).
- `app/bot/` — handlerlar, klaviaturalar, middlewarelar, FSM holatlari.
- `app/database/` — modellar, async sessiya, repository qatlami.
- `app/services/` — biznes-logika (profile, workout, nutrition, progress, ai, reminder).
- `app/utils/` — validators, calculations, text, logging.
- `app/data/` — config-driven mashqlar (`exercises.py`) va oziq-ovqat (`foods.py`).

## Qoidalar
- Handlerlar DB ga to'g'ridan-to'g'ri emas, **repository** funksiyalari orqali
  murojaat qiladi. Tranzaksiyani middleware commit qiladi (handlerda
  `session.commit()` chaqirmang).
- Yangi router `app/bot/handlers/__init__.py` da ro'yxatdan o'tkaziladi. AI
  catch-all handleri **oxirida** turishi shart.
- Hisob-kitob mantiqi `app/utils/calculations.py` da bo'lsin va test qilinsin.

## Ishga tushirish va test
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # BOT_TOKEN kiriting
python -m app.main            # botni ishga tushirish
python -m pytest -q           # testlar (tokensiz ishlaydi)
```

## Migratsiyalar (Alembic)
```bash
alembic upgrade head                          # sxemani qo'llash
alembic revision --autogenerate -m "xabar"    # model o'zgarsa yangi migratsiya
```
Eslatma: `init_db()` ham jadvallarni yaratadi (Alemb.siz tez start uchun).

## Testni buzmaslik
Har o'zgarishdan keyin `python -m pytest -q` yashil bo'lishi shart. Yangi
funksiyaga test yozing (validatsiya, xavfsizlik chegaralari, foydalanuvchi
izolyatsiyasi).
