"""
Модели приложения `pdre_calculation`.

Здесь описаны основные сущности методики расчёта ПДРЕ:
- `ProtectedArea` — особо охраняемая природная территория (ООПТ);
- `TourismObject` — туристский объект (маршрут / площадка / точка);
- `LimitingFactor` — лимитирующий фактор нагрузки;
- `PDREParameter` — пространственные параметры территории (уклон, NDVI и т.п.);
- `CalculationResult` — результаты расчёта ПДРЕ;
- `TourismPassport` — паспорт территории с обобщением результатов.
"""
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import MinValueValidator, MaxValueValidator


class ProtectedArea(gis_models.Model):
    """
    Особо охраняемая природная территория (ООПТ).

    Содержит:
    - название, тип и границы;
    - автоматически вычисляемую площадь;
    - результаты интегрального расчёта ПДРЕ по территории.
    """

    AREA_TYPES = (
        ("federal", "Федеральная"),
        ("regional", "Региональная"),
        ("local", "Местная"),
    )

    name = gis_models.CharField(
        max_length=500,
        verbose_name="Наименование",
    )
    area_type = gis_models.CharField(
        max_length=50,
        choices=AREA_TYPES,
        verbose_name="Тип ООПТ",
    )
    # Полигон границ территории в системе координат WGS84 (EPSG:4326)
    boundary = gis_models.PolygonField(
        verbose_name="Границы",
        srid=4326,
    )
    cadastral_number = gis_models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Кадастровый номер",
    )
    # Площадь в гектарах (вычисляется автоматически в методе save)
    area_ha = gis_models.FloatField(
        verbose_name="Площадь (га)",
        editable=False,
    )
    description = gis_models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание",
    )

    # Данные для расчёта ПДРЕ
    calculation_date = gis_models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата расчёта",
    )
    pdre_value = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="ПДРЕ ООПТ (чел/ед.времени)",
    )
    calculation_method = gis_models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="Метод расчёта",
    )
    calculation_parameters = models.JSONField(
        default=dict,
        verbose_name="Параметры расчёта",
    )

    objects = gis_models.Manager()

    class Meta:
        verbose_name = "ООПТ"
        verbose_name_plural = "ООПТ"
        indexes = [
            gis_models.Index(fields=["boundary"]),
        ]

    def save(self, *args, **kwargs) -> None:
        """
        Переопределяем сохранение, чтобы автоматически
        пересчитывать площадь территории в гектарах.
        """
        if self.boundary:
            from django.contrib.gis.geos import GEOSGeometry

            # Работаем с оригинальной геометрией, а не копией
            geom = self.boundary
            
            # Если SRID не установлен, устанавливаем по умолчанию
            if geom.srid is None:
                geom.srid = 4326  # WGS84
            
            # Трансформируем в метрическую проекцию
            geom.transform(3857)
            # Площадь в квадратных метрах -> переводим в гектары
            self.area_ha = geom.area / 10_000.0
            
            # Возвращаем обратно в исходную проекцию (если нужно)
            geom.transform(4326)  # или другой исходный SRID

        super().save(*args, **kwargs)
        
    def __str__(self) -> str:
        return f"{self.name} ({self.get_area_type_display()})"


