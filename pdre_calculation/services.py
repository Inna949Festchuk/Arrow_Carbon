"""
Сервисы для работы с внешними данными и визуализацией.

В этом модуле размещены классы:
- `DataImportService` — импорт объектов из OSM и GPX;
- `MapVisualizationService` — генерация HTML-карт с ПДРЕ;
- `ParameterCalculationService` — заготовка под расчёт пространственных параметров.
"""
from __future__ import annotations

import os
import zipfile
from typing import List, Dict, Any

import geopandas as gpd
import osmnx as ox
import gpxpy
import folium
from shapely.geometry import shape

from django.contrib.gis.geos import GEOSGeometry
from django.conf import settings

from .models import ProtectedArea, TourismObject, PDREParameter


class DataImportService:
    """
    Сервис импорта пространственных данных для расчёта ПДРЕ.

    Основные источники:
    - OpenStreetMap (через osmnx / Overpass API);
    - GPX-файлы с маршрутами.
    """

    @staticmethod
    def import_osm_features(
        place_name: str,
        tags: Dict[str, Any],
        bounding_polygon: GEOSGeometry | None = None,
    ) -> List[Dict[str, Any]]:
        """
        Импортирует объекты из OpenStreetMap по имени региона и набору тегов.

        :param place_name: строка, описывающая регион поиска (например, "Камчатский край, Россия")
        :param tags: словарь тегов для OSM (например, {"boundary": "protected_area"})
        :param bounding_polygon: опциональный ограничивающий полигон (ООПТ)
        :return: список словарей с геометрией и атрибутами объектов
        """
        try:
            # Настраиваем URL Overpass API (можно заменить на зеркала при необходимости)
            ox.settings.overpass_url = "https://overpass-api.de/api/"

            # Запрашиваем объекты по place_name и тегам
            features = ox.features_from_place(place_name, tags=tags)

            # Если передан ограничивающий полигон — фильтруем объекты по пересечению
            if bounding_polygon:
                shapely_polygon = shape(bounding_polygon.json)
                features = features[features.geometry.intersects(shapely_polygon)]

            results: List[Dict[str, Any]] = []

            for _, row in features.iterrows():
                if row.geometry is None:
                    continue

                # Создаём GeoSeries для перерасчёта в метрическую проекцию
                geom_gdf = gpd.GeoSeries([row.geometry], crs="EPSG:4326").to_crs(epsg=3857)
                geom_projected = geom_gdf.iloc[0]

                result: Dict[str, Any] = {
                    "geometry": row.geometry.wkt,
                    "geometry_type": row.geometry.geom_type,
                    "area_sq_m": None,
                    "length_km": None,
                    "properties": {},
                    "source": "osm",
                }

                # Копируем только интересующие нас атрибуты (ключи тегов)
                for key in tags.keys():
                    if key in row:
                        result["properties"][key] = row.get(key)

                # В зависимости от типа геометрии считаем площадь или длину
                if row.geometry.geom_type in ("Polygon", "MultiPolygon"):
                    result["area_sq_m"] = float(geom_projected.area)
                elif row.geometry.geom_type in ("LineString", "MultiLineString"):
                    result["length_km"] = float(geom_projected.length / 1000.0)

                results.append(result)

            return results
        except Exception as exc:
            # Перехватываем общую ошибку и упаковываем её в понятное сообщение
            raise RuntimeError(f"Ошибка импорта из OSM: {exc}") from exc

    @staticmethod
    def import_gpx_routes(gpx_file_path: str, protected_area: ProtectedArea) -> List[TourismObject]:
        """
        Импортирует маршруты из GPX-файла (или архива .zip с GPX-файлами).
        """
        created_objects: List[TourismObject] = []

        try:
            if gpx_file_path.endswith(".zip"):
                # Если передан ZIP-архив — обрабатываем все GPX-файлы внутри
                with zipfile.ZipFile(gpx_file_path, "r") as z:
                    for filename in z.namelist():
                        if not filename.endswith(".gpx"):
                            continue
                        with z.open(filename) as f:
                            created_objects.extend(
                                DataImportService._process_gpx_file(f, filename, protected_area),
                            )
            else:
                # Обычный одиночный GPX-файл
                with open(gpx_file_path, "r", encoding="utf-8") as f:
                    created_objects.extend(
                        DataImportService._process_gpx_file(f, gpx_file_path, protected_area),
                    )

            return created_objects
        except Exception as exc:
            raise RuntimeError(f"Ошибка импорта GPX: {exc}") from exc

    @staticmethod
    def _process_gpx_file(file_obj, filename: str, protected_area: ProtectedArea) -> List[TourismObject]:
        """
        Обрабатывает один GPX-файл и создаёт объекты `TourismObject` для треков.
        """
        created_objects: List[TourismObject] = []

        # Парсим GPX-структуру
        gpx_data = gpxpy.parse(file_obj)

        for track in gpx_data.tracks:
            for segment in track.segments:
                if len(segment.points) < 2:
                    # Сегмент слишком короткий, пропускаем
                    continue

                # Формируем координаты для LINESTRING (долгота, широта)
                coordinates = [(p.longitude, p.latitude) for p in segment.points]
                coords_str = ", ".join(f"{lon} {lat}" for lon, lat in coordinates)
                line_string = GEOSGeometry(f"LINESTRING({coords_str})", srid=4326)

                # Пересчитываем длину в километрах
                gdf = gpd.GeoSeries([line_string], crs="EPSG:4326").to_crs(epsg=3857)
                length_km = float(gdf.iloc[0].length / 1000.0)

                tourism_object = TourismObject.objects.create(
                    protected_area=protected_area,
                    name=f"{track.name or filename}",
                    object_type="linear",
                    tourism_type="day_trip",
                    geometry=line_string,
                    length_km=length_km,
                    # Простое предположение: скорость ~3 км/ч
                    avg_visit_duration=length_km / 3.0 if length_km > 0 else 1.0,
                    data_source=f"GPX: {filename}",
                )

                created_objects.append(tourism_object)

        return created_objects

    @staticmethod
    def import_protected_areas_from_osm(place_name: str, area_type: str) -> List[ProtectedArea]:
        """
        Импортирует ООПТ из OpenStreetMap.

        :param place_name: регион поиска (строка)
        :param area_type: тип границы в терминах OSM (national_park, nature_reserve, protected_area)
        """
        created_areas: List[ProtectedArea] = []

        tags_map: Dict[str, Dict[str, str]] = {
            "national_park": {"boundary": "national_park"},
            "nature_reserve": {"leisure": "nature_reserve"},
            "protected_area": {"boundary": "protected_area"},
        }

        if area_type not in tags_map:
            raise ValueError(f"Неизвестный тип ООПТ: {area_type}")

        tags = tags_map[area_type]
        features = DataImportService.import_osm_features(place_name, tags)

        for feature in features:
            try:
                protected_area = ProtectedArea.objects.create(
                    name=feature["properties"].get("name", f"ООПТ {area_type}"),
                    area_type="federal" if area_type == "national_park" else "regional",
                    boundary=GEOSGeometry(feature["geometry"], srid=4326),
                    description=feature["properties"].get("description", ""),
                    calculation_parameters={
                        "source": "osm",
                        "tags": tags,
                    },
                )
                created_areas.append(protected_area)
            except Exception:
                # Здесь можно добавить логирование ошибок создания конкретных объектов
                continue

        return created_areas


