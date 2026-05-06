from django.contrib import admin
from apps.core.models import Company, Warehouse, Zone, BinLocation

admin.site.register(Company)
admin.site.register(Warehouse)
admin.site.register(Zone)
admin.site.register(BinLocation)
