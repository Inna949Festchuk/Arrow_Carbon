#!/usr/bin/env python
"""
Точка входа для управления Django-проектом.
"""
import os
import sys


def main() -> None:
    """Основная функция запуска management-команд Django."""
    # Указываем модуль настроек Django-проекта
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "web_gis_project.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Не удалось импортировать Django. Убедитесь, что оно установлено "
            "и что виртуальное окружение активировано."
        ) from exc
    # Передаём аргументы командной строки Django
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()


