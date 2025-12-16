"""
Маршрутизация API для приложения `pdre_calculation`.

Здесь регистрируются ViewSet-ы DRF через роутер.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ProtectedAreaViewSet,
    TourismObjectViewSet,
    LimitingFactorViewSet,
    CalculationResultViewSet,
    PDREAPIViewSet,
)


router = DefaultRouter()
router.register(r"protected-areas", ProtectedAreaViewSet) # регистрация ViewSet ProtectedArea 
router.register(r"tourism-objects", TourismObjectViewSet)
router.register(r"limiting-factors", LimitingFactorViewSet)
router.register(r"calculation-results", CalculationResultViewSet)
router.register(r"pdre", PDREAPIViewSet, basename="pdre")


urlpatterns = [
    path("", include(router.urls)),
]


