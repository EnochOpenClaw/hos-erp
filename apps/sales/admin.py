from django.contrib import admin
from apps.sales.models import Customer, Quote, QuoteLine, SalesOrder, SalesOrderLine

admin.site.register(Customer)
admin.site.register(Quote)
admin.site.register(QuoteLine)
admin.site.register(SalesOrder)
admin.site.register(SalesOrderLine)
