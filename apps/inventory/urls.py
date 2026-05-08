from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.inventory.views import StockItemViewSet, OffcutViewSet

router = DefaultRouter()
router.register("stock-items", StockItemViewSet)
router.register("offcuts", OffcutViewSet)

urlpatterns = [
    path("", include(router.urls)),
]