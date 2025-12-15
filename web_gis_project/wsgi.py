"""
WSGI-конфигурация для развёртывания Django-проекта.

Используется веб-серверами (gunicorn, uWSGI и др.) для запуска приложения.
"""
import os

from django.core.wsgi import get_wsgi_application

# Указываем путь к модулю настроек
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_gis_project.settings")

application = get_wsgi_application()


