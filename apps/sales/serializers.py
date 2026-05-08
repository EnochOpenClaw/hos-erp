from rest_framework import serializers
from apps.sales.models import Customer, Quote, QuoteLine, SalesOrder, SalesOrderLine


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "company", "name", "code", "email", "phone", "address", "is_active", "created_at", "updated_at"]


class QuoteLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True, default=None)

    class Meta:
        model = QuoteLine
        fields = ["id", "description", "product", "product_code", "quantity", "unit_price", "line_total"]


class QuoteSerializer(serializers.ModelSerializer):
    lines = QuoteLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id", "company", "customer", "customer_name", "quote_number",
            "status", "status_display", "valid_until", "notes", "discount_pct",
            "lines", "created_at", "updated_at",
        ]


class SalesOrderLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True, default=None)

    class Meta:
        model = SalesOrderLine
        fields = ["id", "description", "product", "product_code", "quantity", "unit_price", "line_total"]


class SalesOrderSerializer(serializers.ModelSerializer):
    lines = SalesOrderLineSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="customer.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = SalesOrder
        fields = [
            "id", "company", "customer", "customer_name", "order_number",
            "status", "status_display", "order_date", "lines",
            "created_at", "updated_at",
        ]