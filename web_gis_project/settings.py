"""
Базовые настройки Django-проекта для расчёта ПДРЕ.

Это типичный settings.py для проекта уровня middle-разработчика:
- разделены основные блоки конфигурации;
- присутствуют комментарии на русском языке;
- оставлены заготовки для дальнейшего развития проекта.
"""
from pathlib import Path
import os


# -----------------------------
# БАЗОВЫЕ ПУТИ И НАСТРОЙКИ
# -----------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

# В продакшене обязательно переопределить через переменные окружения
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-secret-key-change-me",  # только для разработки
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS: list[str] = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")


# -----------------------------
# УСТАНОВЛЕННЫЕ ПРИЛОЖЕНИЯ
# -----------------------------

INSTALLED_APPS = [
    # Стандартные приложения Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # GeoDjango для работы с пространственными данными
    "django.contrib.gis",

    # Сторонние приложения
    "rest_framework",
    "rest_framework_gis",
    "corsheaders",
    "django_celery_results",
    "django_celery_beat",

    # Ваши внутренние приложения (можете добавить свои позже)
    "pdre_calculation",
    # "satellite_data",
    # "classification",
    # "open_data",
    # "recreation_load",
    # "automation",
]


# -----------------------------
# MIDDLEWARE
# -----------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # CORS должен идти до CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# -----------------------------
# ROOT URL / WSGI
# -----------------------------

ROOT_URLCONF = "web_gis_project.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = "web_gis_project.wsgi.application"


# -----------------------------
# БАЗА ДАННЫХ
# -----------------------------

"""
Типичная конфигурация для PostgreSQL + PostGIS.
В реальном окружении значения должны приходить из переменных окружения.
"""

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": os.environ.get("POSTGRES_DB", "pdre_db"),
        "USER": os.environ.get("POSTGRES_USER", "pdre_user"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "pdre_password"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


# -----------------------------
# НАСТРОЙКИ АУТЕНТИФИКАЦИИ
# -----------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# -----------------------------
# ЛОКАЛИЗАЦИЯ
# -----------------------------

LANGUAGE_CODE = "ru-ru"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# -----------------------------
# СТАТИКА И МЕДИА
# -----------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# -----------------------------
# DRF НАСТРОЙКИ
# -----------------------------

REST_FRAMEWORK = {
    # Базовые настройки DRF, можно расширять при необходимости
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}


# -----------------------------
# CORS
# -----------------------------

CORS_ALLOW_ALL_ORIGINS = True  # Для разработки. В продакшене лучше ограничить домены.

# -----------------------------
# CELERY
# -----------------------------

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

# -----------------------------
# GDAL / GEOS
# -----------------------------

# Для Linux: пути могут отличаться в зависимости от дистрибутива
GDAL_LIBRARY_PATH = os.environ.get("GDAL_LIBRARY_PATH", "/usr/lib/libgdal.so")
GEOS_LIBRARY_PATH = os.environ.get("GEOS_LIBRARY_PATH", "/usr/lib/libgeos_c.so")


# -----------------------------
# ПРОЧЕЕ
# -----------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
