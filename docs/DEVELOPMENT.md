# Руководство по разработке

Руководство для разработчиков проекта Arrow_Carbon.

## Настройка окружения разработки

### Требования

- Python 3.11+
- PostgreSQL 14+ с PostGIS 3.4+
- Redis 7+
- GDAL, GEOS, PROJ (системные библиотеки)
- Docker и Docker Compose (опционально)

### Установка системных зависимостей

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    postgresql-14 \
    postgresql-14-postgis-3 \
    postgresql-contrib \
    redis-server \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    libpq-dev \
    build-essential
```

#### macOS

```bash
brew install python@3.11
brew install postgresql@14
brew install postgis
brew install redis
brew install gdal
brew install geos
brew install proj
```

### Создание виртуального окружения

```bash
python3.11 -m venv venv
source venv/bin/activate  # Linux/macOS
# или
venv\Scripts\activate  # Windows
```

### Установка Python-зависимостей

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Настройка базы данных

1. Создайте базу данных:
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE pdre_db;
CREATE USER pdre_user WITH PASSWORD 'pdre_password';
GRANT ALL PRIVILEGES ON DATABASE pdre_db TO pdre_user;
\c pdre_db
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
\q
```

2. Настройте переменные окружения:
```bash
export POSTGRES_DB=pdre_db
export POSTGRES_USER=pdre_user
export POSTGRES_PASSWORD=pdre_password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
```

### Настройка Django

1. Выполните миграции:
```bash
python manage.py migrate
```

2. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

3. Запустите сервер разработки:
```bash
python manage.py runserver
```

### Настройка Celery

1. Запустите Redis:
```bash
redis-server
```

2. В отдельном терминале запустите Celery worker:
```bash
celery -A web_gis_project worker -l info
```

3. В еще одном терминале запустите Celery beat:
```bash
celery -A web_gis_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## Структура кода

### Стиль кода

Проект следует PEP 8 с некоторыми исключениями:
- Максимальная длина строки: 100 символов
- Использование type hints где возможно
- Docstrings для всех функций и классов

### Организация файлов

```
pdre_calculation/
├── __init__.py
├── admin.py              # Регистрация моделей в админке
├── apps.py               # Конфигурация приложения
├── models.py             # Модели данных
├── views.py              # API ViewSets
├── serializers.py        # DRF сериализаторы
├── urls.py               # URL-маршруты
├── services.py           # Бизнес-логика (импорт, визуализация)
├── calculation_methods.py # Методика расчета ПДРЕ
├── tasks.py              # Celery-задачи
├── tests.py              # Тесты (заготовка)
└── migrations/           # Миграции БД
```

### Добавление новой функциональности

#### 1. Добавление новой модели

```python
# pdre_calculation/models.py
from django.contrib.gis.db import models as gis_models

class NewModel(gis_models.Model):
    name = gis_models.CharField(max_length=200)
    geometry = gis_models.GeometryField(srid=4326)
    
    class Meta:
        verbose_name = "Новая модель"
        verbose_name_plural = "Новые модели"
```

Создайте миграции:
```bash
python manage.py makemigrations pdre_calculation
python manage.py migrate
```

#### 2. Добавление API эндпоинта

```python
# pdre_calculation/serializers.py
class NewModelSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = NewModel
        geo_field = "geometry"
        fields = "__all__"

# pdre_calculation/views.py
class NewModelViewSet(viewsets.ModelViewSet):
    queryset = NewModel.objects.all()
    serializer_class = NewModelSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

# pdre_calculation/urls.py
router.register(r"new-models", NewModelViewSet)
```

#### 3. Добавление Celery-задачи

```python
# pdre_calculation/tasks.py
from celery import shared_task

@shared_task
def new_task(param1: str, param2: int) -> dict:
    """Описание задачи."""
    # Логика задачи
    return {"status": "success"}
```

## Тестирование

### Написание тестов

Создайте тесты в `pdre_calculation/tests.py`:

```python
from django.test import TestCase
from django.contrib.gis.geos import Polygon
from pdre_calculation.models import ProtectedArea
from pdre_calculation.calculation_methods import PDREMethodology

class ProtectedAreaTestCase(TestCase):
    def setUp(self):
        self.area = ProtectedArea.objects.create(
            name="Тестовая ООПТ",
            area_type="federal",
            boundary=Polygon(((0, 0), (1, 0), (1, 1), (0, 1), (0, 0)), srid=4326)
        )
    
    def test_area_calculation(self):
        self.assertIsNotNone(self.area.area_ha)
        self.assertGreater(self.area.area_ha, 0)
