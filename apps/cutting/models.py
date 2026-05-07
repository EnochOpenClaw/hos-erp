# cutting/models.py
from django.db import models
import uuid
from apps.core.models import TimestampedModel, Company, Division, BinLocation


class OffcutStatus:
    IN_STOCK = "in_stock"
    RESERVED = "reserved"
    CONSUMED = "consumed"
    SCRAPPED = "scrapped"
    CHOICES = [
        (IN_STOCK, "In Stock / Available"),
        (RESERVED, "Reserved for Cut"),
        (CONSUMED, "Consumed in Cut"),
        (SCRAPPED, "Scrapped"),
    ]


class CutDesign(TimestampedModel):
    """
    One run of the cut optimizer (one job/quote).
    Stores the full solver bar_plan as JSON so the same plan can be
    re-rendered to PDF without re-running the MILP.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    division = models.ForeignKey(Division, on_delete=models.PROTECT, related_name="cut_designs")
    # FK to SalesOrderLine is optional — a design might be exploratory
    sales_order_line = models.ForeignKey(
        "sales.SalesOrderLine", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cut_designs"
    )
    name = models.CharField(max_length=200, blank=True)
    job_no = models.CharField(max_length=30, blank=True)

    # Optimizer config snapshot (kerf, trim, stock lengths, offcut thresholds...)
    config_json = models.JSONField(default=dict, blank=True)

    # Full bar_plan from solver, as JSON — see bar_plan schema below
    bar_plan_json = models.JSONField(default=dict, blank=True)

    # Offcut keep threshold used (mm)
    offcut_keep_min_mm = models.PositiveIntegerField(default=150)

    status = models.CharField(max_length=20, default="draft", choices=[
        ("draft", "Draft"),
        ("optimized", "Optimized"),
        ("released", "Released to Floor"),
        ("cut", "Cuts Complete"),
    ])

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name or self.job_no or str(self.id)[:8]} ({self.division.code})"

    @property
    def bar_plan(self):
        """Decode bar_plan_json to Python dict on access."""
        return self.bar_plan_json or {}

    @bar_plan.setter
    def bar_plan(self, value):
        self.bar_plan_json = value


class CutRequirement(TimestampedModel):
    """
    One cut requirement: one line from a quote/sales order.
    Multiple CutRequirements can point to the same Extrusion|Type|Style|Colour
    and will be pooled together by the MILP solver.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design = models.ForeignKey(CutDesign, on_delete=models.CASCADE, related_name="requirements")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    # Override fields in case product variant differs from master
    style = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=100, blank=True)
    colour_code = models.CharField(max_length=30, blank=True)
    # Cut length in mm
    cut_length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.PositiveIntegerField(default=1)
    # How many of qty are already allocated to CutBars
    allocated_qty = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["design", "id"]

    def save(self, *args, **kwargs):
        # Auto-populate style/colour/code from product if not set
        if self.product_id:
            from apps.products.models import Product
            try:
                prod = Product.objects.get(id=self.product_id)
                if not self.style:
                    self.style = prod.style or ""
                if not self.colour:
                    self.colour = prod.colour or ""
                if not self.colour_code:
                    self.colour_code = prod.colour_code or ""
            except Exception:
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.code} × {self.qty} @ {self.cut_length_mm}mm"

    @property
    def remaining_qty(self):
        return self.qty - self.allocated_qty

    @property
    def extrusion(self):
        return self.product.extrusion.name if self.product and self.product.extrusion else ""

    def matches_offcut(self, offcut):
        """Check if offcut matches this requirement's style/finish."""
        style = (self.style or "").lower().strip()
        colour = (self.colour or "").lower().strip()
        code = (self.colour_code or "").lower().strip()

        off_style = (offcut.style or "").lower().strip()
        off_colour = (offcut.colour or "").lower().strip()
        off_code = (offcut.colour_code or "").lower().strip()

        # Mill must match mill
        if colour == "mill" and off_colour != "mill":
            return False

        # Colour must match when specified
        if colour and colour != off_colour:
            return False

        # Colour code must match when specified
        if code and code != off_code:
            return False

        # Style compatibility (Option C hybrid):
        # Security/Decorative offcut can serve either pure category
        if "security" in style and not ("security" in off_style or "security/decorative" in off_style):
            return False
        if "decorative" in style and not ("decorative" in off_style or "security/decorative" in off_style):
            return False

        return True


