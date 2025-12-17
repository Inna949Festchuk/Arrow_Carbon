# Модели данных

Подробное описание моделей данных проекта Arrow_Carbon.

## Обзор

Проект использует Django ORM с расширением GeoDjango для работы с пространственными данными. Все модели находятся в приложении `pdre_calculation`.

## Основные модели

### ProtectedArea (ООПТ)

Особо охраняемая природная территория.

**Поля:**
- `id` (BigAutoField) — первичный ключ
- `name` (CharField, max_length=500) — наименование ООПТ
- `area_type` (CharField) — тип ООПТ:
  - `federal` — федеральная
  - `regional` — региональная
  - `local` — местная
- `boundary` (PolygonField, SRID=4326) — границы территории в формате WGS84
- `cadastral_number` (CharField, nullable) — кадастровый номер
- `area_ha` (FloatField, readonly) — площадь в гектарах (вычисляется автоматически)
- `description` (TextField, nullable) — описание
- `calculation_date` (DateTimeField, auto_now_add) — дата последнего расчета
- `pdre_value` (FloatField, nullable) — общая ПДРЕ ООПТ (чел/ед.времени)
- `calculation_method` (CharField, nullable) — метод расчета
- `calculation_parameters` (JSONField) — параметры расчета

**Связи:**
- `tourism_objects` — связанные туристские объекты (ForeignKey)
- `parameters` — параметры территории (ForeignKey)
- `calculations` — результаты расчетов (ForeignKey)
- `passport` — паспорт территории (OneToOne)

**Методы:**
- `save()` — переопределен для автоматического расчета площади

**Пример использования:**
```python
from pdre_calculation.models import ProtectedArea
from django.contrib.gis.geos import Polygon

# Создание ООПТ
area = ProtectedArea.objects.create(
    name="Национальный парк",
    area_type="federal",
    boundary=Polygon(((37.0, 55.0), (38.0, 55.0), (38.0, 56.0), (37.0, 56.0), (37.0, 55.0)), srid=4326)
)
# Площадь автоматически рассчитается при сохранении
print(area.area_ha)
```

### TourismObject (Туристский объект)

Туристский объект на территории ООПТ (маршрут, площадка, точка).

**Поля:**
- `id` (BigAutoField) — первичный ключ
- `protected_area` (ForeignKey -> ProtectedArea) — связанная ООПТ
- `name` (CharField, max_length=500) — наименование
- `object_type` (CharField) — тип объекта:
  - `areal` — площадной объект
  - `linear` — линейный объект (маршрут)
  - `point` — точечный объект
- `tourism_type` (CharField) — тип туризма:
  - `day_trip` — однодневный маршрут
  - `multi_day` — многодневный маршрут
  - `autonomous` — автономный многодневный маршрут
  - `facility` — объект инфраструктуры
- `geometry` (GeometryField, SRID=4326) — геометрия объекта (Point/LineString/Polygon)
- `area_sq_m` (FloatField, nullable) — площадь объекта в кв. метрах
- `length_km` (FloatField, nullable) — длина маршрута в км
- `area_per_visitor` (FloatField, default=10.0) — площадь на одного посетителя (кв. м)
- `operating_hours` (FloatField, default=8.0) — время доступности объекта (часов в сутки)
- `avg_visit_duration` (FloatField, default=2.0) — среднее время посещения (часов)
- `avg_group_size` (FloatField, default=3.0) — средний размер группы (чел.)
- `return_factor` (FloatField, nullable) — коэффициент возвращения (вычисляется)
- `base_capacity` (FloatField, nullable) — базовая емкость BCC (вычисляется)
- `potential_capacity` (FloatField, nullable) — потенциальная емкость PCC (вычисляется)
- `pdre_capacity` (FloatField, nullable) — ПДРЕ объекта RCC (вычисляется)
- `correction_factors` (JSONField) — поправочные коэффициенты Cf1, Cf2, ...
- `management_factor` (FloatField, default=0.8, 0.0-1.0) — коэффициент управленческой емкости MC
- `data_source` (CharField, nullable) — источник данных
- `last_updated` (DateTimeField, auto_now) — последнее обновление
- `is_active` (BooleanField, default=True) — активен ли объект