```

### Запуск тестов

```bash
# Все тесты
python manage.py test

# Конкретное приложение
python manage.py test pdre_calculation

# Конкретный тест
python manage.py test pdre_calculation.tests.ProtectedAreaTestCase
```

## Отладка

### Django Debug Toolbar

Для разработки можно установить Django Debug Toolbar:

```bash
pip install django-debug-toolbar
```

Добавьте в `settings.py`:
```python
INSTALLED_APPS = [
    # ...
    'debug_toolbar',
]

MIDDLEWARE = [
    # ...
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

INTERNAL_IPS = ['127.0.0.1']
```

### Логирование

Настройте логирование в `settings.py`:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'pdre_calculation': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### Отладка Celery

Для мониторинга Celery используйте Flower:

```bash
pip install flower
celery -A web_gis_project flower
```

Откройте http://localhost:5555

## Работа с геоданными

### Импорт данных

#### Из OpenStreetMap

```python
from pdre_calculation.services import DataImportService
from django.contrib.gis.geos import GEOSGeometry

features = DataImportService.import_osm_features(
    place_name="Камчатский край, Россия",
    tags={"boundary": "national_park"}
)
```

#### Из GPX-файла

```python
from pdre_calculation.services import DataImportService
from pdre_calculation.models import ProtectedArea

objects = DataImportService.import_gpx_routes(
    gpx_file_path="routes.gpx",
    protected_area=area
)
```

### Работа с геометрией

```python
from django.contrib.gis.geos import Polygon, Point, LineString

# Создание полигона
polygon = Polygon(((37.0, 55.0), (38.0, 55.0), (38.0, 56.0), (37.0, 56.0), (37.0, 55.0)), srid=4326)

# Трансформация в метрическую проекцию
polygon.transform(3857)
area_sq_m = polygon.area

# Обратная трансформация
polygon.transform(4326)
```

### Работа с растровыми данными

```python
import rasterio
from rasterio.warp import calculate_default_transform, reproject

# Открытие растрового файла
with rasterio.open('dem.tif') as src:
    data = src.read(1)
    transform = src.transform
    crs = src.crs
```

## Производительность

### Оптимизация запросов

Используйте `select_related` и `prefetch_related`:

```python
# Плохо
objects = TourismObject.objects.all()
for obj in objects:
    print(obj.protected_area.name)  # N+1 запросов

# Хорошо
objects = TourismObject.objects.select_related('protected_area')
for obj in objects:
    print(obj.protected_area.name)  # 1 запрос
```

### Кэширование

```python
from django.core.cache import cache

# Сохранение в кэш
cache.set('key', value, timeout=3600)

# Получение из кэша
value = cache.get('key')
```

### Массовые операции

Используйте `bulk_create` и `bulk_update`:

```python
objects = [TourismObject(...) for _ in range(100)]
TourismObject.objects.bulk_create(objects)
```

## Git workflow

### Ветвление

- `main` — стабильная версия
- `develop` — разработка
- `feature/feature-name` — новая функциональность
- `bugfix/bug-name` — исправление багов

### Коммиты

Используйте понятные сообщения коммитов:

```
feat: добавлен импорт данных из GPX
fix: исправлен расчет площади для полигонов
docs: обновлена документация API
refactor: рефакторинг calculation_methods.py
```

## Деплой

### Подготовка к продакшену

1. Измените `DEBUG = False` в `settings.py`
2. Настройте `ALLOWED_HOSTS`
3. Используйте сильный `SECRET_KEY`
4. Настройте статические файлы:
```python
STATIC_ROOT = '/var/www/static/'
MEDIA_ROOT = '/var/www/media/'
```

5. Используйте Gunicorn или uWSGI вместо runserver

### Docker Compose для продакшена

Создайте `docker-compose.prod.yml` с настройками для продакшена:
- Nginx как reverse proxy
- Gunicorn для Django
- SSL сертификаты
- Резервное копирование БД

## Полезные команды

```bash
# Создание миграций
python manage.py makemigrations

# Применение миграций
python manage.py migrate

# Создание суперпользователя
python manage.py createsuperuser

# Django shell
python manage.py shell

# Сбор статических файлов
python manage.py collectstatic

# Проверка кода
flake8 .
black --check .
mypy .

# Запуск тестов с покрытием
coverage run --source='.' manage.py test
coverage report
```

## Полезные ссылки

- [Django документация](https://docs.djangoproject.com/)
- [GeoDjango документация](https://docs.djangoproject.com/en/stable/ref/contrib/gis/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Celery документация](https://docs.celeryproject.org/)
- [PostGIS документация](https://postgis.net/documentation/)