class TourismObject(gis_models.Model):
    """
    Туристский объект на территории ООПТ.

    Может быть:
    - площадным (например, рекреационная площадка);
    - линейным (маршрут, тропа);
    - точечным (видовая точка, стоянка и т.п.).
    """

    OBJECT_TYPES = (
        ("areal", "Площадной объект"),
        ("linear", "Линейный объект (маршрут)"),
        ("point", "Точечный объект"),
    )

    TOURISM_TYPES = (
        ("day_trip", "Однодневный маршрут"),
        ("multi_day", "Многодневный маршрут"),
        ("autonomous", "Автономный многодневный маршрут"),
        ("facility", "Объект инфраструктуры"),
    )

    protected_area = gis_models.ForeignKey(
        ProtectedArea,
        on_delete=gis_models.CASCADE,
        related_name="tourism_objects",
        verbose_name="ООПТ",
    )
    name = gis_models.CharField(
        max_length=500,
        verbose_name="Наименование",
    )
    object_type = gis_models.CharField(
        max_length=50,
        choices=OBJECT_TYPES,
        verbose_name="Тип объекта",
    )
    tourism_type = gis_models.CharField(
        max_length=50,
        choices=TOURISM_TYPES,
        verbose_name="Тип туризма",
    )
    # Общая геометрия объекта (точка / линия / полигон)
    geometry = gis_models.GeometryField(
        verbose_name="Геометрия",
        srid=4326,
    )

    # Площадь и длина используются как исходные данные для формул методики
    area_sq_m = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="Площадь объекта (кв. м)",
    )
    length_km = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="Длина маршрута (км)",
    )
    area_per_visitor = gis_models.FloatField(
        default=10.0,
        verbose_name="Площадь на одного посетителя (кв. м)",
        help_text="Согласно п.18 методики",
    )

    # Временные характеристики работы объекта
    operating_hours = gis_models.FloatField(
        default=8.0,
        verbose_name="Время доступности объекта (часов в сутки)",
    )
    avg_visit_duration = gis_models.FloatField(
        default=2.0,
        verbose_name="Среднее время посещения (часов)",
    )
    avg_group_size = gis_models.FloatField(
        default=3.0,
        verbose_name="Средний размер группы (чел.)",
    )

    # Расчётные поля, которые будут заполняться из методики
    return_factor = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="Коэффициент возвращения",
    )
    base_capacity = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="Базовая емкость (BCC)",
    )
    potential_capacity = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="Потенциальная емкость (PCC)",
    )
    pdre_capacity = gis_models.FloatField(
        blank=True,
        null=True,
        verbose_name="ПДРЕ объекта (RCC)",
    )

    # Поправочные коэффициенты (Cf1, Cf2, ...), а также вспомогательные данные (например, сегменты маршрута)
    correction_factors = models.JSONField(
        default=dict,
        verbose_name="Поправочные коэффициенты",
        help_text="Словарь с коэффициентами Cf1, Cf2, ... и дополнительными параметрами",
    )
    management_factor = gis_models.FloatField(
        default=0.8,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Коэффициент управленческой емкости (MC)",
    )

    # Метаданные
    data_source = gis_models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Источник данных",
    )
    last_updated = gis_models.DateTimeField(
        auto_now=True,
        verbose_name="Последнее обновление",
    )
    is_active = gis_models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    objects = gis_models.Manager()

    class Meta:
        verbose_name = "Туристский объект"
        verbose_name_plural = "Туристские объекты"
        indexes = [
            gis_models.Index(fields=["geometry"]),
            gis_models.Index(fields=["protected_area", "object_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_object_type_display()})"


class LimitingFactor(gis_models.Model):
    """
    Лимитирующий фактор развития туризма.

    Используется для описания факторов:
    - экологических;
    - социальных;
    - социокультурных;
    - инфраструктурных.
    """

    FACTOR_TYPES = (
        ("ecological", "Экологический"),
        ("social", "Социальный"),
        ("cultural", "Социокультурный"),
        ("infrastructure", "Инфраструктурный"),
    )

    name = gis_models.CharField(
        max_length=200,
        verbose_name="Наименование фактора",
    )
    factor_type = gis_models.CharField(
        max_length=50,
        choices=FACTOR_TYPES,
        verbose_name="Тип фактора",
    )
    description = gis_models.TextField(
        verbose_name="Описание",
    )
    coefficient_value = gis_models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        verbose_name="Значение коэффициента",
    )
    calculation_formula = gis_models.TextField(
        blank=True,
        null=True,
        verbose_name="Формула расчёта",
    )

    # Привязка фактора к определённым территориям
    apply_to_all = gis_models.BooleanField(
        default=True,
        verbose_name="Применять ко всем ООПТ",
    )
    protected_areas = gis_models.ManyToManyField(
        ProtectedArea,
        blank=True,
        verbose_name="ООПТ для применения",
    )
    geometry = gis_models.GeometryField(
        blank=True,
        null=True,
        verbose_name="Геометрия влияния",
        help_text="Зона влияния фактора",
    )

    objects = gis_models.Manager()

    class Meta:
        verbose_name = "Лимитирующий фактор"
        verbose_name_plural = "Лимитирующие факторы"

    def __str__(self) -> str:
        return f"{self.name} ({self.get_factor_type_display()})"


class PDREParameter(gis_models.Model):
    """
    Пространственные параметры расчёта ПДРЕ для территории.

    Примеры параметров:
    - уклон;
    - плотность растительности;
    - пожарная опасность и т.д.
    """

    PARAMETER_TYPES = (
        ("slope", "Уклон территории"),
        ("vegetation_density", "Плотность растительности"),
        ("soil_erosion", "Эрозионная опасность"),
        ("fire_hazard", "Пожарная опасность"),
        ("wetlands", "Увлажнённость"),
        ("infrastructure", "Близость инфраструктуры"),
        ("anthropogenic", "Антропогенная нагрузка"),
    )

    protected_area = gis_models.ForeignKey(
        ProtectedArea,
        on_delete=gis_models.CASCADE,
        related_name="parameters",
        verbose_name="ООПТ",
    )
    parameter_type = gis_models.CharField(
        max_length=50,
        choices=PARAMETER_TYPES,
        verbose_name="Тип параметра",
    )
    calculation_date = gis_models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата расчёта",
    )

    # Растровые данные (например, DEM, NDVI)
    from django.contrib.gis.db.models import RasterField  # локальный импорт во избежание циклов

    raster_data = RasterField(
        blank=True,
        null=True,
        verbose_name="Растровые данные",
    )
    # Векторные зоны, отражающие классы параметра
    vector_zones = gis_models.GeometryCollectionField(
        blank=True,
        null=True,
        verbose_name="Векторные зоны",
    )
    value_range = models.JSONField(
        default=dict,
        verbose_name="Диапазон значений",
        help_text="{'min': 0, 'max': 1, 'mean': 0.5}",
    )

    data_source = gis_models.CharField(
        max_length=200,
        verbose_name="Источник данных",
    )
    processing_method = gis_models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Метод обработки",
    )

    objects = gis_models.Manager()

    class Meta:
        verbose_name = "Параметр территории"
        verbose_name_plural = "Параметры территории"
        unique_together = ["protected_area", "parameter_type"]

    def __str__(self) -> str:
        return f"{self.get_parameter_type_display()} для {self.protected_area.name}"


