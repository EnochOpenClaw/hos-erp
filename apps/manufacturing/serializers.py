# manufacturing/serializers.py
from rest_framework import serializers
from .models import Job, ControlSheet, ControlSheetLine, CutRequirement, CutPlan
from apps.core.models import Division


class ControlSheetLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = ControlSheetLine
        fields = [
            "id", "control_sheet", "product", "product_code", "product_name",
            "length_mm", "quantity", "finish", "powder_color",
            "position", "notes",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        cs = self.context.get("control_sheet")
        if cs:
            validated_data["control_sheet"] = cs
        return ControlSheetLine.objects.create(**validated_data)


class ControlSheetSerializer(serializers.ModelSerializer):
    lines = ControlSheetLineSerializer(many=True, read_only=True)
    job_number = serializers.CharField(source="job.job_number", read_only=True)
    job_status = serializers.CharField(source="job.status", read_only=True)

    class Meta:
        model = ControlSheet
        fields = [
            "id", "job", "job_number", "job_status",
            "sheet_number", "name", "status", "is_final",
            "opening_type",
            "WIDTH_MM", "HEIGHT_MM",
            "lock_type", "colour_name", "colour_code", "powder_coat",
            "mesh_type", "has_top_rail", "has_bottom_rail", "rail_width_mm",
            "hardware_notes",
            "signed_off_by", "signed_off_at",
            "lines",
            "created_at",
        ]
        read_only_fields = ["id", "status", "is_final", "signed_off_by", "signed_off_at", "created_at"]

    def create(self, validated_data):
        lines_data = validated_data.pop("lines", None)
        cs = ControlSheet.objects.create(**validated_data)
        if lines_data:
            for line in lines_data:
                ControlSheetLine.objects.create(control_sheet=cs, **line)
        return cs

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for line in lines_data:
                ControlSheetLine.objects.create(control_sheet=instance, **line)
        return instance


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for the jobs list table."""
    division_code = serializers.CharField(source="division.code", read_only=True)
    control_sheet_count = serializers.SerializerMethodField()
    cut_design_status = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            "id", "job_number", "description",
            "customer_name", "customer_ref",
            "division", "division_code",
            "status", "priority",
            "control_sheet_count", "cut_design_status",
            "notes",
            "created_at",
        ]

    def get_control_sheet_count(self, obj):
        return obj.control_sheets.count()

    def get_cut_design_status(self, obj):
        if obj.cut_design:
            return obj.cut_design.status
        return None


class JobSerializer(serializers.ModelSerializer):
    division_code = serializers.CharField(source="division.code", read_only=True)
    cut_design_id = serializers.CharField(source="cut_design.id", read_only=True, allow_null=True)
    control_sheet_count = serializers.SerializerMethodField()
    control_sheets = ControlSheetSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "job_number", "description",
            "customer_name", "customer_ref",
            "division", "division_code",
            "status", "priority",
            "cut_design", "cut_design_id",
            "notes",
            "control_sheet_count", "control_sheets",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "job_number", "created_at", "updated_at"]

    def get_control_sheet_count(self, obj):
        return obj.control_sheets.count()

    def create(self, validated_data):
        company = self.context.get("company") or __import__("apps.core.models", fromlist=["Company"]).Company.objects.get(name="OpenFactory Systems")
        return Job.objects.create(company=company, **validated_data)


class GenerateCutRequirementsSerializer(serializers.Serializer):
    """Body for POST /jobs/{id}/generate_requirements/"""
    division_id = serializers.UUIDField(required=False)
    offcut_keep_min_mm = serializers.IntegerField(default=150)

    def validate(self, attrs):
        job = self.context.get("job")
        if not job.division and not attrs.get("division_id"):
            raise serializers.ValidationError({"division_id": "Job has no division assigned."})
        return attrs


class CutRequirementSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = CutRequirement
        fields = [
            "id", "product", "product_code", "product_name",
            "cut_length_mm", "qty", "allocated_qty",
            "style", "colour", "colour_code",
        ]