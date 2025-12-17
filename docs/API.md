# API Документация

Документация REST API для проекта Arrow_Carbon.

## Базовый URL

Все API-эндпоинты доступны по адресу:
```
http://localhost:8000/api/pdre/
```

## Аутентификация

По умолчанию API использует базовую аутентификацию Django (Session Authentication и Basic Authentication). Для доступа к защищенным эндпоинтам требуется авторизация.

## Формат ответов

API возвращает данные в формате JSON. Геоданные возвращаются в формате GeoJSON согласно стандарту [GeoJSON](https://geojson.org/).

## Эндпоинты

### ООПТ (Protected Areas)

#### Получить список ООПТ

```http
GET /api/pdre/protected-areas/
```

**Ответ:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "Polygon",
        "coordinates": [[[lon, lat], ...]]
      },
      "properties": {
        "id": 1,
        "name": "Национальный парк",
        "area_type": "federal",
        "area_ha": 1250.5,
        "pdre_value": 1500.0,
        "calculation_date": "2024-01-15T10:00:00Z",
        "description": "Описание ООПТ",
        "cadastral_number": "77:01:0001001:1001"
      }
    }
  ]
}
```

#### Получить конкретную ООПТ

```http
GET /api/pdre/protected-areas/{id}/
```

#### Создать ООПТ

```http
POST /api/pdre/protected-areas/
Content-Type: application/json

{
  "name": "Название ООПТ",
  "area_type": "federal",
  "boundary": {
    "type": "Polygon",
    "coordinates": [[[lon, lat], ...]]
  },
  "description": "Описание",
  "cadastral_number": "77:01:0001001:1001"
}
```

#### Обновить ООПТ

```http
PUT /api/pdre/protected-areas/{id}/
PATCH /api/pdre/protected-areas/{id}/
```

#### Удалить ООПТ

```http
DELETE /api/pdre/protected-areas/{id}/
```

#### Запустить расчет ПДРЕ для ООПТ

```http
POST /api/pdre/protected-areas/{id}/calculate_pdre/
Content-Type: application/json

{
  "calculation_period": "month"
}
```

**Ответ:**
```json
{
  "status": "calculation_started",
  "task_id": "abc123-def456-ghi789",
  "message": "Расчёт ПДРЕ для Национальный парк запущен"
}
```

#### Получить туристские объекты ООПТ

```http
GET /api/pdre/protected-areas/{id}/tourism_objects/
```

**Ответ:**
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "geometry": {
        "type": "LineString",
        "coordinates": [[lon, lat], ...]
      },
      "properties": {
        "id": 1,
        "name": "Туристический маршрут",
        "object_type": "linear",
        "tourism_type": "day_trip",
        "length_km": 5.2,
        "base_capacity": 120.0,
        "potential_capacity": 100.0,
        "pdre_capacity": 80.0,
        "return_factor": 4.0,
        "is_active": true
      }
    }
  ]
}
```

#### Получить историю расчетов ООПТ

```http
GET /api/pdre/protected-areas/{id}/calculation_history/
```

### Туристские объекты (Tourism Objects)

#### Получить список туристских объектов

```http
GET /api/pdre/tourism-objects/
```

**Параметры запроса:**
- `protected_area` (int) — фильтр по ID ООПТ

**Пример:**
```http
GET /api/pdre/tourism-objects/?protected_area=1
```

#### Получить конкретный объект

```http
GET /api/pdre/tourism-objects/{id}/
```

#### Создать туристский объект

```http
POST /api/pdre/tourism-objects/
Content-Type: application/json

{
  "protected_area": 1,
  "name": "Туристический маршрут",
  "object_type": "linear",
  "tourism_type": "day_trip",
  "geometry": {
    "type": "LineString",
    "coordinates": [[lon, lat], ...]
  },
  "length_km": 5.2,
  "area_per_visitor": 10.0,
  "operating_hours": 8.0,
  "avg_visit_duration": 2.0,
  "avg_group_size": 3.0,
  "management_factor": 0.8
}
```

#### Пересчитать показатели объекта

```http
POST /api/pdre/tourism-objects/{id}/recalculate/
```

**Ответ:**
```json
{
  "return_factor": 4.0,
  "base_capacity": 120.0,
  "potential_capacity": 100.0,
  "pdre_capacity": 80.0
}
```

### Лимитирующие факторы (Limiting Factors)

#### Получить список факторов

```http
GET /api/pdre/limiting-factors/
```

#### Получить факторы по типу

```http
GET /api/pdre/limiting-factors/by_type/?type=ecological
```

**Доступные типы:**
- `ecological` — экологический
- `social` — социальный
- `cultural` — социокультурный
- `infrastructure` — инфраструктурный

### Результаты расчетов (Calculation Results)

#### Получить список результатов

```http
GET /api/pdre/calculation-results/
```

**Параметры запроса:**
- `protected_area` (int) — фильтр по ID ООПТ

#### Получить конкретный результат

```http
GET /api/pdre/calculation-results/{id}/
```

