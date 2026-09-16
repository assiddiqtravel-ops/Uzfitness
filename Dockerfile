# UzFit AI — Telegram fitness bot
FROM python:3.12-slim

# matplotlib va boshqa kutubxonalar uchun minimal tizim paketlari
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Avval requirements — Docker keshidan foydalanish uchun
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Ilova kodi
COPY . .

# Ma'lumotlar bazasi uchun papka (volume bilan almashtiriladi)
RUN mkdir -p /app/data

# Botni ishga tushirish (polling yoki webhook — .env dagi RUN_MODE ga qarab)
CMD ["python", "-m", "app.main"]
