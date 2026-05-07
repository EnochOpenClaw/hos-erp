from django.contrib import admin
from apps.core.models import Company, Division, Location, BinLocation


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "tax_id", "is_active"]
    search_fields = ["name", "code"]


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "division_type", "factory_type", "parent", "is_active"]
    list_filter = ["division_type", "factory_type", "is_active"]
    search_fields = ["name", "code"]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "division", "location_type", "parent", "is_active"]
    list_filter = ["division", "location_type", "is_active"]
    search_fields = ["name", "code"]


@admin.register(BinLocation)
class BinLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "location", "barcode", "is_active"]
    search_fields = ["name", "barcode"]
