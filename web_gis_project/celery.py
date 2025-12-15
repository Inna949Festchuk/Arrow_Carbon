"""
Конфигурация Celery для проекта.

Celery используется для асинхронного выполнения задач:
- расчёт ПДРЕ;
- импорт геоданных;
- генерация отчётов и паспортов.
"""
import os

from celery import Celery

# Указываем настройки Django для Celery
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_gis_project.settings")

# Создаём экземпляр Celery-приложения
app = Celery("web_gis_project")

# Загружаем конфигурацию Celery из Django-настроек с префиксом CELERY_
app.config_from_object("django.conf:settings", namespace="CELERY")

# Автоматически находим задачи (tasks.py) во всех установленных приложениях
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self) -> None:
    """
    Простейшая отладочная задача, которую можно запустить
    командой `celery -A web_gis_project debug_task`.
    """
    print(f"Request: {self.request!r}")


