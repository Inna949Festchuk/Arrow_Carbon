"""
Celery-задачи для асинхронных операций приложения `pdre_calculation`.

Задачи:
- расчёт ПДРЕ для выбранной ООПТ;
- импорт данных из OSM;
- расчёт пространственных параметров;
- генерация паспорта территории.
"""
from __future__ import annotations

from typing import Dict, Any

from celery import shared_task
from django.db import transaction
import logging

from .models import ProtectedArea, CalculationResult
from .calculation_methods import PDREMethodology
from .services import DataImportService, MapVisualizationService

logger = logging.getLogger(__name__)


@shared_task
def calculate_pdre_for_area(protected_area_id: int, period: str = "month") -> Dict[str, Any]:
    """
    Асинхронная задача Celery для расчёта ПДРЕ по конкретной ООПТ.
    """
    logger.info("Запуск расчёта ПДРЕ для ООПТ id=%s", protected_area_id)

    # Оборачиваем логику в транзакцию на случай ошибок
    with transaction.atomic():
        calculation_result = CalculationResult.objects.create(
            protected_area_id=protected_area_id,
            calculation_period=period,
            calculation_status="processing",
        )

        try:
            # Основной расчёт
            results = PDREMethodology.calculate_for_protected_area(protected_area_id)
            protected_area = ProtectedArea.objects.get(id=protected_area_id)

            # Создаём визуализацию (простую HTML-карту)
            map_url = MapVisualizationService.create_pdre_heatmap(protected_area, results)

            # Заполняем модель результата
            calculation_result.total_pdre = results["total_pdre"]
            calculation_result.area_pdre = {
                obj["object_name"]: obj["pdre_capacity"] for obj in results["object_results"]
            }
            calculation_result.calculation_details = results
            calculation_result.visualization_url = map_url
            calculation_result.calculation_status = "completed"
            calculation_result.save()

            logger.info(
                "Расчёт ПДРЕ завершён для ООПТ id=%s, итого: %s",
                protected_area_id,
                results["total_pdre"],
            )

            return {
                "success": True,
                "protected_area_id": protected_area_id,
                "total_pdre": results["total_pdre"],
                "map_url": map_url,
                "calculation_id": calculation_result.id,
            }
        except Exception as exc:
            logger.exception("Ошибка расчёта ПДРЕ для ООПТ id=%s: %s", protected_area_id, exc)
            calculation_result.calculation_status = "failed"
            calculation_result.error_message = str(exc)
            calculation_result.save()

            return {
                "success": False,
                "error": str(exc),
                "protected_area_id": protected_area_id,
            }


@shared_task
def import_osm_data_task(place_name: str, area_type: str) -> Dict[str, Any]:
    """
    Асинхронная задача импорта данных ООПТ из OpenStreetMap.
    """
    try:
        logger.info("Начат импорт OSM для %s (%s)", place_name, area_type)
        imported_areas = DataImportService.import_protected_areas_from_osm(place_name, area_type)

        return {
            "success": True,
            "imported_count": len(imported_areas),
            "imported_areas": [area.id for area in imported_areas],
        }
    except Exception as exc:
        logger.exception("Ошибка импорта OSM: %s", exc)
        return {
            "success": False,
            "error": str(exc),
        }


@shared_task
def calculate_territory_parameters(protected_area_id: int) -> Dict[str, Any]:
    """
    Заготовка под асинхронный расчёт параметров территории.

    В текущем шаблоне фактические расчёты не реализованы,
    но структура задачи оставлена для последующей доработки.
    """
    try:
        logger.info("Запуск расчёта параметров для ООПТ id=%s", protected_area_id)
        ProtectedArea.objects.get(id=protected_area_id)

        # Здесь можно вызвать методы ParameterCalculationService
        # для рассчёта уклона, NDVI, пожарной опасности и т.д.

        return {
            "success": True,
            "protected_area_id": protected_area_id,
            "parameters_calculated": [],
        }
    except Exception as exc:
        logger.exception("Ошибка расчёта параметров для ООПТ id=%s: %s", protected_area_id, exc)
        return {
            "success": False,
            "error": str(exc),
        }


@shared_task
def generate_tourism_passport(protected_area_id: int) -> Dict[str, Any]:
    """
    Заготовка под генерацию PDF-паспорта территории.

    В этой задаче можно:
    - собрать данные из `CalculationResult` и `TourismPassport`;
    - сформировать PDF (например, с помощью ReportLab / WeasyPrint);
    - сохранить файл и обновить модель `TourismPassport`.
    """
    try:
        logger.info("Генерация паспорта для ООПТ id=%s", protected_area_id)
        # Реализация не добавлена в данном примере.
        raise NotImplementedError("Генерация паспорта ещё не реализована")
    except Exception as exc:
        logger.exception("Ошибка генерации паспорта для ООПТ id=%s: %s", protected_area_id, exc)
        return {
            "success": False,
            "error": str(exc),
        }


