# powdercoat/models.py
"""
Powder coating sub-flow with QC checks at every transition.

Stock state transitions with QC:
  received from supplier → stored  (QC: incoming inspection)
  stored → issued to factory       (QC: issue check)
  stored → sent to powdercoat      (QC: outgoing to powdercoat check)
  sent to powdercoat → returned     (QC: incoming from powdercoat check)
  returned → cut                   (QC: pre-cut check)

Quality checks are mandatory audit records attached to StockItems
and/or PowdercoatJobs, not loose comments.
"""
from django.db import models
import uuid
from apps.core.models import TimestampedModel, Division, BinLocation
from apps.products.models import Product


class QualityCheckType:
    INCOMING_GRN    = "incoming_grn"     # Stock received from supplier
    ISSUE_TO_FACTORY = "issue_factory"   # Stock issued from store to factory
    OUTGOING_POWDER  = "outgoing_powder" # Stock leaving factory for powder coater
    INCOMING_POWDER  = "incoming_powder" # Stock returning from powder coater
    PRE_CUT          = "pre_cut"         # Stock about to be cut
    FINAL_QC         = "final_qc"       # Finished goods final check

    CHOICES = [
        (INCOMING_GRN,     "Incoming (GRN)"),
        (ISSUE_TO_FACTORY, "Issue to Factory"),
        (OUTGOING_POWDER,  "Outgoing to Powder Coating"),
        (INCOMING_POWDER,  "Returning from Powder Coating"),
        (PRE_CUT,          "Pre-Cut Check"),
        (FINAL_QC,         "Final QC"),
    ]

    PASS_CODES  = ["pass", "fail", "conditional"]
    FAIL_REASONS = [
        "damage", "wrong_colour", "wrong_qty", "surface_mark",
        "dimensional_issue", "documentation_missing", "other",
    ]


class QualityCheck(TimestampedModel):
    """
    A quality check record attached to a StockItem or a PowdercoatJob.
    Every factory floor transition gets a QC record — pass/fail/conditional.
    """
    PASS_CODES  = QualityCheckType.PASS_CODES
    FAIL_REASONS = QualityCheckType.FAIL_REASONS

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # What was checked
    check_type = models.CharField(max_length=30, choices=QualityCheckType.CHOICES)
    result = models.CharField(max_length=20, choices=[
        ("pass",         "Pass"),
        ("conditional",  "Conditional — note issue"),
        ("fail",         "Fail — reject"),
    ])

    # Reference to the stock item or powdercoat job
    stock_item = models.ForeignKey(
        "inventory.StockItem", on_delete=models.CASCADE,
        null=True, blank=True, related_name="quality_checks"
    )
    powdercoat_job = models.ForeignKey(
        "PowdercoatJob", on_delete=models.CASCADE,
        null=True, blank=True, related_name="quality_checks"
    )

    # Who did the check (free-text until we have users)
    checked_by = models.CharField(max_length=100, blank=True)
    check_date = models.DateTimeField(auto_now_add=True)

    # Condition notes
    notes = models.TextField(blank=True)
    # If fail: reason
    fail_reason = models.CharField(max_length=50, blank=True)
    # If conditional: what must be done
    condition = models.TextField(blank=True)

    class Meta:
        ordering = ["-check_date"]
        verbose_name_plural = "Quality Checks"

    def __str__(self):
        return f"{self.check_type} — {self.result} ({self.check_date:%Y-%m-%d})"


