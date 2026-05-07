from rest_framework import serializers
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderLine


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = ["id", "product", "product_code", "product_name", "description",
                 "ordered_qty", "unit_price", "received_qty", "total", "is_complete"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    division_code = serializers.CharField(source="division.code", read_only=True)
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id", "po_number", "division", "division_code", "supplier",
                 "supplier_name", "status", "order_date", "expected_date",
                 "notes", "lines", "total_value"]
