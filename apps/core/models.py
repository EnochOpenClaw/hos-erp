"""
Core models: Company, Location, User (base RBAC)
"""
from django.db import models
import uuid


class TimestampedModel(models.Model):
    """Abstract base with created_at / updated_at"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimestampedModel):
    """Tenant root — each customer/branch is a company"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=30, unique=True)
    tax_id = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Warehouse(TimestampedModel):
    """Top-level location (e.g. Shutter Factory, Flyscreen Factory)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="warehouses"
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]
        unique_together = [["company", "code"]]

    def __str__(self):
        return f"{self.company.code}/{self.code} — {self.name}"


class Zone(TimestampedModel):
    """Zone within a warehouse (RACK, TABLE, STAGING, etc.)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    warehouse = models.ForeignKey(
        Warehouse, on_delete=models.CASCADE, related_name="zones"
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    zone_type = models.CharField(max_length=30, choices=[
        ("RACK", "Rack (items > 1040mm)"),
        ("TABLE", "Table/Crate (items ≤ 1040mm)"),
        ("STAGING", "Factory Staging"),
        ("POWDERCOAT_IN", "Powder Coat In"),
        ("POWDERCOAT_OUT", "Powder Coat Out"),
        ("QUARANTINE", "Quarantine"),
        ("SHIPPING", "Shipping"),
        ("RECEIVING", "Receiving"),
    ], default="RACK")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["warehouse", "name"]
        unique_together = [["warehouse", "code"]]

    def __str__(self):
        return f"{self.warehouse}/{self.code} ({self.zone_type})"


class BinLocation(TimestampedModel):
    """Specific bin within a zone (e.g. C1, C2-SB-P01)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    zone = models.ForeignKey(
        Zone, on_delete=models.CASCADE, related_name="bins"
    )
    name = models.CharField(max_length=50)
    barcode = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["zone", "name"]
        unique_together = [["zone", "name"]]

    def __str__(self):
        return f"{self.zone}/{self.name}"

    @property
    def full_code(self):
        return f"{self.zone.warehouse.code}-{self.zone.code}-{self.name}"
