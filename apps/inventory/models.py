"""
Inventory: Stock items and their state machine.
"""
from django.db import models
import uuid
from apps.core.models import TimestampedModel, Company
from apps.products.models import Product


# ─── Stock State Machine ───────────────────────────────────────────────────────
# A stock item moves through states. States are stored as strings
# rather than a separate model for simplicity.

VALID_STATES = [
    ("ordered",    "On Order"),
    ("received",   "Received"),
    ("stored",     "In Store"),
    ("cut",        "Cut"),
    ("prepared",   "Prepared for Assembly"),
    ("sent_powder", "Sent to Powder Coating"),
    ("returned_powder", "Returned from Powder Coating"),
    ("assembled",  "Assembled"),
    ("cleaned",    "Cleaned"),
    ("packed",     "Packed"),
    ("installed",  "Installed"),
    ("consumed",   "Consumed"),
    ("discarded",  "Discarded"),
]

OFFCUT_MIN_MM = {
    "frame": 494,
    "rail":  254,
    "blade": 279,
    "track": 254,
}


class StockItem(TimestampedModel):
    """
    A physical unit of stock.
    Grows from Material → Stock → Cut/Assembled → Sold.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stock_items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_items")
    barcode = models.CharField(max_length=50, blank=True)
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)

    # Length in mm (only meaningful when unit_type = BAR)
    length_mm = models.PositiveIntegerField(null=True, blank=True)

    # State machine
    state = models.CharField(max_length=30, choices=VALID_STATES, default="stored")

    # Where it lives
    bin_location = models.ForeignKey(
        "core.BinLocation", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="stock_items"
    )

    # Powder coating
    requires_powdercoat = models.BooleanField(default=False)
    powder_color = models.CharField(max_length=50, blank=True)

    # Cost tracking
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    # Links
    source_order = models.CharField(max_length=50, blank=True)  # PO / MO reference

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "state"]),
            models.Index(fields=["product", "state"]),
        ]

    def __str__(self):
        loc = f" @ {self.bin_location}" if self.bin_location else ""
        return f"{self.product.code} × {self.quantity} {self.product.unit_type}{loc}"

    @property
    def is_offcut(self):
        """True if this is an offcut short enough to potentially reuse."""
        if not self.length_mm or not self.product.extrusion:
            return False
        thresh = OFFCUT_MIN_MM.get(self.product.extrusion.category, 254)
        return self.length_mm < thresh


class Offcut(TimestampedModel):
    """
    An offcut resulting from a cutting operation.
    Kept for reuse when large enough to be useful.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="offcuts")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="offcuts")
    length_mm = models.PositiveIntegerField()
    quantity = models.DecimalField(max_digits=12, decimal_places=4, default=1)
    finish = models.CharField(max_length=30, choices=[("mill", "Mill"), ("powdercoated", "Powdercoated")], default="mill")
    powder_color = models.CharField(max_length=50, blank=True)
    bin_location = models.ForeignKey(
        "core.BinLocation", on_delete=models.SET_NULL,
        null=True, blank=True, related_name="offcuts"
    )
    # If already matched to a demand, it is reserved
    is_reserved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-length_mm"]

    def __str__(self):
        return f"Offcut {self.product.code} {self.length_mm}mm × {self.quantity}"