class CalculationResult(gis_models.Model):
    """
    Результат расчёта ПДРЕ по территории.

    Содержит:
    - агрегированную ПДРЕ;
    - распределение нагрузки по участкам;
    - подробные параметры и логи расчёта.
    """

    protected_area = gis_models.ForeignKey(
        ProtectedArea,
        on_delete=gis_models.CASCADE,
        related_name="calculations",
        verbose_name="ООПТ",
    )
    calculation_date = gis_models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата расчёта",
    )
    calculation_period = gis_models.CharField(
        max_length=50,
        verbose_name="Период расчёта",
        help_text="Месяц, сезон, год и др.",
    )

    total_pdre = gis_models.FloatField(
        verbose_name="Общая ПДРЕ ООПТ (чел/ед.времени)",
    )
    area_pdre = models.JSONField(
        default=dict,
        verbose_name="ПДРЕ по участкам",
        help_text="Словарь с распределением ПДРЕ по участкам",
    )

    calculation_details = models.JSONField(
        default=dict,
        verbose_name="Детали расчёта",
        help_text="Подробная информация о каждом этапе расчёта",
    )
    input_parameters = models.JSONField(
        default=dict,
        verbose_name="Входные параметры",
        help_text="Использованные параметры расчёта",
    )

    # Поле для хранения растровой тепловой карты (при необходимости)
    from django.contrib.gis.db.models import RasterField as _RasterField

    heatmap_data = _RasterField(
        blank=True,
        null=True,
        verbose_name="Тепловая карта нагрузки",
    )
    visualization_url = gis_models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на визуализацию",
    )

    calculation_status = gis_models.CharField(
        max_length=50,
        default="completed",
        choices=(
            ("pending", "В ожидании"),
            ("processing", "В обработке"),
            ("completed", "Завершено"),
            ("failed", "Ошибка"),
        ),
        verbose_name="Статус расчёта",
    )
    error_message = gis_models.TextField(
        blank=True,
        null=True,
        verbose_name="Сообщение об ошибке",
    )

    objects = gis_models.Manager()

    class Meta:
        verbose_name = "Результат расчёта ПДРЕ"
        verbose_name_plural = "Результаты расчётов ПДРЕ"
        ordering = ["-calculation_date"]

    def __str__(self) -> str:
        return f"Расчёт ПДРЕ для {self.protected_area.name} от {self.calculation_date.date()}"


class TourismPassport(gis_models.Model):
    """
    Паспорт территории с результатами расчёта ПДРЕ.

    Содержит:
    - краткое описание;
    - основную методику;
    - сводные результаты и рекомендации;
    - файлы отчётов и карты.
    """

    protected_area = gis_models.OneToOneField(
        ProtectedArea,
        on_delete=gis_models.CASCADE,
        related_name="passport",
        verbose_name="ООПТ",
    )

    creation_date = gis_models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
    )
    valid_until = gis_models.DateField(
        verbose_name="Действителен до",
    )
    version = gis_models.CharField(
        max_length=20,
        default="1.0",
        verbose_name="Версия",
    )

    executive_summary = gis_models.TextField(
        verbose_name="Краткое резюме",
    )
    methodology_description = gis_models.TextField(
        verbose_name="Описание методики",
    )
    calculation_results = gis_models.TextField(
        verbose_name="Результаты расчёта",
    )
    recommendations = gis_models.TextField(
        verbose_name="Рекомендации",
    )

    map_image = gis_models.ImageField(
        upload_to="passport_maps/",
        blank=True,
        null=True,
        verbose_name="Карта",
    )
    charts_data = models.JSONField(
        default=dict,
        verbose_name="Данные для графиков",
    )

    document_file = gis_models.FileField(
        upload_to="passport_documents/",
        verbose_name="Файл паспорта (PDF)",
    )

    approved_by = gis_models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Утверждён",
    )
    is_active = gis_models.BooleanField(
        default=True,
        verbose_name="Активен",
    )

    objects = gis_models.Manager()

    class Meta:
        verbose_name = "Паспорт территории"
        verbose_name_plural = "Паспорта территорий"

    def __str__(self) -> str:
        return f"Паспорт {self.protected_area.name} (версия {self.version})"


