# cutting/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CutDesignViewSet

router = DefaultRouter()
router.register(r"designs", CutDesignViewSet, basename="cutting-design")

urlpatterns = [
    path("", include(router.urls)),
]
