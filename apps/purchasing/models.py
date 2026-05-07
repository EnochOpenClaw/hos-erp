"""
Purchasing: Suppliers, Purchase Orders, Goods Received Notes.
"""
from django.db import models
from django.utils import timezone
import uuid
from apps.core.models import TimestampedModel, Company, Division


class Supplier(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    lead_time_days = models.PositiveIntegerField(default=7)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["company", "code"]]

    def __str__(self):
        return self.name


class PurchaseOrder(TimestampedModel):
    """
    PO tied to a division. Number format: PO-{DIV}-{SEQ:04}
    """
    STATUSES = [
        ("draft",     "Draft"),
        ("sent",      "Sent to Supplier"),
        ("partial",   "Partially Received"),
        ("received",  "Fully Received"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_orders")
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="purchase_orders")
    po_number = models.CharField(max_length=30, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    status = models.CharField(max_length=20, choices=STATUSES, default="draft")
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.po_number} ({self.supplier.name})"

    def save(self, *args, **kwargs):
        if not self.po_number:
            year = self.order_date.year
            seq = PurchaseOrder.objects.filter(
                division=self.division,
                order_date__year=year
            ).count() + 1
            self.po_number = f"PO-{self.division.code}-{seq:04}"
        super().save(*args, **kwargs)

    @property
    def total_value(self):
        return sum(line.total for line in self.lines.all())

    @property
    def lines_received(self):
        return all(line.received_qty >= line.ordered_qty for line in self.lines.all())


class PurchaseOrderLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=300, blank=True)
    ordered_qty = models.DecimalField(max_digits=12, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    received_qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)

    class Meta:
        ordering = ["po", "id"]

    def __str__(self):
        return f"{self.product.code} × {self.ordered_qty}"

    @property
    def total(self):
        return self.ordered_qty * self.unit_price

    @property
    def is_complete(self):
        return self.received_qty >= self.ordered_qty


class GoodsReceivedNote(TimestampedModel):
    """
    GRN — records a receiving event against a PO.
    """
    STATUSES = [
        ("pending", "Pending QC"),
        ("passed",  "QC Passed"),
        ("failed",  "QC Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grns")
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="grns")
    grn_number = models.CharField(max_length=30, unique=True)
    received_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default="pending")

    class Meta:
        ordering = ["-received_date"]

    def save(self, *args, **kwargs):
        if not self.grn_number:
            year = self.received_date.year
            seq = GoodsReceivedNote.objects.filter(
                received_date__year=year
            ).count() + 1
            self.grn_number = f"GRN-{year}-{seq:04}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grn_number} → {self.po.po_number}"


class GoodsReceivedNoteLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT)
    received_qty = models.DecimalField(max_digits=12, decimal_places=4)
    condition_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["grn", "id"]

    def __str__(self):
        return f"{self.po_line.product.code} × {self.received_qty}"
