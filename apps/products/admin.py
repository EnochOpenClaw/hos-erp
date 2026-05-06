from django.contrib import admin
from apps.products.models import MaterialCategory, ExtrusionType, Product

admin.site.register(MaterialCategory)
admin.site.register(ExtrusionType)
admin.site.register(Product)
