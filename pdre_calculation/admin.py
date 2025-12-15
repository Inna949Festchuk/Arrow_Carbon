"""
Регистрация моделей приложения `pdre_calculation` в админ-панели Django.

Используется GeoDjango-админка для отображения геометрий на карте.
"""
from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import (
    ProtectedArea,
    TourismObject,
    LimitingFactor,
    PDREParameter,
    CalculationResult,
    TourismPassport,
)


@admin.register(ProtectedArea)
class ProtectedAreaAdmin(GISModelAdmin):
    """
    Админ-класс для модели ООПТ.
    """

    list_display = ("name", "area_type", "area_ha", "pdre_value", "calculation_date")
    list_filter = ("area_type", "calculation_date")
    search_fields = ("name", "cadastral_number")
    readonly_fields = ("area_ha",)


@admin.register(TourismObject)
class TourismObjectAdmin(GISModelAdmin):
    """
    Админ-класс для туристских объектов.
    """

    list_display = ("name", "protected_area", "object_type", "pdre_capacity", "is_active")
    list_filter = ("object_type", "tourism_type", "is_active")
    search_fields = ("name", "protected_area__name")
    raw_id_fields = ("protected_area",)


@admin.register(LimitingFactor)
class LimitingFactorAdmin(admin.ModelAdmin):
    """
    Админ-класс для лимитирующих факторов.
    """

    list_display = ("name", "factor_type", "coefficient_value", "apply_to_all")
    list_filter = ("factor_type", "apply_to_all")
    filter_horizontal = ("protected_areas",)


@admin.register(PDREParameter)
class PDREParameterAdmin(GISModelAdmin):
    """
    Админ-класс для пространственных параметров территории.
    """

    list_display = ("protected_area", "parameter_type", "calculation_date", "data_source")
    list_filter = ("parameter_type", "data_source")
    raw_id_fields = ("protected_area",)


@admin.register(CalculationResult)
class CalculationResultAdmin(admin.ModelAdmin):
    """
    Админ-класс для результатов расчёта ПДРЕ.
    """

    list_display = ("protected_area", "calculation_date", "total_pdre", "calculation_status")
    list_filter = ("calculation_status", "calculation_date")
    search_fields = ("protected_area__name",)
    readonly_fields = ("calculation_details", "input_parameters")


@admin.register(TourismPassport)
class TourismPassportAdmin(admin.ModelAdmin):
    """
    Админ-класс для паспортов территорий.
    """

    list_display = ("protected_area", "version", "valid_until", "is_active")
    list_filter = ("is_active", "version")
    search_fields = ("protected_area__name",)