**Ответ:**
```json
{
  "id": 1,
  "protected_area": 1,
  "protected_area_name": "Национальный парк",
  "calculation_date": "2024-01-15T10:00:00Z",
  "calculation_period": "month",
  "total_pdre": 1500.0,
  "area_pdre": {
    "Маршрут 1": 500.0,
    "Маршрут 2": 1000.0
  },
  "calculation_details": {
    "protected_area_id": 1,
    "total_pdre": 1500.0,
    "object_results": [...]
  },
  "visualization_url": "/media/maps/pdre_map_1.html",
  "calculation_status": "completed"
}
```

### Вспомогательные эндпоинты

#### Импорт данных из OpenStreetMap

```http
POST /api/pdre/pdre/import_osm_data/
Content-Type: application/json

{
  "place_name": "Камчатский край, Россия",
  "area_type": "national_park"
}
```

**Доступные типы:**
- `national_park` — национальный парк
- `nature_reserve` — природный заповедник
- `protected_area` — охраняемая территория

**Ответ:**
```json
{
  "status": "import_started",
  "task_id": "abc123-def456-ghi789"
}
```

#### Расчет параметров территории

```http
POST /api/pdre/pdre/calculate_territory_parameters/
Content-Type: application/json

{
  "protected_area_id": 1
}
```

**Ответ:**
```json
{
  "status": "calculation_started",
  "task_id": "abc123-def456-ghi789"
}
```

#### Быстрый расчет ПДРЕ

```http
POST /api/pdre/pdre/quick_calculate/
Content-Type: application/json

{
  "protected_area_id": 1
}
```

**Ответ:**
```json
{
  "protected_area_id": 1,
  "protected_area_name": "Национальный парк",
  "total_pdre": 1500.0,
  "object_results": [
    {
      "object_id": 1,
      "object_name": "Маршрут 1",
      "return_factor": 4.0,
      "base_capacity": 500.0,
      "potential_capacity": 400.0,
      "pdre_capacity": 320.0
    }
  ],
  "calculation_date": "2024-01-15T10:00:00Z",
  "area_ha": 1250.5
}
```

## Коды ответов

- `200 OK` — успешный запрос
- `201 Created` — ресурс успешно создан
- `202 Accepted` — запрос принят к обработке (асинхронная задача)
- `400 Bad Request` — неверный запрос
- `401 Unauthorized` — требуется аутентификация
- `403 Forbidden` — недостаточно прав
- `404 Not Found` — ресурс не найден
- `500 Internal Server Error` — внутренняя ошибка сервера

## Обработка ошибок

При возникновении ошибки API возвращает JSON с описанием проблемы:

```json
{
  "error": "Описание ошибки",
  "details": {
    "field_name": ["Сообщение об ошибке"]
  }
}
```

## Примеры использования

### Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000/api/pdre"

# Получить список ООПТ
response = requests.get(f"{BASE_URL}/protected-areas/")
areas = response.json()

# Создать ООПТ
new_area = {
    "name": "Тестовая ООПТ",
    "area_type": "regional",
    "boundary": {
        "type": "Polygon",
        "coordinates": [[[37.0, 55.0], [38.0, 55.0], [38.0, 56.0], [37.0, 56.0], [37.0, 55.0]]]
    }
}
response = requests.post(f"{BASE_URL}/protected-areas/", json=new_area)

# Запустить расчет ПДРЕ
response = requests.post(
    f"{BASE_URL}/protected-areas/1/calculate_pdre/",
    json={"calculation_period": "month"}
)
task_id = response.json()["task_id"]
```

### cURL

```bash
# Получить список ООПТ
curl -X GET http://localhost:8000/api/pdre/protected-areas/

# Создать ООПТ
# curl -X POST http://localhost:8000/api/pdre/protected-areas/ \
#   -H "Content-Type: application/json" \
#   -d '{
#     "name": "Тестовая ООПТ",
#     "area_type": "regional",
#     "boundary": {
#       "type": "Polygon",
#       "coordinates": [[[37.0, 55.0], [38.0, 55.0], [38.0, 56.0], [37.0, 56.0], [37.0, 55.0]]]
#     }
#   }'

# Сначала зарегистрироваться через админпанель -u "user1:password949"
 curl -X POST http://localhost:8000/api/pdre/protected-areas/ \                                                        
  -H "Content-Type: application/json" \
  -u "user1:password949" \
  -d '{                   
    "name": "Тестовая ООПТ",                                                                   
    "area_type": "regional",
    "boundary": "SRID=4326;POLYGON((37.0 55.0, 38.0 55.0, 38.0 56.0, 37.0 56.0, 37.0 55.0))"
  }' 

# Запустить расчет ПДРЕ
curl -X POST http://localhost:8000/api/pdre/protected-areas/1/calculate_pdre/ \
  -H "Content-Type: application/json" \
  -u "user1:password949" \
  -d '{"calculation_period": "month"}'
```

## Мониторинг задач Celery

Для проверки статуса асинхронных задач используйте ID задачи, возвращаемый в ответе. Статус можно проверить через Django admin или напрямую через Celery API (если настроен).

