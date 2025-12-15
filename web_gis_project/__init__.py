"""
Пакет проекта Django.

Здесь подключается Celery-приложение, чтобы оно загружалось
при старте Django.
"""
from .celery import app as celery_app

__all__ = ("celery_app",)