**Связи:**
- `protected_area` — ООПТ, к которой относится объект

**Пример использования:**
```python
from pdre_calculation.models import TourismObject, ProtectedArea
from django.contrib.gis.geos import LineString

# Создание линейного маршрута
route = TourismObject.objects.create(
    protected_area=area,
    name="Туристический маршрут",
    object_type="linear",
    tourism_type="day_trip",
    geometry=LineString((37.0, 55.0), (37.5, 55.5), srid=4326),
    length_km=5.2,
    area_per_visitor=10.0,
    operating_hours=8.0,
    avg_visit_duration=2.0,
    avg_group_size=3.0
)
```

### LimitingFactor (Лимитирующий фактор)

Фактор, ограничивающий развитие туризма на территории.

**Поля:**
- `id` (BigAutoField) — первичный ключ
- `name` (CharField, max_length=200) — наименование фактора
- `factor_type` (CharField) — тип фактора:
  - `ecological` — экологический
  - `social` — социальный
  - `cultural` — социокультурный
  - `infrastructure` — инфраструктурный
- `description` (TextField) — описание
- `coefficient_value` (FloatField, default=1.0, 0.0-1.0) — значение коэффициента
- `calculation_formula` (TextField, nullable) — формула расчета
- `apply_to_all` (BooleanField, default=True) — применять ко всем ООПТ
- `protected_areas` (ManyToMany -> ProtectedArea) — ООПТ для применения
- `geometry` (GeometryField, nullable) — геометрия влияния фактора

**Пример использования:**
```python
from pdre_calculation.models import LimitingFactor

factor = LimitingFactor.objects.create(
    name="Высокая пожарная опасность",
    factor_type="ecological",
    description="Территория находится в зоне высокой пожарной опасности",
    coefficient_value=0.7,
    apply_to_all=False
)
factor.protected_areas.add(area)
```

### PDREParameter (Параметр территории)

Пространственные параметры для расчета ПДРЕ (уклон, NDVI и т.д.).

**Поля:**
- `id` (BigAutoField) — первичный ключ
- `protected_area` (ForeignKey -> ProtectedArea) — связанная ООПТ
- `parameter_type` (CharField) — тип параметра:
  - `slope` — уклон территории
  - `vegetation_density` — плотность растительности
  - `soil_erosion` — эрозионная опасность
  - `fire_hazard` — пожарная опасность
  - `wetlands` — увлажненность
  - `infrastructure` — близость инфраструктуры
  - `anthropogenic` — антропогенная нагрузка
- `calculation_date` (DateTimeField, auto_now_add) — дата расчета
- `raster_data` (RasterField, nullable) — растровые данные (DEM, NDVI и т.д.)
- `vector_zones` (GeometryCollectionField, nullable) — векторные зоны параметра
- `value_range` (JSONField) — диапазон значений `{'min': 0, 'max': 1, 'mean': 0.5}`
- `data_source` (CharField) — источник данных
- `processing_method` (CharField, nullable) — метод обработки

**Ограничения:**
- `unique_together = ['protected_area', 'parameter_type']` — один параметр каждого типа на ООПТ

### CalculationResult (Результат расчета)

Результат расчета ПДРЕ по территории.

