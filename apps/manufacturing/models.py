# manufacturing/models.py
"""
Manufacturing: Jobs, Control Sheets, Cutting Plans, BOMs.
"""
from django.db import models
import uuid
from apps.core.models import TimestampedModel, Company


class Job(TimestampedModel):
    """
    A manufacturing job. Corresponds to a customer's order or project.
    One Job has many ControlSheets (one per opening).
    """
    STATUS_CHOICES = [
        ("draft",     "Draft"),
        ("confirmed", "Confirmed — awaiting final sizes"),
        ("ready",     "Ready — all control sheets in, ready for cut"),
        ("cutting",   "In Cutting"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    job_number = models.CharField(max_length=50, unique=True)  # JOB-YYYY-NNNN
    description = models.TextField(blank=True)

    # Customer / project reference
    customer_name = models.CharField(max_length=200, blank=True)
    customer_ref = models.CharField(max_length=100, blank=True)  # customer's PO / ref

    division = models.ForeignKey(
        "core.Division", on_delete=models.PROTECT,
        related_name="manufacturing_jobs"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    # Lower number = higher priority. 0 = normal FIFO, 1+ = urgent.
    priority = models.PositiveIntegerField(default=0, db_index=True)
    # Once all control sheets are final and payment received → ready

    # Linked cut design (created after optimization)
    cut_design = models.ForeignKey(
        "cutting.CutDesign", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="manufacturing_jobs"
    )

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["priority", "created_at"]

    def __str__(self):
        return f"{self.job_number} — {self.status}"

    def save(self, *args, **kwargs):
        if not self.job_number:
            self.job_number = self._generate_number()
        super().save(*args, **kwargs)

    def _generate_number(self):
        import datetime
        year = datetime.date.today().year
        prefix = f"JOB-{year}-"
        last = Job.objects.filter(job_number__startswith=prefix).order_by("job_number").last()
        if last:
            try:
                seq = int(last.job_number.split("-")[-1]) + 1
            except Exception:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @property
    def control_sheets(self):
        return self.control_sheets.all()

    @property
    def all_sheets_final(self):
        return all(cs.is_final for cs in self.control_sheets)


class ControlSheet(TimestampedModel):
    """
    One Control Sheet = one opening in a Job.
    Contains all the per-opening configuration and sizing.
    Many ControlSheets per Job.

    Status:
      draft    = sizes / config still being finalised
      final    = locked in, ready to drive cut requirements
      issued   = issued to factory (cut requirements generated)
    """
    STATUS_CHOICES = [
        ("draft",  "Draft — not yet final"),
        ("final",  "Final — sizes locked"),
        ("issued", "Issued to Factory"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="control_sheets")

    # Sheet identity
    sheet_number = models.PositiveIntegerField(
        help_text="Sequential number within this job (1, 2, 3...)"
    )
    name = models.CharField(
        max_length=200, blank=True,
        help_text="e.g. 'Opening 1 — Front Door' or 'Window A'"
    )

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="draft")
    is_final = models.BooleanField(default=False)

    # Opening type
    OPENING_TYPES = [
        ("door",    "Door"),
        ("window",  "Window"),
        ("flyscreen","Flyscreen"),
        ("security", "Security Barrier"),
        ("other",   "Other"),
    ]
    opening_type = models.CharField(max_length=20, choices=OPENING_TYPES, default="door")

    # Configuration
    WIDTH_MM  = models.PositiveIntegerField(null=True, blank=True, help_text="Overall width (mm)")
    HEIGHT_MM = models.PositiveIntegerField(null=True, blank=True, help_text="Overall height (mm)")

    # Lock type
    LOCK_TYPE_CHOICES = [
        ("none",    "No Lock"),
        ("standard","Standard Lock"),
        ("deadbolt","Deadbolt"),
        ("key",     "Key Operated"),
        ("thumb",   "Thumb Turn"),
    ]
    lock_type = models.CharField(max_length=20, choices=LOCK_TYPE_CHOICES, blank=True)

    # Colour / powder
    colour_name  = models.CharField(max_length=100, blank=True)
    colour_code  = models.CharField(max_length=30, blank=True)
    powder_coat  = models.BooleanField(default=False, help_text="Requires powder coating")

    # Mesh type (for flyscreens)
    MESH_CHOICES = [
        ("none",    "No Mesh"),
        ("fibreglass", "Fibreglass"),
        ("aluminium",  "Aluminium"),
        ("security",   "Security Mesh"),
    ]
    mesh_type = models.CharField(max_length=20, choices=MESH_CHOICES, default="none")

    # Rails / Stiles
    has_top_rail    = models.BooleanField(default=True)
    has_bottom_rail = models.BooleanField(default=True)
    rail_width_mm   = models.PositiveIntegerField(default=0)

    # Hardware notes
    hardware_notes = models.TextField(blank=True)

    # Signed off
    signed_off_by = models.CharField(max_length=100, blank=True)
    signed_off_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["job", "sheet_number"]
        unique_together = [["job", "sheet_number"]]

    def __str__(self):
        return f"CS-{self.job.job_number} #{self.sheet_number}: {self.name or self.opening_type}"


class ControlSheetLine(TimestampedModel):
    """
    One line on a Control Sheet — one extrusion requirement.
    e.g. "Stile LH × 2, 2990mm, mill finish"
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    control_sheet = models.ForeignKey(
        ControlSheet, on_delete=models.CASCADE,
        related_name="lines"
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT,
        related_name="control_sheet_lines"
    )

    # Override length from product's standard (if this opening is non-standard)
    length_mm = models.PositiveIntegerField(
        null=True, blank=True,
        help_text="Override length (leave blank to use product standard)"
    )

    quantity  = models.PositiveIntegerField(default=1)
    finish    = models.CharField(max_length=30, choices=[
        ("mill",         "Mill (Uncoated)"),
        ("powdercoated", "Powdercoated"),
    ], default="mill")
    powder_color = models.CharField(max_length=50, blank=True)

    # Side / position on the opening
    POSITION_CHOICES = [
        ("left",   "Left Stile"),
        ("right",  "Right Stile"),
        ("top",    "Top Rail"),
        ("bottom", "Bottom Rail"),
        ("mid",    "Mid Rail"),
        ("louvre", "Louvre"),
        ("track",  "Track"),
        ("other",  "Other"),
    ]
    position = models.CharField(max_length=20, choices=POSITION_CHOICES, blank=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["position", "product"]

    def __str__(self):
        L = self.length_mm or (self.product.length_mm if self.product else "?")
        return f"{self.product.code if self.product else '?'} {L}mm × {self.quantity}"


class CutRequirement(TimestampedModel):
    """
    A single demand line driven by a ControlSheet.
    These get grouped and sent to the optimizer together.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="cut_requirements")
    control_sheet = models.ForeignKey(
        ControlSheet, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="cut_requirements"
    )
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT,
        related_name="cut_requirements"
    )
    cut_length_mm = models.PositiveIntegerField(
        help_text="Finished cut length (after all processing)"
    )
    qty = models.PositiveIntegerField()
    style = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=100, blank=True)
    colour_code = models.CharField(max_length=30, blank=True)
    allow_offcut_match = models.BooleanField(default=True)
    allocated_qty = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["product", "cut_length_mm"]

    def __str__(self):
        return f"{self.product.code} {self.cut_length_mm}mm × {self.qty}"


class CutPlan(TimestampedModel):
    """
    The optimizer output: one plan per extrusion group.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="cut_plans")
    group_key = models.CharField(max_length=200)
    bars_used = models.PositiveIntegerField()
    waste_pct = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("cut",     "Bars Cut"),
        ("completed","Completed"),
    ], default="pending")

    class Meta:
        ordering = ["group_key"]

    def __str__(self):
        return f"Plan {self.group_key} ({self.bars_used} bars, {self.waste_pct}% waste)"


class CutPlanBar(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cut_plan = models.ForeignKey(CutPlan, on_delete=models.CASCADE, related_name="bars")
    stock_bar_id = models.CharField(max_length=50, blank=True)
    bar_length_mm = models.PositiveIntegerField()
    cuts_json = models.JSONField(default=list)
    offcut_mm = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]


class BOM(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="boms")
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["company", "code", "version"]]

    def __str__(self):
        return f"{self.code} v{self.version}"


class BOMLine(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    length_mm = models.PositiveIntegerField(null=True, blank=True)
    finish = models.CharField(max_length=30, choices=[
        ("mill", "Mill"), ("powdercoated", "Powdercoated"),
    ], default="mill")
    powder_color = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["id"]
