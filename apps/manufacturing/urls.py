from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import JobViewSet, ControlSheetViewSet, CuttingQueueViewSet

router = DefaultRouter()
router.register(r"jobs", JobViewSet, basename="job")
router.register(r"control-sheets", ControlSheetViewSet, basename="control-sheet")
router.register(r"factory", CuttingQueueViewSet, basename="factory")

urlpatterns = [
    path("", include(router.urls)),
]