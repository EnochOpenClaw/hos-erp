from rest_framework import serializers
from apps.products.models import MaterialCategory, ExtrusionType, Product


class MaterialCategorySerializer(serializers.ModelSerializer):
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = MaterialCategory
        fields = ["id", "name", "description", "sort_order", "product_count", "created_at", "updated_at"]


class ExtrusionTypeSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    product_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = ExtrusionType
        fields = [
            "id", "name", "category", "category_display", "description",
            "weight_per_mm", "die_number", "standard_bar_mm", "kerf_mm",
            "is_active", "product_count", "created_at", "updated_at",
        ]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True, default=None)
    extrusion_name = serializers.CharField(source="extrusion.name", read_only=True, default=None)
    unit_type_display = serializers.CharField(source="get_unit_type_display", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id", "name", "code", "category", "category_name",
            "extrusion", "extrusion_name", "style", "colour", "colour_code",
            "description", "unit_type", "unit_type_display", "is_active",
            "created_at", "updated_at",
        ]