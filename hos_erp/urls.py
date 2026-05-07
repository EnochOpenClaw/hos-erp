"""
URL configuration for hos_erp project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/purchasing/", include("apps.purchasing.urls")),
]
