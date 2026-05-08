"""
URL configuration for hos_erp project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/purchasing/", include("apps.purchasing.urls")),
    path("api/cutting/", include("apps.cutting.urls")),
    path("api/manufacturing/", include("apps.manufacturing.urls")),
    path("api/powdercoat/", include("apps.powdercoat.urls")),
    path("api/core/", include("apps.core.urls")),
    path("api/products/", include("apps.products.urls")),
    path("api/inventory/", include("apps.inventory.urls")),
    path("api/sales/", include("apps.sales.urls")),
]
