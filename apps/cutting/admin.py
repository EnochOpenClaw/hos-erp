# cutting/admin.py
from django.contrib import admin
from .models import CutDesign, CutRequirement, CutBar, CutBarCut, Offcut, OffcutConsumeEvent


class CutRequirementInline(admin.TabularInline):
    model = CutRequirement
    extra = 0
    readonly_fields = ["allocated_qty"]


class CutBarInline(admin.TabularInline):
    model = CutBar
    extra = 0
    readonly_fields = ["offcut_mm"]
    show_change_link = True


class CutBarCutInline(admin.TabularInline):
    model = CutBarCut
    extra = 0
    readonly_fields = ["position_mm", "length_mm", "item_id"]


class OffcutInline(admin.TabularInline):
    model = Offcut
    fk_name = "design"
    extra = 0
    readonly_fields = [
        "extrusion", "length_mm", "stock_len_mm", "style",
        "colour", "colour_code", "status", "bin_location",
    ]
    can_delete = False
    max_num = 0


@admin.register(CutDesign)
class CutDesignAdmin(admin.ModelAdmin):
    list_display = ["name", "job_no", "division", "status", "offcut_keep_min_mm", "created_at"]
    list_filter = ["status", "division"]
    search_fields = ["name", "job_no"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [CutRequirementInline, CutBarInline, OffcutInline]


@admin.register(CutRequirement)
class CutRequirementAdmin(admin.ModelAdmin):
    list_display = ["id", "design", "product", "cut_length_mm", "qty", "remaining_qty", "allocated_qty"]
    list_filter = ["design__division"]
    readonly_fields = ["id", "created_at", "updated_at", "allocated_qty", "remaining_qty"]


@admin.register(CutBar)
class CutBarAdmin(admin.ModelAdmin):
    list_display = ["bar_no", "design", "stock_len_mm", "offcut_mm", "source_offcut"]
    list_filter = ["design__division"]
    inlines = [CutBarCutInline]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(CutBarCut)
class CutBarCutAdmin(admin.ModelAdmin):
    list_display = ["bar", "requirement", "position_mm", "length_mm", "item_id"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Offcut)
class OffcutAdmin(admin.ModelAdmin):
    list_display = [
        "extrusion", "length_mm", "stock_len_mm", "style",
        "colour", "colour_code", "status", "bin_location", "design",
    ]
    list_filter = ["status", "extrusion", "design__division"]
    search_fields = ["extrusion", "colour", "colour_code"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(OffcutConsumeEvent)
class OffcutConsumeEventAdmin(admin.ModelAdmin):
    list_display = ["offcut", "design", "requirement", "qty", "created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