class MapVisualizationService:
    """
    Сервис визуализации результатов расчёта ПДРЕ.

    Использует библиотеку `folium` для формирования HTML-карт.
    """

    @staticmethod
    def create_pdre_heatmap(protected_area: ProtectedArea, calculation_result: Dict[str, Any]) -> str:
        """
        Создаёт простую HTML-карту с ООПТ и туристскими объектами.

        Возвращает относительный URL к сгенерированному файлу.
        """
        try:
            centroid = protected_area.boundary.centroid
            map_center = [centroid.y, centroid.x]

            # Базовая карта
            folium_map = folium.Map(location=map_center, zoom_start=10)

            # Добавляем границы ООПТ
            folium.GeoJson(
                protected_area.boundary.json,
                name=f"Границы {protected_area.name}",
                style_function=lambda x: {
                    "fillColor": "#00ff00",
                    "color": "#00aa00",
                    "weight": 2,
                    "fillOpacity": 0.1,
                },
            ).add_to(folium_map)

            # Добавляем туристские объекты
            tourism_objects = TourismObject.objects.filter(protected_area=protected_area)

            for obj in tourism_objects:
                color = MapVisualizationService._get_object_color(obj)

                folium.GeoJson(
                    obj.geometry.json,
                    name=obj.name,
                    style_function=lambda x, color=color: {
                        "fillColor": color,
                        "color": color,
                        "weight": 3,
                        "fillOpacity": 0.5,
                    },
                    tooltip=f"{obj.name}<br>ПДРЕ: {obj.pdre_capacity or 'не рассчитан'}",
                ).add_to(folium_map)

            folium.LayerControl().add_to(folium_map)

            # Сохраняем карту в HTML
            map_html = folium_map._repr_html_()
            maps_dir = os.path.join(settings.MEDIA_ROOT, "maps")
            os.makedirs(maps_dir, exist_ok=True)

            filename = f"pdre_map_{protected_area.id}.html"
            map_path = os.path.join(maps_dir, filename)

            with open(map_path, "w", encoding="utf-8") as file:
                file.write(map_html)

            return os.path.join(settings.MEDIA_URL, "maps", filename)
        except Exception as exc:
            raise RuntimeError(f"Ошибка создания карты: {exc}") from exc

    @staticmethod
    def _get_object_color(tourism_object: TourismObject) -> str:
        """
        Возвращает цвет объекта на карте в зависимости от его типа.
        """
        color_map = {
            "areal": "#ff0000",   # красный
            "linear": "#0000ff",  # синий
            "point": "#00ff00",   # зелёный
        }
        return color_map.get(tourism_object.object_type, "#888888")

    @staticmethod
    def create_passport_map(protected_area: ProtectedArea) -> str:
        """
        Заготовка под создание карты для паспорта территории
        (дополнительные подписи, легенды и т.д.).

        Для простоты пока не реализовано.
        """
        raise NotImplementedError("Функция создания карты для паспорта ещё не реализована")


class ParameterCalculationService:
    """
    Сервис расчёта пространственных параметров территории.

    В этом примере методы оставлены как заготовки, чтобы показать архитектуру.
    Реализация может использовать `rasterio`, `numpy`, `scipy` и т.п.
    """

    @staticmethod
    def calculate_slope(dem_raster_path: str, protected_area: ProtectedArea) -> PDREParameter:
        """
        Расчёт уклона территории по цифровой модели рельефа (DEM).

        В данном шаблоне метод не реализован полностью, оставлен для дальнейшей доработки.
        """
        raise NotImplementedError("Расчёт уклона ещё не реализован")

    @staticmethod
    def calculate_vegetation_density(ndvi_raster_path: str, protected_area: ProtectedArea) -> PDREParameter:
        """
        Расчёт плотности растительности по NDVI.
        """
        raise NotImplementedError("Расчёт плотности растительности ещё не реализован")

    @staticmethod
    def calculate_fire_hazard(protected_area: ProtectedArea, weather_data: Dict[str, Any] | None = None) -> PDREParameter:
        """
        Расчёт пожарной опасности на основе погодных данных и других факторов.
        """
        raise NotImplementedError("Расчёт пожарной опасности ещё не реализован")


