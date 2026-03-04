"""
API URL configuration for the EveryCheese REST API.

Author: Sai Saketh Gooty Kase
"""

from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import DefaultRouter

from .api_views import CheeseViewSet

router = DefaultRouter()
router.register(r"cheeses", CheeseViewSet, basename="cheese")

urlpatterns = [
    path("", include(router.urls)),
    # OpenAPI schema + interactive docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "docs/",
        SpectacularSwaggerView.as_view(url_name="api:schema"),
        name="swagger-ui",
    ),
    path(
        "redoc/",
        SpectacularRedocView.as_view(url_name="api:schema"),
        name="redoc",
    ),
]
