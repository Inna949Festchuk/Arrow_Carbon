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

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \                 # компиляторы и заголовки
    gdal-bin \                        # утилиты GDAL
    libgdal-dev \                     # dev‑заголовки GDAL
    binutils \                        # для линковки гео‑библиотек
    libproj-dev \                     # библиотека проекций PROJ
    proj-bin \                        # утилиты PROJ
    libgeos-dev \                     # GEOS
    libpq-dev \                       # клиент Postgres
    gettext \                         # для локализации (опционально)
    && rm -rf /var/lib/apt/lists/*

# В некоторых системах пути к библиотекам GDAL/GEOS отличаются.
# Для Debian 12 часто используются следующие пути (можете проверить через `ldconfig -p`):
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

############################################################
# Команда по умолчанию
#
# Для разработки: runserver на 0.0.0.0:8000
# В продакшене лучше использовать gunicorn/uwsgi.
############################################################

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]


