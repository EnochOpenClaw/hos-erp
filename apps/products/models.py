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
    # Default markup % applied to products in this category when cost price updates
    default_markup_pct = models.DecimalField(max_digits=5, decimal_places=2, default=30.00,
                                             help_text="Default markup %% for products in this category")

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
    # Finish / colour attributes — blank means "from price list / unspecified"
    style = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=100, blank=True)
    colour_code = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    unit_type = models.CharField(max_length=20, choices=[
        ("BAR", "Bar (length)"),
        ("KG", "Kilogram"),
        ("EACH", "Each"),
        ("SET", "Set"),
    ], default="BAR")
    # Costing — updated automatically when invoice is posted
    unit_cost = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True,
                                     help_text="Last purchase cost price per unit")
    selling_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True,
                                         help_text="Current selling price (auto or manual)")
    # Markup override — if set, overrides category default for auto-price update
    markup_override = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True,
                                           help_text="Markup %% to apply instead of category default")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category__name", "name"]

    @staticmethod
    def generate_code(category, extrusion, colour_code, style):
        """
        Auto-generate product code from selected fields.
        Format: CAT-EXTR-COL
          CAT   = first 3 chars of category name, uppercase
          EXTR  = first 4 meaningful chars of extrusion name
          COL   = colour_code or style[0:2] or 'NC'
        """
        parts = []

        if category:
            parts.append(category.name.upper()[:3])
        else:
            parts.append('GEN')

        strip_words = {'type','profile','channel','track','stile','rail','louvre','slat','rod','bar'}
        if extrusion:
            name_words = extrusion.name.upper().split()
            meaningful = [w for w in name_words if w.lower() not in strip_words]
            ext_part = ''.join(w[:4] for w in (meaningful if meaningful else name_words))[:4]
            parts.append(ext_part or 'UNK')
        else:
            parts.append('UNK')

        col = (colour_code.upper()[:3] if colour_code else (style.upper()[:2] if style else 'NC'))
        parts.append(col)

        return '-'.join(parts)

    def save(self, *args, **kwargs):
        if not self.code or self.code.startswith('TMP'):
            self.code = self.generate_code(self.category, self.extrusion, self.colour_code, self.style)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} — {self.name}"