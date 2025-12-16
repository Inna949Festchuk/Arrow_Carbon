############################################################
# Dockerfile для Django‑приложения (Debian / Python)
#
# Образ содержит:
# - Python + зависимости из requirements.txt;
# - системные библиотеки для GeoDjango (GDAL, GEOS, PROJ, Postgres);
# - запуск Django‑сервера (dev‑вариант) по умолчанию.
############################################################

# Базовый образ: Python на Debian (bookworm = Debian 12)
FROM python:3.11-slim-bookworm

LABEL maintainer="you@example.com"

# Отключаем буферизацию stdout/stderr и пишем юникод
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Рабочая директория внутри контейнера
WORKDIR /app

############################################################
# Установка системных зависимостей
############################################################

# Установка системных зависимостей для GeoDjango
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Компиляторы и заголовки
    build-essential \
    # Утилиты GDAL
    gdal-bin \
    # Dev-заголовки GDAL
    libgdal-dev \
    # Для линковки гео-библиотек
    binutils \
    # Библиотека проекций PROJ
    libproj-dev \
    # Утилиты PROJ
    proj-bin \
    # GEOS
    libgeos-dev \
    # Клиент Postgres
    libpq-dev \
    # Для локализации
    gettext \
    # Для Pillow
    libjpeg-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libtiff-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# В некоторых системах пути к библиотекам GDAL/GEOS отличаются.
# Для Debian 12 часто используются следующие пути:

# Пути к библиотекам GDAL/GEOS
ENV GDAL_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgdal.so.32 \
    GEOS_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu/libgeos_c.so.1

############################################################
# Установка Python‑зависимостей
############################################################

# Копируем только requirements.txt для кэширования установки пакетов
COPY requirements.txt /app/requirements.txt

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

############################################################
# Копирование исходного кода проекта
############################################################

COPY . /app

# По умолчанию django использует настройки из web_gis_project/settings.py
ENV DJANGO_SETTINGS_MODULE=web_gis_project.settings

# Порт, который слушает Django
EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]