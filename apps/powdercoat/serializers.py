# powdercoat/serializers.py
from rest_framework import serializers
from .models import (
    QualityCheck, PowdercoatSupplier, PowdercoatJob,
    PowdercoatJobItem, StockIssue, StockIssueLine, QualityCheckType,
)


class QualityCheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = QualityCheck
        fields = [
            "id", "check_type", "result",
            "stock_item", "powdercoat_job",
            "checked_by", "check_date",
            "notes", "fail_reason", "condition",
        ]
        read_only_fields = ["id", "check_date"]


class PowdercoatJobItemSerializer(serializers.ModelSerializer):
    stock_item_barcode = serializers.CharField(source="stock_item.barcode", read_only=True, allow_null=True)

    class Meta:
        model = PowdercoatJobItem
        fields = [
            "id", "stock_item", "stock_item_barcode",
            "extrusion", "style", "length_mm", "quantity",
            "sent_state", "returned_state", "qc_result", "notes",
        ]


class PowdercoatJobSerializer(serializers.ModelSerializer):
    items = PowdercoatJobItemSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    division_code = serializers.CharField(source="division.code", read_only=True)
    qc_checks = QualityCheckSerializer(many=True, read_only=True)

    class Meta:
        model = PowdercoatJob
        fields = [
            "id", "job_number", "division", "division_code",
            "supplier", "supplier_name",
            "powder_color", "powder_color_code",
            "sent_date", "due_date", "returned_date",
            "status", "notes",
            "items", "qc_checks",
            "created_at",
        ]
        read_only_fields = ["id", "job_number", "created_at"]


class StockIssueLineSerializer(serializers.ModelSerializer):
    stock_item_barcode = serializers.CharField(source="stock_item.barcode", read_only=True, allow_null=True)

    class Meta:
        model = StockIssueLine
        fields = [
            "id", "stock_item", "stock_item_barcode",
            "product_code", "extrusion", "style", "colour", "colour_code",
            "length_mm", "quantity",
            "qc_result", "qc_notes",
        ]


class StockIssueSerializer(serializers.ModelSerializer):
    lines = StockIssueLineSerializer(many=True, read_only=True)
    division_code = serializers.CharField(source="division.code", read_only=True)
    receiving_location_name = serializers.CharField(source="receiving_location.name", read_only=True)

    class Meta:
        model = StockIssue
        fields = [
            "id", "issue_number", "division", "division_code",
            "receiving_location", "receiving_location_name",
            "status", "issued_date", "confirmed_date",
            "issued_by", "received_by", "notes",
            "lines",
            "created_at",
        ]
        read_only_fields = ["id", "issue_number", "created_at"]


class CreateQCCheckSerializer(serializers.Serializer):
    check_type = serializers.ChoiceField(choices=QualityCheckType.CHOICES)
    result = serializers.ChoiceField(choices=[("pass", "Pass"), ("conditional", "Conditional"), ("fail", "Fail")])
    stock_item_id = serializers.UUIDField(required=False, allow_null=True)
    powdercoat_job_id = serializers.UUIDField(required=False, allow_null=True)
    checked_by = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    fail_reason = serializers.CharField(required=False, allow_blank=True)
    condition = serializers.CharField(required=False, allow_blank=True)