**Поля:**
- `id` (BigAutoField) — первичный ключ
- `protected_area` (ForeignKey -> ProtectedArea) — связанная ООПТ
- `calculation_date` (DateTimeField, auto_now_add) — дата расчета
- `calculation_period` (CharField) — период расчета (месяц, сезон, год)
- `total_pdre` (FloatField) — общая ПДРЕ ООПТ (чел/ед.времени)
- `area_pdre` (JSONField) — ПДРЕ по участкам `{'участок': значение}`
- `calculation_details` (JSONField) — детали расчета
- `input_parameters` (JSONField) — входные параметры
- `heatmap_data` (RasterField, nullable) — растровая тепловая карта
- `visualization_url` (URLField, nullable) — ссылка на визуализацию
- `calculation_status` (CharField, default='completed') — статус:
  - `pending` — в ожидании
  - `processing` — в обработке
  - `completed` — завершено
  - `failed` — ошибка
- `error_message` (TextField, nullable) — сообщение об ошибке

**Сортировка:**
- По умолчанию сортируется по дате расчета (новые первыми)

### TourismPassport (Паспорт территории)

Паспорт территории с результатами расчета ПДРЕ.

**Поля:**
- `id` (BigAutoField) — первичный ключ
- `protected_area` (OneToOne -> ProtectedArea) — связанная ООПТ
- `creation_date` (DateTimeField, auto_now_add) — дата создания
- `valid_until` (DateField) — действителен до
- `version` (CharField, default='1.0') — версия паспорта
- `executive_summary` (TextField) — краткое резюме
- `methodology_description` (TextField) — описание методики
- `calculation_results` (TextField) — результаты расчета
- `recommendations` (TextField) — рекомендации
- `map_image` (ImageField, nullable) — карта
- `charts_data` (JSONField) — данные для графиков
- `document_file` (FileField) — файл паспорта (PDF)
- `approved_by` (CharField, nullable) — утвержден кем
- `is_active` (BooleanField, default=True) — активен ли паспорт

## Связи между моделями

```
ProtectedArea (1) ──< (N) TourismObject
ProtectedArea (1) ──< (N) PDREParameter
ProtectedArea (1) ──< (N) CalculationResult
ProtectedArea (1) ──< (1) TourismPassport
ProtectedArea (N) ──< (N) LimitingFactor (ManyToMany)
```

## Индексы

Для оптимизации запросов созданы следующие индексы:

1. **ProtectedArea:**
   - Пространственный индекс на `boundary`

2. **TourismObject:**
   - Пространственный индекс на `geometry`
   - Составной индекс на `(protected_area, object_type)`

## JSON-поля

### ProtectedArea.calculation_parameters
```json
{
  "source": "osm",
  "tags": {"boundary": "national_park"},
  "calculation_date": "2024-01-15"
}
```

### TourismObject.correction_factors
```json
{
  "Cf1": 0.8,
  "Cf2": 0.9,
  "Cf3": 1.0,
  "route_segments": [
    {
      "length_km": 2.5,
      "optimal_distance_km": 1.0,
      "travel_time_hours": 1.5,
      "avg_speed_kmh": 3.0
    }
  ]
}
```

### PDREParameter.value_range
```json
{
  "min": 0.0,
  "max": 1.0,
  "mean": 0.5,
  "std": 0.2
}
```

### CalculationResult.area_pdre
```json
{
  "Маршрут 1": 500.0,
  "Маршрут 2": 1000.0,
  "Площадка 1": 200.0
}
```

## Миграции

Миграции находятся в `pdre_calculation/migrations/`. При изменении моделей необходимо:

1. Создать миграции:
```bash
python manage.py makemigrations pdre_calculation
```

2. Применить миграции:
```bash
python manage.py migrate
```

## Рекомендации по использованию

1. **Геоданные:** Всегда используйте SRID=4326 (WGS84) для хранения геоданных
2. **Расчеты:** Для расчетов площадей и длин используйте метрическую проекцию (EPSG:3857)
3. **JSON-поля:** Используйте структурированные данные в JSON-полях для гибкости
4. **Индексы:** При добавлении новых полей для фильтрации создавайте индексы
5. **Транзакции:** Используйте транзакции при массовых операциях

