"""
Реализация основных формул методики расчёта ПДРЕ.

Здесь сосредоточена чистая бизнес-логика без привязки к HTTP/DRF:
- расчёт базовой, потенциальной и предельно допустимой емкости;
- агрегирование результатов по объектам и всей ООПТ.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class CalculationInputs:
    """
    Контейнер входных параметров для расчёта одного туристского объекта.

    Поля максимально близки к тем, что хранятся в модели `TourismObject`.
    """

    object_type: str  # 'areal' или 'linear'
    tourism_type: str  # 'day_trip', 'multi_day', 'autonomous'
    area_sq_m: float | None = None
    length_km: float | None = None
    area_per_visitor: float = 10.0
    operating_hours: float = 8.0
    avg_visit_duration: float = 2.0
    avg_group_size: float = 3.0
    time_unit_days: int = 30  # единица времени (количество дней, например, месяц)
    route_segments: List[Dict[str, Any]] | None = None  # для линейных маршрутов
    correction_factors: List[float] | None = None
    management_factor: float = 0.8


class PDREMethodology:
    """
    Класс с реализацией методики расчёта ПДРЕ по Постановлению №1809.

    Все методы сделаны `@staticmethod`, чтобы их можно было легко вызывать
    из задач Celery, вьюх и тестов без создания экземпляров класса.
    """

    # -----------------------------
    # БАЗОВЫЕ ФУНКЦИИ
    # -----------------------------

    @staticmethod
    def calculate_return_factor(operating_hours: float, avg_visit_duration: float) -> float:
        """
        Расчёт коэффициента возвращения (Rf).

        Формула: Rf = T / Td,
        где:
        - T  — время доступности объекта (часы в сутки),
        - Td — средняя длительность посещения (часы).
        """
        if avg_visit_duration <= 0:
            return 0.0
        return operating_hours / avg_visit_duration

    @staticmethod
    def calculate_base_capacity_areal(inputs: CalculationInputs) -> float:
        """
        Базовая емкость для площадных объектов (BCCqs).

        Упрощённая формула:
            BCC = (A / Au) * Rf * t,
        где:
        - A  — доступная площадь объекта, кв. м;
        - Au — площадь, приходящаяся на одного посетителя, кв. м;
        - Rf — коэффициент возвращения;
        - t  — количество дней в расчётном периоде.
        """
        if not inputs.area_sq_m or inputs.area_per_visitor <= 0:
            return 0.0

        rf = PDREMethodology.calculate_return_factor(
            inputs.operating_hours,
            inputs.avg_visit_duration,
        )

        return (inputs.area_sq_m / inputs.area_per_visitor) * rf * inputs.time_unit_days

    # -----------------------------
    # ЛИНЕЙНЫЕ МАРШРУТЫ
    # -----------------------------

    @staticmethod
    def calculate_base_capacity_linear(inputs: CalculationInputs) -> float:
        """
        Базовая емкость для линейных объектов.

        В зависимости от типа маршрута используются разные формулы:
        - однодневные,
        - многодневные,
        - автономные многодневные маршруты.
        """
        if inputs.tourism_type == "day_trip":
            return PDREMethodology._calculate_bbcqp1(inputs)
        if inputs.tourism_type == "multi_day":
            return PDREMethodology._calculate_bbcqp2(inputs)
        if inputs.tourism_type == "autonomous":
            return PDREMethodology._calculate_bbcqp3(inputs)
        return 0.0

    @staticmethod
    def _calculate_bbcqp1(inputs: CalculationInputs) -> float:
        """
        Базовая емкость для линейных маршрутов без ограничения времени (BCCqp1).

        Здесь предполагается, что туристы могут выходить на маршрут в любое время
        в пределах рабочего интервала.
        """
        if not inputs.route_segments:
            return 0.0

        total_capacity = 0.0
        for segment in inputs.route_segments:
            dtp = segment.get("length_km", 0.0)
            dgp = segment.get("optimal_distance_km", 1.0)
            tdp = segment.get("travel_time_hours", 1.0)
            ts = inputs.operating_hours

            if dgp <= 0 or tdp <= 0:
                continue

            segment_capacity = (dtp / dgp) * (ts / tdp)
            total_capacity += segment_capacity

        days_on_route = max(len(inputs.route_segments), 1)
        return total_capacity * inputs.avg_group_size * (inputs.time_unit_days / days_on_route)

    @staticmethod
    def _calculate_bbcqp2(inputs: CalculationInputs) -> float:
        """
        Базовая емкость для маршрутов с фиксированным временем (BCCqp2).
        """
        if not inputs.route_segments:
            return 0.0

        total_groups = 0.0
        for segment in inputs.route_segments:
            max_groups = PDREMethodology._calculate_max_groups_per_day(
                segment,
                inputs.operating_hours,
            )
            total_groups += max_groups

        days_on_route = max(len(inputs.route_segments), 1)
        return total_groups * inputs.avg_group_size * (inputs.time_unit_days / days_on_route)

    @staticmethod
    def _calculate_bbcqp3(inputs: CalculationInputs) -> float:
        """
        Базовая емкость для автономных маршрутов (BCCqp3).
        """
        if not inputs.route_segments:
            return 0.0

        min_groups = float("inf")
        for segment in inputs.route_segments:
            max_groups = PDREMethodology._calculate_max_groups_per_day(
                segment,
                inputs.operating_hours,
            )
            if max_groups < min_groups:
                min_groups = max_groups

        if min_groups == float("inf"):
            return 0.0

        return min_groups * inputs.avg_group_size * inputs.time_unit_days

    @staticmethod
    def _calculate_max_groups_per_day(segment: Dict[str, Any], operating_hours: float) -> float:
        """
        Расчёт максимального числа групп в день на участке маршрута (gp).
        """
        dgp = segment.get("optimal_distance_km", 1.0)
        tdp = segment.get("travel_time_hours", 1.0)
        vp = segment.get("avg_speed_kmh", 3.0)

        if dgp <= 0 or tdp <= 0:
            return 0.0

        return 1.0 + ((vp * (operating_hours - tdp)) / dgp)

    # -----------------------------
    # ПОТЕНЦИАЛЬНАЯ И ПРЕДЕЛЬНАЯ ЕМКОСТЬ
    # -----------------------------

    @staticmethod
    def calculate_potential_capacity(base_capacity: float, correction_factors: List[float]) -> float:
        """
        Потенциальная рекреационная емкость (PCCq).

        Все поправочные коэффициенты перемножаются и корректируют базовую емкость.
        """
        if not correction_factors:
            return base_capacity

        cf_product = math.prod(correction_factors)
        return base_capacity * cf_product

    @staticmethod
    def calculate_pdre_capacity(potential_capacity: float, management_factor: float) -> float:
        """
        Предельно допустимая емкость объекта (RCCq).
        """
        return potential_capacity * management_factor

    @staticmethod
    def calculate_total_pdre(object_capacities: List[float]) -> float:
        """
        Общая ПДРЕ ООПТ (сумма по всем активным объектам).
        """
        return sum(object_capacities)

    # -----------------------------
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # -----------------------------

    @staticmethod
    def calculate_for_object(inputs: CalculationInputs) -> Dict[str, float]:
        """
        Полный расчёт всех основных показателей для одного объекта.
        """
        results: Dict[str, float] = {}

        # Базовая емкость в зависимости от типа объекта
        if inputs.object_type == "areal":
            base_capacity = PDREMethodology.calculate_base_capacity_areal(inputs)
        else:
            base_capacity = PDREMethodology.calculate_base_capacity_linear(inputs)

        results["base_capacity"] = base_capacity
        results["return_factor"] = PDREMethodology.calculate_return_factor(
            inputs.operating_hours,
            inputs.avg_visit_duration,
        )

        # Потенциальная емкость
        correction_factors = inputs.correction_factors or [1.0]
        potential_capacity = PDREMethodology.calculate_potential_capacity(
            base_capacity,
            correction_factors,
        )
        results["potential_capacity"] = potential_capacity

        # ПДРЕ объекта
        pdre_capacity = PDREMethodology.calculate_pdre_capacity(
            potential_capacity,
            inputs.management_factor,
        )
        results["pdre_capacity"] = pdre_capacity

        return results

    @staticmethod
    def calculate_for_protected_area(protected_area_id: int) -> Dict[str, Any]:
        """
        Расчёт ПДРЕ для всей ООПТ.

        1. Получаем все активные туристские объекты ООПТ.
        2. Для каждого объекта формируем `CalculationInputs` и считаем показатели.
        3. Обновляем связанные модели и возвращаем агрегированный результат.
        """
        from .models import ProtectedArea, TourismObject

        try:
            protected_area = ProtectedArea.objects.get(id=protected_area_id)
        except ProtectedArea.DoesNotExist as exc:
            raise ValueError(f"ООПТ с ID {protected_area_id} не найдена") from exc

        tourism_objects = TourismObject.objects.filter(
            protected_area=protected_area,
            is_active=True,
        )

        total_pdre = 0.0
        object_results: list[Dict[str, Any]] = []

        for obj in tourism_objects:
            # Берём список коэффициентов Cf* из JSON-поля.
            # Если структура сложнее — её можно расширить.
            correction_values = list(obj.correction_factors.values()) if obj.correction_factors else []

            # Для линейных маршрутов сегменты можно хранить в JSON-поле,
            # например, `{"route_segments": [...]}`.
            route_segments = obj.correction_factors.get("route_segments", []) if obj.correction_factors else []

            inputs = CalculationInputs(
                object_type=obj.object_type,
                tourism_type=obj.tourism_type,
                area_sq_m=obj.area_sq_m,
                length_km=obj.length_km,
                area_per_visitor=obj.area_per_visitor,
                operating_hours=obj.operating_hours,
                avg_visit_duration=obj.avg_visit_duration,
                avg_group_size=obj.avg_group_size,
                time_unit_days=30,  # месяц как базовый период
                correction_factors=correction_values,
                management_factor=obj.management_factor,
                route_segments=route_segments,
            )

            results = PDREMethodology.calculate_for_object(inputs)

            # Обновляем объект в БД
            obj.return_factor = results["return_factor"]
            obj.base_capacity = results["base_capacity"]
            obj.potential_capacity = results["potential_capacity"]
            obj.pdre_capacity = results["pdre_capacity"]
            obj.save()

            total_pdre += results["pdre_capacity"]
            object_results.append(
                {
                    "object_id": obj.id,
                    "object_name": obj.name,
                    **results,
                }
            )

        # Сохраняем итоговую ПДРЕ на уровне ООПТ
        protected_area.pdre_value = total_pdre
        protected_area.calculation_method = "methodology_1809"
        protected_area.save()

        return {
            "protected_area_id": protected_area.id,
            "protected_area_name": protected_area.name,
            "total_pdre": total_pdre,
            "object_results": object_results,
            "calculation_date": protected_area.calculation_date,
            "area_ha": protected_area.area_ha,
        }


