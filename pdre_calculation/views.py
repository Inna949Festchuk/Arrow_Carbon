"""
Вьюсеты DRF для работы с сущностями ПДРЕ и запуска расчётов.

Содержит:
- CRUD по ООПТ и туристским объектам;
- просмотр лимитирующих факторов и результатов расчёта;
- вспомогательный API для запуска Celery-задач.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import (
    ProtectedArea,
    TourismObject,
    LimitingFactor,
    PDREParameter,
    CalculationResult,
    TourismPassport,
)
from .serializers import (
    ProtectedAreaSerializer,
    TourismObjectSerializer,
    LimitingFactorSerializer,
    PDREParameterSerializer,
    CalculationResultSerializer,
    TourismPassportSerializer,
    PDREInputSerializer,
    ImportOSMSerializer,
)
from .tasks import (
    calculate_pdre_for_area,
    import_osm_data_task,
    calculate_territory_parameters,
)
from .calculation_methods import PDREMethodology, CalculationInputs


class ProtectedAreaViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с ООПТ (ProtectedArea).

    Включает:
    - стандартные CRUD-операции;
    - дополнительное действие для запуска расчёта ПДРЕ;
    - получение связанных туристских объектов и истории расчётов.
    """

    queryset = ProtectedArea.objects.all().order_by("name")
    serializer_class = ProtectedAreaSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=True, methods=["post"])
    def calculate_pdre(self, request, pk=None):
        """
        Запуск асинхронного расчёта ПДРЕ для выбранной ООПТ.
        """
        protected_area = self.get_object()

        serializer = PDREInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = calculate_pdre_for_area.delay(
            protected_area.id,
            serializer.validated_data.get("calculation_period", "month"),
        )

        return Response(
            {
                "status": "calculation_started",
                "task_id": task.id,
                "message": f"Расчёт ПДРЕ для {protected_area.name} запущен",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=True, methods=["get"])
    def tourism_objects(self, request, pk=None):
        """
        Возвращает список активных туристских объектов для выбранной ООПТ.
        """
        protected_area = self.get_object()
        objects_qs = TourismObject.objects.filter(protected_area=protected_area, is_active=True)
        serializer = TourismObjectSerializer(objects_qs, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def calculation_history(self, request, pk=None):
        """
        История расчётов ПДРЕ для выбранной ООПТ.
        """
        protected_area = self.get_object()
        calculations = CalculationResult.objects.filter(protected_area=protected_area)
        serializer = CalculationResultSerializer(calculations, many=True)
        return Response(serializer.data)


class TourismObjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с туристскими объектами (TourismObject).

    Поддерживает фильтрацию по ООПТ и пересчёт показателей для конкретного объекта.
    """

    queryset = TourismObject.objects.all().order_by("name")
    serializer_class = TourismObjectSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Переопределяем queryset, чтобы добавить фильтрацию по параметру `protected_area`.
        """
        queryset = super().get_queryset()
        protected_area_id = self.request.query_params.get("protected_area")
        if protected_area_id:
            queryset = queryset.filter(protected_area_id=protected_area_id)
        return queryset

    @action(detail=True, methods=["post"])
    def recalculate(self, request, pk=None):
        """
        Пересчитывает показатели емкости (BCC, PCC, RCC) для выбранного объекта.
        """
        tourism_object = self.get_object()

        correction_values = list(tourism_object.correction_factors.values()) if tourism_object.correction_factors else []
        route_segments = (
            tourism_object.correction_factors.get("route_segments", [])
            if tourism_object.correction_factors
            else []
        )

        inputs = CalculationInputs(
            object_type=tourism_object.object_type,
            tourism_type=tourism_object.tourism_type,
            area_sq_m=tourism_object.area_sq_m,
            length_km=tourism_object.length_km,
            area_per_visitor=tourism_object.area_per_visitor,
            operating_hours=tourism_object.operating_hours,
            avg_visit_duration=tourism_object.avg_visit_duration,
            avg_group_size=tourism_object.avg_group_size,
            correction_factors=correction_values,
            management_factor=tourism_object.management_factor,
            route_segments=route_segments,
        )

        results = PDREMethodology.calculate_for_object(inputs)

        tourism_object.return_factor = results["return_factor"]
        tourism_object.base_capacity = results["base_capacity"]
        tourism_object.potential_capacity = results["potential_capacity"]
        tourism_object.pdre_capacity = results["pdre_capacity"]
        tourism_object.save()

        return Response(results)


class LimitingFactorViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с лимитирующими факторами.
    """

    queryset = LimitingFactor.objects.all().order_by("name")
    serializer_class = LimitingFactorSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=["get"])
    def by_type(self, request):
        """
        Дополнительный эндпоинт для фильтрации факторов по типу.
        """
        factor_type = request.query_params.get("type")
        if not factor_type:
            return Response([], status=status.HTTP_200_OK)

        factors = LimitingFactor.objects.filter(factor_type=factor_type)
        serializer = self.get_serializer(factors, many=True)
        return Response(serializer.data)


class CalculationResultViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для просмотра результатов расчёта ПДРЕ.
    """

    queryset = CalculationResult.objects.all().order_by("-calculation_date")
    serializer_class = CalculationResultSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        """
        Поддерживает фильтрацию результатов по ООПТ.
        """
        queryset = super().get_queryset()
        protected_area_id = self.request.query_params.get("protected_area")
        if protected_area_id:
            queryset = queryset.filter(protected_area_id=protected_area_id)
        return queryset


class PDREAPIMixin:
    """
    Миксин с вспомогательными API-методами, не привязанными к конкретной модели.

    Используется в `PDREAPIViewSet`.
    """

    @action(detail=False, methods=["post"])
    def import_osm_data(self, request):
        """
        Запускает асинхронный импорт данных из OSM.
        """
        serializer = ImportOSMSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        task = import_osm_data_task.delay(
            serializer.validated_data["place_name"],
            serializer.validated_data["area_type"],
        )
        return Response(
            {
                "status": "import_started",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"])
    def calculate_territory_parameters(self, request):
        """
        Запускает асинхронный расчёт пространственных параметров территории.
        """
        protected_area_id = request.data.get("protected_area_id")
        if not protected_area_id:
            return Response(
                {"error": "protected_area_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        task = calculate_territory_parameters.delay(protected_area_id)
        return Response(
            {
                "status": "calculation_started",
                "task_id": task.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    @action(detail=False, methods=["post"])
    def quick_calculate(self, request):
        """
        Выполняет быстрый (синхронный) расчёт ПДРЕ без создания записи `CalculationResult`.
        """
        protected_area_id = request.data.get("protected_area_id")
        if not protected_area_id:
            return Response(
                {"error": "protected_area_id обязателен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            results = PDREMethodology.calculate_for_protected_area(int(protected_area_id))
            return Response(results)
        except Exception as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PDREAPIViewSet(PDREAPIMixin, viewsets.GenericViewSet):
    """
    Обобщённый ViewSet для вспомогательных операций вокруг ПДРЕ.

    Не привязан к конкретной модели, используется только для маршрутов миксина.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]


