"""
Manufacturing: Jobs, Cutting Plans, BOMs.
The heart of the operation.
"""
from django.db import models
import uuid
from apps.core.models import TimestampedModel, Company


class Job(TimestampedModel):
    """
    A manufacturing job (corresponds to a line on a manufacturing sheet).
    Contains one or more demand lines that need to be cut.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="jobs")
    job_number = models.CharField(max_length=50)  # e.g. JOB-9999-Item1
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("cutting", "In Cutting"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], default="pending")
    source_order = models.CharField(max_length=50, blank=True)  # MO reference

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["company", "job_number"]]

    def __str__(self):
        return f"{self.job_number} ({self.status})"


class CutRequirement(TimestampedModel):
    """
    A single demand line: e.g. "Stile, 299mm, qty 2, mill finish".
    These get grouped and sent to the optimizer together.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="cut_requirements")
    product = models.ForeignKey(
        "products.Product", on_delete=models.PROTECT, related_name="cut_requirements"
    )
    length_mm = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()
    finish = models.CharField(max_length=30, choices=[
        ("mill", "Mill"),
        ("powdercoated", "Powdercoated"),
    ], default="mill")
    powder_color = models.CharField(max_length=50, blank=True)
    # If this requirement can be fulfilled from offcut stock
    allow_offcut_match = models.BooleanField(default=True)

    class Meta:
        ordering = ["product", "length_mm"]

    def __str__(self):
        return f"{self.product.code} {self.length_mm}mm × {self.quantity}"


class CutPlan(TimestampedModel):
    """
    The optimizer output: one plan per (Extrusion | Finish | Colour) group.
    Contains individual CutBars.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="cut_plans")
    group_key = models.CharField(max_length=200)  # "Stile | mill | ANP3050"
    bars_used = models.PositiveIntegerField()
    waste_pct = models.DecimalField(max_digits=5, decimal_places=2)
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("cut", "Bars Cut"),
        ("completed", "Completed"),
    ], default="pending")

    class Meta:
        ordering = ["group_key"]

    def __str__(self):
        return f"Plan {self.group_key} ({self.bars_used} bars, {self.waste_pct}% waste)"


class CutBar(TimestampedModel):
    """
    One stock bar allocated from a CutPlan.
    Records which demand lines were cut from this bar.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cut_plan = models.ForeignKey(CutPlan, on_delete=models.CASCADE, related_name="cut_bars")
    stock_bar_id = models.CharField(max_length=50, blank=True)  # source stock barcode
    bar_length_mm = models.PositiveIntegerField()
    cuts_json = models.JSONField(default=list)  # [{"length_mm": 299, "qty": 2, "offcut_mm": 97}]
    offcut_mm = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["id"]


class BOM(TimestampedModel):
    """
    Bill of Materials — a recipe for a finished product.
    Links a finished product to its component cut requirements.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="boms")
    name = models.CharField(max_length=200)  # e.g. "Security Shutter - Standard"
    code = models.CharField(max_length=50)
    version = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["company", "code", "version"]]

    def __str__(self):
        return f"{self.code} v{self.version}"


class BOMLine(TimestampedModel):
    """One line in a BOM."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bom = models.ForeignKey(BOM, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey("products.Product", on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    length_mm = models.PositiveIntegerField(null=True, blank=True)
    finish = models.CharField(max_length=30, choices=[
        ("mill", "Mill"),
        ("powdercoated", "Powdercoated"),
    ], default="mill")
    powder_color = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ["id"]
