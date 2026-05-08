from rest_framework import serializers
from apps.inventory.models import StockItem, Offcut


class StockItemSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    extrusion_name = serializers.CharField(source="product.extrusion.name", read_only=True, default=None)
    state_display = serializers.CharField(source="get_state_display", read_only=True)
    bin_full_code = serializers.CharField(source="bin_location.full_code", read_only=True, default=None)
    is_offcut = serializers.BooleanField(read_only=True)

    class Meta:
        model = StockItem
        fields = [
            "id", "company", "product", "product_code", "product_name",
            "extrusion_name", "barcode", "quantity", "length_mm", "state",
            "state_display", "bin_location", "bin_full_code", "requires_powdercoat",
            "powder_color", "unit_cost", "source_order", "is_active",
            "is_offcut", "created_at", "updated_at",
        ]


class OffcutSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    extrusion_name = serializers.CharField(source="product.extrusion.name", read_only=True, default=None)
    finish_display = serializers.CharField(source="get_finish_display", read_only=True)
    bin_full_code = serializers.CharField(source="bin_location.full_code", read_only=True, default=None)

    class Meta:
        model = Offcut
        fields = [
            "id", "company", "product", "product_code", "extrusion_name",
            "length_mm", "quantity", "finish", "finish_display",
            "powder_color", "bin_location", "bin_full_code",
            "is_reserved", "is_active", "created_at", "updated_at",
        ]