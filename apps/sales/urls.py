from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sales.views import CustomerViewSet, QuoteViewSet, SalesOrderViewSet

router = DefaultRouter()
router.register("customers", CustomerViewSet)
router.register("quotes", QuoteViewSet)
router.register("sales-orders", SalesOrderViewSet)

urlpatterns = [
    path("", include(router.urls)),
]