class PowdercoatSupplier(TimestampedModel):
    """
    A powder coating company / supplier.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    contact_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    lead_time_days = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class PowdercoatJob(TimestampedModel):
    """
    One trip to the powder coating plant.

    A job batches one or more StockItems (extrusion lengths) of the same
    colour, going to the same supplier, on the same day.

    Status flow:
      draft → sent → returned → completed
                ↑         ↑
                QC check  QC check (incoming from powdercoat)
    """
    STATUS_CHOICES = [
        ("draft",     "Draft — not yet sent"),
        ("sent",      "Sent to Powder Coater"),
        ("returned",  "Returned from Powder Coater"),
        ("completed", "Completed — all items received back"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_number = models.CharField(max_length=20, unique=True)  # PC-YYYY-NNNN

    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name="powdercoat_jobs")
    supplier = models.ForeignKey(
        PowdercoatSupplier, on_delete=models.PROTECT,
        related_name="powdercoat_jobs"
    )

    # The colour being applied to all items in this job
    powder_color = models.CharField(max_length=100)
    powder_color_code = models.CharField(max_length=30, blank=True)

    # Dates
    sent_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    returned_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_number} — {self.powder_color} ({self.status})"

    def save(self, *args, **kwargs):
        if not self.job_number:
            self.job_number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        import datetime
        year = datetime.date.today().year
        prefix = f"PC-{year}-"
        last = PowdercoatJob.objects.filter(
            job_number__startswith=prefix
        ).order_by("job_number").last()
        if last:
            try:
                seq = int(last.job_number.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class PowdercoatJobItem(TimestampedModel):
    """
    One line on a PowdercoatJob — a StockItem (bar) being sent for coating.
    Tracks which StockItem, what state it was in, and what came back.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(PowdercoatJob, on_delete=models.CASCADE, related_name="items")
    stock_item = models.ForeignKey(
        "inventory.StockItem", on_delete=models.PROTECT,
        related_name="powdercoat_items"
    )

    # Snapshot at send time
    extrusion = models.CharField(max_length=100)  # e.g. "Stile", "Louvre"
    style = models.CharField(max_length=50, blank=True)
    length_mm = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    # Track the state transitions
    sent_state = models.CharField(max_length=30)  # state when sent (e.g. "stored")
    returned_state = models.CharField(max_length=30, blank=True)  # state when returned

    # QC result for this specific item
    qc_result = models.CharField(max_length=20, choices=[
        ("pass",         "Pass"),
        ("conditional",  "Conditional"),
        ("fail",         "Fail"),
        ("pending",      "Pending Inspection"),
    ], default="pending")

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["job", "id"]

    def __str__(self):
        return f"{self.extrusion} {self.length_mm}mm × {self.quantity} ({self.qc_result})"


class StockIssue(TimestampedModel):
    """
    Stock issued from the store to the factory floor.
    The counterpart to a PowdercoatJob — a job at the factory level.

    Issue flow:
      draft → issued → received_at_factory
    """
    STATUS_CHOICES = [
        ("draft",    "Draft"),
        ("issued",   "Issued to Factory"),
        ("confirmed","Confirmed at Factory"),
        ("cancelled","Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue_number = models.CharField(max_length=20, unique=True)  # ISSUE-YYYY-NNNN
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name="stock_issues")

    # The factory/location receiving the stock
    receiving_location = models.ForeignKey(
        "core.Location", on_delete=models.PROTECT,
        related_name="stock_issues_received"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    issued_date = models.DateField(null=True, blank=True)
    confirmed_date = models.DateField(null=True, blank=True)
    issued_by = models.CharField(max_length=100, blank=True)
    received_by = models.CharField(max_length=100, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.issue_number} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.issue_number:
            self.issue_number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        import datetime
        year = datetime.date.today().year
        prefix = f"ISSUE-{year}-"
        last = StockIssue.objects.filter(
            issue_number__startswith=prefix
        ).order_by("issue_number").last()
        if last:
            try:
                seq = int(last.issue_number.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"


class StockIssueLine(TimestampedModel):
    """
    One line on a StockIssue — a StockItem being issued.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issue = models.ForeignKey(StockIssue, on_delete=models.CASCADE, related_name="lines")
    stock_item = models.ForeignKey(
        "inventory.StockItem", on_delete=models.PROTECT,
        related_name="issue_lines"
    )

    # Snapshot at issue time
    product_code = models.CharField(max_length=50)
    extrusion = models.CharField(max_length=100, blank=True)
    style = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=100, blank=True)
    colour_code = models.CharField(max_length=30, blank=True)
    length_mm = models.PositiveIntegerField(null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    # QC for this line
    qc_result = models.CharField(max_length=20, choices=[
        ("pass",         "Pass"),
        ("conditional",  "Conditional"),
        ("fail",         "Fail"),
        ("pending",      "Pending"),
    ], default="pending")
    qc_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["issue", "id"]
