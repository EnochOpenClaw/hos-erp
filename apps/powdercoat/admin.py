# powdercoat/admin.py
from django.contrib import admin
from .models import (
    QualityCheck, PowdercoatSupplier, PowdercoatJob,
    PowdercoatJobItem, StockIssue, StockIssueLine,
)


class PowdercoatJobItemInline(admin.TabularInline):
    model = PowdercoatJobItem
    extra = 0
    readonly_fields = ["extrusion", "style", "length_mm", "qc_result"]


class QualityCheckInline(admin.TabularInline):
    model = QualityCheck
    extra = 0
    readonly_fields = ["check_type", "result", "checked_by", "check_date", "notes"]


class StockIssueLineInline(admin.TabularInline):
    model = StockIssueLine
    extra = 0
    readonly_fields = ["product_code", "extrusion", "style", "colour", "length_mm", "quantity", "qc_result"]


@admin.register(QualityCheck)
class QualityCheckAdmin(admin.ModelAdmin):
    list_display = ["id", "check_type", "result", "stock_item", "powdercoat_job", "checked_by", "check_date"]
    list_filter = ["check_type", "result"]
    search_fields = ["notes", "checked_by"]
    readonly_fields = ["id", "check_date"]


@admin.register(PowdercoatSupplier)
class PowdercoatSupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "email", "phone", "lead_time_days", "is_active"]
    search_fields = ["name", "code"]


@admin.register(PowdercoatJob)
class PowdercoatJobAdmin(admin.ModelAdmin):
    list_display = ["job_number", "division", "supplier", "powder_color", "status", "sent_date", "due_date"]
    list_filter = ["status", "division", "supplier"]
    search_fields = ["job_number", "powder_color"]
    readonly_fields = ["id", "job_number", "created_at"]
    inlines = [PowdercoatJobItemInline, QualityCheckInline]


@admin.register(PowdercoatJobItem)
class PowdercoatJobItemAdmin(admin.ModelAdmin):
    list_display = ["job", "stock_item", "extrusion", "length_mm", "quantity", "qc_result"]
    list_filter = ["qc_result", "job__division"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(StockIssue)
class StockIssueAdmin(admin.ModelAdmin):
    list_display = ["issue_number", "division", "receiving_location", "status", "issued_date", "issued_by"]
    list_filter = ["status", "division"]
    search_fields = ["issue_number"]
    readonly_fields = ["id", "issue_number", "created_at"]
    inlines = [StockIssueLineInline]
