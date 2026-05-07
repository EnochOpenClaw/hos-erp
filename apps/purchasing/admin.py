from django.contrib import admin
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderLine, GoodsReceivedNote, GoodsReceivedNoteLine


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "email", "lead_time_days", "is_active"]
    search_fields = ["name", "code"]


class PurchaseOrderLineInline(admin.TabularInline):
    model = PurchaseOrderLine
    extra = 1


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ["po_number", "division", "supplier", "status", "order_date", "expected_date"]
    list_filter = ["division", "status", "order_date"]
    search_fields = ["po_number", "supplier__name"]
    inlines = [PurchaseOrderLineInline]


@admin.register(GoodsReceivedNote)
class GoodsReceivedNoteAdmin(admin.ModelAdmin):
    list_display = ["grn_number", "po", "received_date", "status"]
    list_filter = ["status", "received_date"]
    search_fields = ["grn_number", "po__po_number"]
