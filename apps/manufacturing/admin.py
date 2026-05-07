from django.contrib import admin
from .models import (
    Job, ControlSheet, ControlSheetLine,
    CutRequirement, CutPlan, CutPlanBar, BOM, BOMLine,
)


class ControlSheetLineInline(admin.TabularInline):
    model = ControlSheetLine
    extra = 1


class ControlSheetInline(admin.TabularInline):
    model = ControlSheet
    extra = 0
    readonly_fields = ["sheet_number"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["job_number", "division", "customer_name", "status", "created_at"]
    list_filter = ["status", "division"]
    search_fields = ["job_number", "customer_name"]
    readonly_fields = ["id", "job_number", "created_at"]
    inlines = [ControlSheetInline]


@admin.register(ControlSheet)
class ControlSheetAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "sheet_number", "name", "status", "is_final", "signed_off_by"]
    list_filter = ["status", "opening_type", "powder_coat"]
    search_fields = ["name", "job__job_number"]
    readonly_fields = ["id", "created_at"]
    inlines = [ControlSheetLineInline]


@admin.register(ControlSheetLine)
class ControlSheetLineAdmin(admin.ModelAdmin):
    list_display = ["id", "control_sheet", "product", "length_mm", "quantity", "finish", "position"]
    list_filter = ["finish", "position"]
    search_fields = ["product__code", "product__name"]


@admin.register(CutRequirement)
class CutRequirementAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "product", "cut_length_mm", "qty", "allocated_qty", "colour"]
    list_filter = ["allow_offcut_match"]
    search_fields = ["product__code"]


@admin.register(CutPlan)
class CutPlanAdmin(admin.ModelAdmin):
    list_display = ["id", "job", "group_key", "bars_used", "waste_pct", "status"]
    list_filter = ["status"]


@admin.register(CutPlanBar)
class CutPlanBarAdmin(admin.ModelAdmin):
    list_display = ["id", "cut_plan", "bar_length_mm", "offcut_mm"]


@admin.register(BOM)
class BOMAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "version", "is_active"]


@admin.register(BOMLine)
class BOMLineAdmin(admin.ModelAdmin):
    list_display = ["id", "bom", "product", "quantity", "length_mm", "finish"]
