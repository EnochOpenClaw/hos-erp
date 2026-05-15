from rest_framework import serializers
from apps.purchasing.models import (
    Supplier, PurchaseOrder, PurchaseOrderLine,
    GoodsReceivedNote, GoodsReceivedNoteLine,
    PurchaseInvoice, PurchaseInvoiceLine, PurchasePriceHistory,
)
from apps.core.models import Company


# ─── Supplier ────────────────────────────────────────────────────────────────

class SupplierSerializer(serializers.ModelSerializer):
    code = serializers.CharField(required=False, read_only=True)
    company = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Supplier
        fields = [
            "id", "company", "name", "code", "email", "phone", "address",
            "lead_time_days", "payment_terms", "contact_name",
            "vat_number", "account_number", "account_name", "account_email",
            "registration_number", "bank_name", "bank_branch", "bank_code",
            "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "code", "created_at", "updated_at"]

    def create(self, validated_data):
        company = Company.objects.get(name="OpenFactory Systems")
        name = validated_data.get("name", "")
        raw_code = Supplier.generate_code(name)
        code = raw_code
        counter = 1
        while Supplier.objects.filter(company=company, code=code).exists():
            suffix = str(counter)
            code = raw_code[:4 - len(suffix)] + suffix if len(raw_code) >= 4 else raw_code + suffix
            counter += 1
        return Supplier.objects.create(company=company, code=code, **validated_data)


# ─── Purchase Order Line ────────────────────────────────────────────────────

class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    product_name = serializers.CharField(source="product.name", read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    job_number = serializers.CharField(source="job.job_number", read_only=True, default=None)

    class Meta:
        model = PurchaseOrderLine
        fields = ["id", "product", "product_code", "product_name", "description",
                 "ordered_qty", "unit_price", "received_qty", "total",
                 "is_complete", "job", "job_number"]
        read_only_fields = ["id", "received_qty", "total", "is_complete", "job_number"]

    def create(self, validated_data):
        po = self.context.get("po")
        if po:
            validated_data["po"] = po
        return PurchaseOrderLine.objects.create(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


# ─── Purchase Order ─────────────────────────────────────────────────────────

class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for PO list view."""
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    division_code = serializers.CharField(source="division.code", read_only=True)
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    line_count = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseOrder
        fields = ["id", "po_number", "division", "division_code", "supplier",
                 "supplier_name", "phase", "reason", "is_eft",
                 "order_date", "expected_date", "total_value", "line_count"]

    def get_line_count(self, obj):
        return obj.lines.count()


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True, read_only=False)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    division_code = serializers.CharField(source="division.code", read_only=True)
    total_value = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = ["id", "po_number", "division", "division_code", "supplier",
                 "supplier_name", "phase", "reason", "requires_quote",
                 "job", "approved_by", "approved_at", "is_eft",
                 "order_date", "expected_date", "notes", "lines", "total_value"]
        read_only_fields = ["id", "po_number", "total_value", "approved_at"]

    def create(self, validated_data):
        company = Company.objects.get(name="OpenFactory Systems")
        lines_data = validated_data.pop("lines", [])
        po = PurchaseOrder.objects.create(company=company, **validated_data)
        for line in lines_data:
            PurchaseOrderLine.objects.create(po=po, **line)
        return po

    def update(self, instance, validated_data):
        lines_data = validated_data.pop("lines", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if lines_data is not None:
            instance.lines.all().delete()
            for line in lines_data:
                PurchaseOrderLine.objects.create(po=instance, **line)
        return instance


# ─── Approval ────────────────────────────────────────────────────────────────

class PurchaseOrderApproveSerializer(serializers.Serializer):
    approved_by = serializers.CharField(max_length=100)
    is_eft = serializers.BooleanField(required=False, default=False)


# ─── GRN ────────────────────────────────────────────────────────────────────

class GRNLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="po_line.product.code", read_only=True)
    product_name = serializers.CharField(source="po_line.product.name", read_only=True)
    ordered_qty = serializers.DecimalField(max_digits=12, decimal_places=4, read_only=True)
    po_line_id = serializers.IntegerField(source="po_line.id", read_only=True)

    class Meta:
        model = GoodsReceivedNoteLine
        fields = ["id", "po_line", "po_line_id", "product_code", "product_name",
                 "ordered_qty", "received_qty", "condition_notes"]


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    lines = GRNLineSerializer(many=True, read_only=True)
    grn_number = serializers.CharField(read_only=True)
    po_number = serializers.CharField(source="po.po_number", read_only=True)

    class Meta:
        model = GoodsReceivedNote
        fields = ["id", "grn_number", "po", "po_number", "received_date",
                 "status", "notes", "lines"]


# ─── Purchase Invoice ────────────────────────────────────────────────────────

class PurchaseInvoiceLineSerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="po_line.product.code", read_only=True)
    product_name = serializers.CharField(source="po_line.product.name", read_only=True)
    po_line_ordered = serializers.DecimalField(
        source="po_line.ordered_qty", max_digits=12, decimal_places=4, read_only=True
    )
    po_unit_price = serializers.DecimalField(
        source="po_line.unit_price", max_digits=12, decimal_places=2, read_only=True
    )
    variance_pct = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseInvoiceLine
        fields = ["id", "po_line", "product_code", "product_name",
                 "po_line_ordered", "invoiced_qty", "po_unit_price",
                 "unit_price", "price_variance", "variance_pct", "line_total", "notes"]

    def get_variance_pct(self, obj):
        return obj.variance_pct


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    lines = PurchaseInvoiceLineSerializer(many=True, read_only=True)
    po_number = serializers.CharField(source="po.po_number", read_only=True)
    grn_number = serializers.CharField(source="grn.grn_number", read_only=True)
    supplier_name = serializers.SerializerMethodField()

    class Meta:
        model = PurchaseInvoice
        fields = ["id", 'invoice_number', 'supplier_inv_number', 'po', 'po_number',
                 'grn_number', 'supplier_name',
                 'invoice_date', 'due_date', 'subtotal', 'vat', 'total',
                 'status', 'notes', 'price_variance_json', 'posted_by', 'posted_at',
                 'lines']

    def get_supplier_name(self, obj):
        return obj.po.supplier.name

    def create(self, validated_data, grn_id=None):
        company = Company.objects.get(name="OpenFactory Systems")
        lines_data = validated_data.pop("lines", [])
        grn_uuid = validated_data.pop("grn", grn_id)
        grn = GoodsReceivedNote.objects.get(id=grn_uuid) if grn_uuid else None
        invoice = PurchaseInvoice.objects.create(
            company=company, grn=grn, **validated_data
        )
        for line in lines_data:
            PurchaseInvoiceLine.objects.create(invoice=invoice, **line)
        return invoice


# ─── Price History ─────────────────────────────────────────────────────────

class PurchasePriceHistorySerializer(serializers.ModelSerializer):
    product_code = serializers.CharField(source="product.code", read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = PurchasePriceHistory
        fields = ["id", "product", "product_code", "supplier", "supplier_name",
                 "unit_price", "po_line", "recorded_at"]