# powdercoat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import QualityCheckViewSet, PowdercoatSupplierViewSet, PowdercoatJobViewSet, StockIssueViewSet

router = DefaultRouter()
router.register(r"qc-checks", QualityCheckViewSet, basename="qc-check")
router.register(r"suppliers", PowdercoatSupplierViewSet, basename="powdercoat-supplier")
router.register(r"jobs", PowdercoatJobViewSet, basename="powdercoat-job")
router.register(r"stock-issues", StockIssueViewSet, basename="stock-issue")

urlpatterns = [
    path("", include(router.urls)),
]
