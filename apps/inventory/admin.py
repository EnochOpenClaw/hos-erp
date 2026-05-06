from django.contrib import admin
from apps.inventory.models import StockItem, Offcut

admin.site.register(StockItem)
admin.site.register(Offcut)
