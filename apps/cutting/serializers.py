# cutting/serializers.py
from rest_framework import serializers
from .models import CutDesign, CutRequirement, CutBar, CutBarCut, Offcut, OffcutConsumeEvent


class CutRequirementSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    remaining_qty = serializers.IntegerField(read_only=True)

    class Meta:
        model = CutRequirement
        fields = [
            "id", "product", "product_code", "product_name",
            "style", "colour", "colour_code",
            "cut_length_mm", "qty", "allocated_qty", "remaining_qty",
        ]


class CutBarCutSerializer(serializers.ModelSerializer):
    item_code = serializers.SerializerMethodField()

    class Meta:
        model = CutBarCut
        fields = ["id", "requirement", "position_mm", "length_mm", "item_id", "item_code"]

    def get_item_code(self, obj):
        if obj.requirement and obj.requirement.product:
            return obj.requirement.product.code
        return f"Item {obj.item_id}"


class CutBarSerializer(serializers.ModelSerializer):
    cuts = CutBarCutSerializer(many=True, read_only=True)
    source_offcut_id = serializers.CharField(source="source_offcut.id", read_only=True, allow_null=True)

    class Meta:
        model = CutBar
        fields = [
            "id", "bar_no", "stock_len_mm", "kerf_mm",
            "trim_start_mm", "trim_end_mm", "offcut_mm",
            "source_offcut_id", "group_key", "cuts",
        ]


class OffcutSerializer(serializers.ModelSerializer):
    bin_label = serializers.CharField(source="bin_location.label", read_only=True, allow_null=True)
    consumed_by_name = serializers.CharField(source="consumed_by.name", read_only=True, allow_null=True)

    class Meta:
        model = Offcut
        fields = [
            "id", "extrusion", "style", "colour", "colour_code",
            "length_mm", "stock_len_mm",
            "bin_location", "bin_label", "location_label", "storage_area",
            "status", "design",
            "source_job_name", "source_job_no",
            "consumed_by", "consumed_by_name", "consumed_date",
        ]


class CutDesignSerializer(serializers.ModelSerializer):
    division_code = serializers.CharField(source="division.code", read_only=True)
    requirements = CutRequirementSerializer(many=True, read_only=True)
    bars = CutBarSerializer(many=True, read_only=True)
    offcuts = OffcutSerializer(many=True, read_only=True)
    bar_plan = serializers.JSONField(read_only=True)

    class Meta:
        model = CutDesign
        fields = [
            "id", "name", "job_no", "division", "division_code",
            "sales_order_line",
            "config_json", "bar_plan_json", "bar_plan",
            "offcut_keep_min_mm", "status", "notes",
            "requirements", "bars", "offcuts",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CutDesignListSerializer(serializers.ModelSerializer):
    division_code = serializers.CharField(source="division.code", read_only=True)
    bar_count = serializers.IntegerField(read_only=True)
    total_bars = serializers.SerializerMethodField()
    total_offcuts = serializers.IntegerField(read_only=True)
    total_cuts = serializers.SerializerMethodField()

    class Meta:
        model = CutDesign
        fields = [
            "id", "name", "job_no", "division", "division_code",
            "status", "offcut_keep_min_mm",
            "bar_count", "total_bars", "total_offcuts", "total_cuts",
            "created_at",
        ]

    def get_total_bars(self, obj):
        return obj.bars.count()

    def get_total_cuts(self, obj):
        return CutBarCut.objects.filter(bar__design=obj).count()


class OptimizeRequestSerializer(serializers.Serializer):
    division_id = serializers.UUIDField()
    sales_order_line_id = serializers.UUIDField(required=False, allow_null=True)
    name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    job_no = serializers.CharField(max_length=30, required=False, allow_blank=True)
    offcut_keep_min_mm = serializers.IntegerField(default=150)
    overrides = serializers.DictField(required=False, default=dict)
