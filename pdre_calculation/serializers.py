"""
Сериализаторы DRF для приложения `pdre_calculation`.

Они отвечают за:
- преобразование моделей в JSON (и обратно);
- валидацию входящих данных для расчётов и импорта.
"""
from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer

from .models import (
    ProtectedArea,
    TourismObject,
    LimitingFactor,
    PDREParameter,
    CalculationResult,
    TourismPassport,
)


class ProtectedAreaSerializer(GeoFeatureModelSerializer):
    """
    Сериализатор для модели ООПТ.

    Возвращает геометрию границ (`boundary`) и основные атрибуты.
    """

    class Meta:
        model = ProtectedArea
        geo_field = "boundary"
        fields = [
            "id",
            "name",
            "area_type",
            "area_ha",
            "pdre_value",
            "calculation_date",
            "description",
            "cadastral_number",
        ]


class TourismObjectSerializer(GeoFeatureModelSerializer):
    """
    Сериализатор для туристских объектов.

    Дополнительно выводит название ООПТ, к которой относится объект.
    """

    protected_area_name = serializers.CharField(
        source="protected_area.name",
        read_only=True,
    )

    class Meta:
        model = TourismObject
        geo_field = "geometry"
        fields = [
            "id",
            "name",
            "protected_area",
            "protected_area_name",
            "object_type",
            "tourism_type",
            "area_sq_m",
            "length_km",
            "base_capacity",
            "potential_capacity",
            "pdre_capacity",
            "return_factor",
            "is_active",
            "data_source",
        ]


class LimitingFactorSerializer(serializers.ModelSerializer):
    """
    Сериализатор для лимитирующих факторов.
    """

    class Meta:
        model = LimitingFactor
        fields = "__all__"


class PDREParameterSerializer(GeoFeatureModelSerializer):
    """
    Сериализатор для пространственных параметров территории.

    В качестве геометрии используется поле `vector_zones`.
    """

    class Meta:
        model = PDREParameter
        geo_field = "vector_zones"
        fields = "__all__"


class CalculationResultSerializer(serializers.ModelSerializer):
    """
    Сериализатор для результатов расчёта ПДРЕ.
    """

    protected_area_name = serializers.CharField(
        source="protected_area.name",
        read_only=True,
    )

    class Meta:
        model = CalculationResult
        fields = "__all__"


class TourismPassportSerializer(serializers.ModelSerializer):
    """
    Сериализатор для паспорта территории.
    """

    class Meta:
        model = TourismPassport
        fields = "__all__"


class PDREInputSerializer(serializers.Serializer):
    """
    Входные данные для запуска расчёта ПДРЕ по ООПТ.
    """

    protected_area_id = serializers.IntegerField(required=True)
    calculation_period = serializers.CharField(default="month")
    include_visualization = serializers.BooleanField(default=True)
    recalculate_parameters = serializers.BooleanField(default=False)


class ImportOSMSerializer(serializers.Serializer):
    """
    Параметры импорта данных из OpenStreetMap.
    """

    place_name = serializers.CharField(required=True)
    area_type = serializers.ChoiceField(
        choices=["national_park", "nature_reserve", "protected_area"],
    )
    tags = serializers.JSONField(required=False)


class CalculationResponseSerializer(serializers.Serializer):
    """
    Стандартный ответ API на запрос расчёта ПДРЕ.
    """

    success = serializers.BooleanField()
    total_pdre = serializers.FloatField(required=False)
    map_url = serializers.URLField(required=False)
    calculation_id = serializers.IntegerField(required=False)
    error = serializers.CharField(required=False)


