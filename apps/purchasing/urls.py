from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.purchasing.views import (
    SupplierViewSet,
    PurchaseOrderViewSet,
    GoodsReceivedNoteViewSet,
    PurchaseInvoiceViewSet,
    PurchasePriceHistoryViewSet,
)

router = DefaultRouter()
router.register("suppliers", SupplierViewSet)
router.register("purchase-orders", PurchaseOrderViewSet)
router.register("grn", GoodsReceivedNoteViewSet)
router.register("invoices", PurchaseInvoiceViewSet)
router.register("price-history", PurchasePriceHistoryViewSet)

urlpatterns = [
    path("", include(router.urls)),
]