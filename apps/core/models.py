"""
Core models: Company, Division, Location, BinLocation
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
    """Tenant root — the business itself"""
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


class Division(TimestampedModel):
    """
    Company divisions — head office divisions and factories.
    Each division has a PO_CODE used in purchase order naming.
    Factories have a factory_type; head office divisions have null.
    """
    DIVISION_TYPES = [
        ("head_office", "Head Office Division"),
        ("factory",     "Factory"),
    ]

    FACTORY_TYPES = [
        ("alu",  "Aluminium Shutter Factory"),
        ("fly",  "Flyscreen Factory"),
        ("wdw",  "Wood Factory"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=10, unique=True)  # ALU, FLY, WDW, INT, EXT, etc.
    division_type = models.CharField(max_length=20, choices=DIVISION_TYPES, default="head_office")
    factory_type = models.CharField(max_length=20, choices=FACTORY_TYPES, null=True, blank=True)
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="children"
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Divisions"

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def is_factory(self):
        return self.division_type == "factory"


class Location(TimestampedModel):
    """
    Any physical place — factory, store, section, storage area.
    Hierarchy: Division (factory) → Location (section/storage) → BinLocation
    Or: Division (head_office) → Location (office/store)
    """
    LOCATION_TYPES = [
        ("factory_section",   "Factory Section"),      # Cutting, Preparation, Assembly, Packing
        ("general_storage",  "General Storage"),       # Factory general storage
        ("offcut_storage",   "Offcut Storage"),         # Offcut bins
        ("store",            "Store"),                  # Aluminium Store, Wood Store, Gear Store
        ("office",           "Office"),                  # Reception, Admin areas
        ("staging",          "Staging Area"),
        ("quarantine",       "Quarantine"),
        ("shipping",        "Shipping"),
        ("receiving",        "Receiving"),
        ("powdercoat_in",    "Powder Coat In"),
        ("powdercoat_out",   "Powder Coat Out"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    division = models.ForeignKey(
        Division, on_delete=models.CASCADE,
        related_name="locations"
    )
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="children"
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    location_type = models.CharField(max_length=20, choices=LOCATION_TYPES)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["division", "name"]
        unique_together = [["division", "code"]]

    def __str__(self):
        return f"{self.division.code}/{self.code} — {self.name}"

    @property
    def full_path(self):
        parts = [self.division.code]
        if self.parent:
            parts.append(self.parent.code)
        parts.append(self.code)
        return " / ".join(parts)


class BinLocation(TimestampedModel):
    """
    Specific bin, shelf, or spot within a Location.
    Used for stock item storage and offcut labelling.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    location = models.ForeignKey(
        Location, on_delete=models.CASCADE, related_name="bins"
    )
    name = models.CharField(max_length=50)
    barcode = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["location", "name"]
        unique_together = [["location", "name"]]

    def __str__(self):
        return f"{self.location.division.code}/{self.location.code}/{self.name}"

    @property
    def full_code(self):
        return f"{self.location.division.code}-{self.location.code}-{self.name}"
