# manufacturing/serializers.py
from rest_framework import serializers
from .models import Job, ControlSheet, ControlSheetLine, CutRequirement, CutPlan


class ControlSheetLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ControlSheetLine
        fields = [
            "id", "product", "product_code", "product_name",
            "length_mm", "quantity", "finish", "powder_color",
            "position", "notes",
        ]


class ControlSheetSerializer(serializers.ModelSerializer):
    lines = ControlSheetLineSerializer(many=True, read_only=True)
    job_number = serializers.CharField(source="job.job_number", read_only=True)

    class Meta:
        model = ControlSheet
        fields = [
            "id", "job", "job_number",
            "sheet_number", "name", "status", "is_final",
            "opening_type",
            "width_mm", "height_mm",
            "lock_type", "colour_name", "colour_code", "powder_coat",
            "mesh_type", "has_top_rail", "has_bottom_rail", "rail_width_mm",
            "hardware_notes",
            "signed_off_by", "signed_off_at",
            "lines",
            "created_at",
        ]


class JobSerializer(serializers.ModelSerializer):
    division_code = serializers.CharField(source="division.code", read_only=True)
    cut_design_id = serializers.CharField(source="cut_design.id", read_only=True, allow_null=True)
    control_sheet_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "job_number", "description",
            "customer_name", "customer_ref",
            "division", "division_code",
            "status",
            "cut_design", "cut_design_id",
            "notes",
            "control_sheet_count",
            "created_at",
        ]

    def get_control_sheet_count(self, obj):
        return obj.control_sheets.count()


class GenerateCutRequirementsSerializer(serializers.Serializer):
    """Body for POST /jobs/{id}/generate_requirements/"""
    division_id = serializers.UUIDField()
    offcut_keep_min_mm = serializers.IntegerField(default=150)
