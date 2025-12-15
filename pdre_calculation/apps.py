"""
Конфигурация приложения `pdre_calculation`.

Здесь можно подключать сигналы, настраивать поведение при старте приложения.
"""
from django.apps import AppConfig


class PdreCalculationConfig(AppConfig):
    """Класс конфигурации приложения ПДРЕ."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "pdre_calculation"
    verbose_name = "Расчёт ПДРЕ"

    def ready(self) -> None:
        """
        Метод вызывается при готовности приложения.

        Здесь можно импортировать модули с сигналами (signals.py),
        чтобы они были зарегистрированы при старте Django.
        """
        # from . import signals  # пример подключения сигналов
        return None


