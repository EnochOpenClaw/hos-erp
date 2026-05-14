"""
Purchasing: Suppliers, Purchase Orders, Goods Received Notes, Invoices.
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
    payment_terms = models.CharField(max_length=100, blank=True)
    contact_name = models.CharField(max_length=100, blank=True)
    vat_number = models.CharField(max_length=30, blank=True)
    account_number = models.CharField(max_length=30, blank=True)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=50, blank=True)
    bank_code = models.CharField(max_length=20, blank=True)
    account_name = models.CharField(max_length=100, blank=True)
    account_email = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["company", "code"]]

    def save(self, *args, **kwargs):
        if not self.code or self.code.startswith('SUP'):
            self.code = self.generate_code(self.name)
        super().save(*args, **kwargs)

    @staticmethod
    def generate_code(name: str) -> str:
        """Generate a short internal code from the supplier name, e.g. AMEX."""
        if not name:
            return 'SUP'
        parts = name.upper().split()
        if len(parts) == 1:
            return parts[0][:4]
        code = ''.join(p[0] for p in parts if p)
        return code[:4]

    def __str__(self):
        return self.name


class PurchaseOrder(TimestampedModel):
    """
    PO tied to a division. Number format: PO-{DIV}-{SEQ:04}

    Lifecycle:
      requisition → pending_approval → approved → ordered → partial/received
    Reason is required before approval. Job link enables accounts verification.
    """
    PHASES = [
        ("requisition",       "Requisition (Draft)"),
        ("pending_approval",  "Awaiting Approval"),
        ("approved",          "Approved — Ready to Send"),
        ("ordered",           "Sent to Supplier"),
        ("partial",           "Partially Received"),
        ("received",          "Fully Received"),
        ("cancelled",         "Cancelled"),
    ]
    REASONS = [
        ("stock_reorder", "Stock Reorder (Minimum Reached)"),
        ("job_request",   "Job Request (Manufacturing)"),
        ("special_order", "Special Order"),
        ("blanket",       "Blanket / Planned Order"),
        ("other",         "Other"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_orders")
    division = models.ForeignKey(Division, on_delete=models.CASCADE, related_name="purchase_orders")
    po_number = models.CharField(max_length=30, unique=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    phase = models.CharField(max_length=20, choices=PHASES, default="requisition")
    reason = models.CharField(max_length=20, choices=REASONS, null=True, blank=True)
    requires_quote = models.BooleanField(
        default=False,
        help_text="Send to supplier for pricing before placing order"
    )
    job = models.ForeignKey("manufacturing.Job", on_delete=models.SET_NULL,
                            null=True, blank=True, related_name="purchase_orders")
    # Approval
    approved_by = models.CharField(max_length=100, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    is_eft = models.BooleanField(
        default=False,
        help_text="True = EFT (POP required before ordering). False = on account."
    )
    pop_document = models.FileField(upload_to="purchasing/pop/%Y/%m/", null=True, blank=True)
    # Dates
    order_date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-order_date"]

    def __str__(self):
        return f"{self.po_number} ({self.supplier.name}) [{self.phase}]"

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
        return all(line.is_complete for line in self.lines.all())


class PurchaseOrderLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    description = models.CharField(max_length=300, blank=True)
    ordered_qty = models.DecimalField(max_digits=12, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    received_qty = models.DecimalField(max_digits=12, decimal_places=4, default=0)
    job = models.ForeignKey("manufacturing.Job", on_delete=models.SET_NULL,
                            null=True, blank=True, related_name="po_lines")

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


class PurchasePriceHistory(TimestampedModel):
    """
    Full price audit trail per product per supplier.
    Created whenever an invoice is posted against a PO line.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="price_history")
    product = models.ForeignKey("products.Product", on_delete=models.CASCADE, related_name="price_history")
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="price_history")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.SET_NULL, null=True, related_name="price_records")
    recorded_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-recorded_at"]

    def __str__(self):
        return f"{self.product.code} @ R{self.unit_price} from {self.supplier.name} ({self.recorded_at.date()})"


class PurchaseInvoice(TimestampedModel):
    """
    Invoice entry derived from a PO/GRN.
    Compared to PO lines to detect overship/shortship and price variances.
    Posted invoice updates stock and triggers selling price recalculation.
    """
    STATUSES = [
        ("draft",        "Draft (Entering)"),
        ("posted",       "Posted to Stock"),
        ("discrepancy",  "Discrepancy — Review Required"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="purchase_invoices")
    po = models.ForeignKey(PurchaseOrder, on_delete=models.PROTECT, related_name="invoices")
    grn = models.ForeignKey(GoodsReceivedNote, on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=50)
    supplier_inv_number = models.CharField(max_length=50, blank=True,
                                            help_text="Supplier's invoice reference")
    invoice_date = models.DateField()
    due_date = models.DateField(null=True, blank=True)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    vat = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUSES, default="draft")
    notes = models.TextField(blank=True)
    price_variance_json = models.JSONField(default=dict, blank=True)
    posted_by = models.CharField(max_length=100, blank=True)
    posted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-invoice_date"]

    def __str__(self):
        return f"INV-{self.invoice_number} → {self.po.po_number}"


class PurchaseInvoiceLine(TimestampedModel):
    """
    Each invoice line links to the PO line it fulfils.
    received_qty here is what was on the invoice vs what was ordered.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name="lines")
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.PROTECT, related_name="invoice_lines")
    invoiced_qty = models.DecimalField(max_digits=12, decimal_places=4)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    price_variance = models.DecimalField(max_digits=12, decimal_places=2, default=0,
                                          help_text="Difference from PO unit price (+ = increase)")
    line_total = models.DecimalField(max_digits=14, decimal_places=2)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["invoice", "id"]

    def __str__(self):
        return f"{self.po_line.product.code} inv × {self.invoiced_qty}"

    @property
    def variance_pct(self):
        if self.po_line.unit_price > 0:
            return (self.price_variance / self.po_line.unit_price) * 100
        return 0