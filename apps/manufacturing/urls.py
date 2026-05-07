from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, ControlSheetViewSet

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"control-sheets", ControlSheetViewSet, basename="control-sheet")

urlpatterns = [
    path("", include(router.urls)),
]
