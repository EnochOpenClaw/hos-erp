"""
Products: Material, Product, ProductVariant
"""
from django.db import models
import uuid
from apps.core.models import TimestampedModel


class MaterialCategory(TimestampedModel):
    """Groups extrusions (Shutters, Flyscreens, Builders Hardware)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Material Categories"

    def __str__(self):
        return self.name


class ExtrusionType(TimestampedModel):
    """
    The type/shape of extrusion — Stile, Louvre, Rail, Bottom Track, etc.
    Each has a category (frame, rail, blade, track, compensating, rod, hardware).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=30, choices=[
        ("frame", "Frame"),
        ("rail", "Rail"),
        ("blade", "Blade/Louvre"),
        ("track", "Track"),
        ("compensating", "Compensating"),
        ("rod", "Rod"),
        ("hardware", "Hardware"),
    ])
    description = models.TextField(blank=True)
    # Weight per mm length (kg) — used for material costing
    weight_per_mm = models.DecimalField(
        max_digits=10, decimal_places=6, null=True, blank=True
    )
    die_number = models.CharField(max_length=50, blank=True)
    # Standard stock bar length
    standard_bar_mm = models.PositiveIntegerField(default=6300)
    # Kerf = saw blade thickness (default 4mm)
    kerf_mm = models.PositiveIntegerField(default=4)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class Product(TimestampedModel):
    """
    A sellable/manufacturable item.
    In its simplest form: just a name and type.
    Grows into: Material → Stock → Manufacturing → Sales.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(
        MaterialCategory, on_delete=models.SET_NULL, null=True,
        related_name="products"
    )
    extrusion = models.ForeignKey(
        ExtrusionType, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="products"
    )
    description = models.TextField(blank=True)
    unit_type = models.CharField(max_length=20, choices=[
        ("BAR", "Bar (length)"),
        ("KG", "Kilogram"),
        ("EACH", "Each"),
        ("SET", "Set"),
    ], default="BAR")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]

    def __str__(self):
        return f"{self.code} — {self.name}"