class CutBar(TimestampedModel):
    """
    One bar cut by the optimizer.
    The offcut below keep_min is the discard; above is a keepable Offcut.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design = models.ForeignKey(CutDesign, on_delete=models.CASCADE, related_name="bars")
    bar_no = models.PositiveIntegerField(default=0)
    # Stock bar used
    stock_len_mm = models.DecimalField(max_digits=10, decimal_places=2)
    # Cutting parameters
    kerf_mm = models.DecimalField(max_digits=8, decimal_places=2, default=4)
    trim_start_mm = models.DecimalField(max_digits=8, decimal_places=2, default=25)
    trim_end_mm = models.DecimalField(max_digits=8, decimal_places=2, default=5)
    # The offcut left on this bar (may be keepable or discard)
    offcut_mm = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # If this bar consumed a pre-existing offcut from inventory
    source_offcut = models.ForeignKey(
        "Offcut", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="consumed_as_source"
    )
    # Group key this bar belongs to in the diagram (Extrusion|Style|Colour)
    group_key = models.CharField(max_length=200, blank=True)
    is_flipped = models.BooleanField(
        default=False, help_text="Operator has placed this bar on the machine"
    )

    class Meta:
        ordering = ["design", "bar_no"]
        unique_together = [["design", "bar_no"]]

    def __str__(self):
        return f"Bar {self.bar_no} — {self.stock_len_mm}mm ({self.offcut_mm}mm offcut)"

    @property
    def is_complete(self):
        lines = list(self.cut_lines.all())
        if not lines:
            return False
        return all(bool(c.is_cut) for c in lines)

    @property
    def cuts(self):
        return list(self.cut_lines.all())


class CutBarCut(TimestampedModel):
    """
    One cut made on a CutBar.
    Cuts are ordered left-to-right on the bar (increasing position_mm).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bar = models.ForeignKey(CutBar, on_delete=models.CASCADE, related_name="cut_lines")
    requirement = models.ForeignKey(
        CutRequirement, on_delete=models.PROTECT,
        null=True, blank=True, related_name="cut_lines"
    )
    # Position from left trim end (mm)
    position_mm = models.DecimalField(max_digits=10, decimal_places=2)
    length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    item_id = models.PositiveIntegerField(default=0)  # drawing/item reference
    is_cut = models.BooleanField(default=False)

    class Meta:
        ordering = ["bar", "position_mm"]


class Offcut(TimestampedModel):
    """
    A keepable offcut from a CutBar (offcut_mm >= offcut_keep_min_mm).
    Lives in a BinLocation until consumed as stock for a new CutDesign.
    """
    STATUSES = OffcutStatus.CHOICES

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    design = models.ForeignKey(CutDesign, on_delete=models.CASCADE, related_name="offcuts")
    bar = models.ForeignKey(CutBar, on_delete=models.CASCADE, related_name="offcut_record")
    # Source bar that created this offcut
    source_job_name = models.CharField(max_length=200, blank=True)
    source_job_no = models.CharField(max_length=30, blank=True)
    # Which design consumed this offcut as stock
    consumed_by = models.ForeignKey(
        CutDesign, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="consumed_offcuts"
    )
    consumed_date = models.DateTimeField(null=True, blank=True)

    # Identity
    extrusion = models.CharField(max_length=100)
    style = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=100, blank=True)
    colour_code = models.CharField(max_length=30, blank=True)

    # Dimensions
    length_mm = models.DecimalField(max_digits=10, decimal_places=2)
    stock_len_mm = models.DecimalField(max_digits=10, decimal_places=2)

    # Location
    bin_location = models.ForeignKey(
        BinLocation, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cutting_offcuts",
    )
    location_label = models.CharField(max_length=100, blank=True)  # free-text fallback
    storage_area = models.CharField(max_length=30, blank=True)  # TABLE / RACK / CRATE

    status = models.CharField(max_length=20, choices=OffcutStatus.CHOICES, default=OffcutStatus.IN_STOCK)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["extrusion", "status"]),
            models.Index(fields=["status", "length_mm"]),
        ]

    def __str__(self):
        return f"{self.extrusion} {self.length_mm}mm ({self.status})"

    def matches_requirement(self, req):
        """Check if this offcut can satisfy a CutRequirement."""
        if self.extrusion.lower() != req.extrusion.lower():
            return False
        if self.length_mm < req.cut_length_mm:
            return False
        return req.matches_offcut(self)

    def can_consume_for(self, requirement, keep_min_mm=150):
        """Can this offcut be consumed to fulfil the given requirement?"""
        if self.status != OffcutStatus.IN_STOCK:
            return False
        if self.extrusion.lower() != (requirement.extrusion or "").lower():
            return False
        if self.length_mm < requirement.cut_length_mm:
            return False
        # Remaining length after cut must meet keep_min
        req_len = requirement.cut_length_mm
        remaining = self.length_mm - req_len
        if remaining < keep_min_mm:
            return False
        return requirement.matches_offcut(self)


class OffcutConsumeEvent(TimestampedModel):
    """
    Audit log: when an offcut was matched and reserved/consumed for a design.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    offcut = models.ForeignKey(Offcut, on_delete=models.CASCADE, related_name="consume_events")
    design = models.ForeignKey(CutDesign, on_delete=models.CASCADE, related_name="offcut_consume_events")
    requirement = models.ForeignKey(CutRequirement, on_delete=models.PROTECT)
    qty = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["offcut", "created_at"]
