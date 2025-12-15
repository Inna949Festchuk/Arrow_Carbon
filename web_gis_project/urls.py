"""
Главный маршрутизатор URL для проекта.

Здесь подключаются:
- админ-панель;
- API-приложения (в т.ч. pdre_calculation);
- статические и медиа-файлы в режиме отладки.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path("admin/", admin.site.urls),

    # Подключение API для ПДРЕ
    path("api/pdre/", include("pdre_calculation.urls")),

    # Здесь же вы можете подключить другие приложения:
    # path("api/satellite/", include("satellite_data.urls")),
    # path("api/classification/", include("classification.urls")),
    # path("api/open-data/", include("open_data.urls")),
    # path("api/recreation/", include("recreation_load.urls")),
    # path("api/automation/", include("automation.urls")),
]


# В режиме DEBUG раздаём статические и медиа-файлы через Django
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


