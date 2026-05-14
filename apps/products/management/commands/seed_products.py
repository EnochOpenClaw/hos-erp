"""
Seed Products, ExtrusionTypes, MaterialCategories.

Usage:
  python manage.py seed_products
  python manage.py seed_products --reset
"""
import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.products.models import MaterialCategory, ExtrusionType, Product


class Command(BaseCommand):
    help = "Seed products catalogue"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete all products, extrusion types, and categories before seeding",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Wiping existing data…")
            Product.objects.all().delete()
            ExtrusionType.objects.all().delete()
            MaterialCategory.objects.all().delete()

        # ── Material Categories ──────────────────────────────────────────────
        # MaterialCategory has: name (unique), description, sort_order, default_markup_pct
        cat_data = [
            ("Frame",     "Outer frames for doors, windows, flyscreens, security barriers", 30),
            ("Rail",      "Horizontal members — top rails, bottom rails, mid rails",        30),
            ("Stile",     "Vertical edge members with or without lock cutouts",              30),
            ("Sash",      "Window sash profiles — double-hung and tilt-and-turn",           30),
            ("Track",     "Sliding door/channel rails — top and bottom",                    30),
            ("Blade",     "Louvre blade assemblies",                                        30),
            ("Hardware",  "Handles, locks, hinges, rollers, cylinders",                    20),
            ("Accessory", "Seals, weatherstrip, bead, glazing, fasteners",                 20),
            ("Mesh",      "Fibreglass insect mesh, aluminium mesh, security mesh",          30),
        ]
        cat_objects = {}
        for name, desc, markup in cat_data:
            cat, _ = MaterialCategory.objects.get_or_create(
                name=name,
                defaults={"description": desc, "default_markup_pct": markup},
            )
            cat_objects[name] = cat
        self.stdout.write(f"  {len(cat_objects)} categories")

        # ── Extrusion Types ────────────────────────────────────────────────
        # ExtrusionType has: name (unique), category (CharField choice), die_number,
        #   standard_bar_mm, kerf_mm, weight_per_mm, description, is_active
        # Category choices: frame | rail | blade | track | compensating | rod | hardware
        extr_data = [
            # Door frame extrusions
            ("STD DR 40x40mm Frame",        "frame",    "EFL-D-001", 6000, 3.0, "Standard 40×40mm aluminium door frame profile"),
            ("STD DR 45x45mm Frame",        "frame",    "EFL-D-002", 6000, 3.0, "Standard 45×45mm door frame profile"),
            ("HEAVY DR 50x50mm Frame",       "frame",    "EFL-D-003", 6000, 3.0, "Heavy-duty 50×50mm door frame for security"),
            ("SEC DR 40x40mm Frame",         "frame",    "EFL-D-004", 6000, 3.0, "Security door frame 40×40mm"),
            # Window frame extrusions
            ("STD WDW 30x30mm Frame",         "frame",    "EFL-W-001", 6000, 3.0, "Standard 30×30mm window frame"),
            ("STD WDW 35x35mm Frame",        "frame",    "EFL-W-002", 6000, 3.0, "Standard 35×35mm window frame"),
            ("WIND STEP 40x25mm Frame",       "frame",    "EFL-W-003", 6000, 3.0, "Step-frame for double-hung sash"),
            # Flyscreen frame extrusions
            ("FLY 20x10mm Screen Frame",    "frame",    "EFL-F-001", 6000, 3.0, "20×10mm flyscreen frame (standard)"),
            ("FLY 25x10mm Screen Frame",     "frame",    "EFL-F-002", 6000, 3.0, "25×10mm flyscreen frame (heavy-duty)"),
            ("FLY 25x25mm Corner Post",       "frame",    "EFL-F-003", 6000, 3.0, "25×25mm flyscreen corner post"),
            # Security barrier frame extrusions
            ("SEC 50x50mm Security Frame",   "frame",    "EFL-S-001", 6000, 3.0, "50×50mm heavy security barrier frame"),
            ("SEC 40x40mm Security Frame",   "frame",    "EFL-S-002", 6000, 3.0, "40×40mm security barrier frame"),
            # Door stile extrusions
            ("DR 40x40mm STILE LH",          "frame",    "EST-D-001", 6000, 3.0, "40×40mm door stile with lock prep — left hand"),
            ("DR 40x40mm STILE RH",          "frame",    "EST-D-002", 6000, 3.0, "40×40mm door stile with lock prep — right hand"),
            ("DR 45x45mm STILE LH",          "frame",    "EST-D-003", 6000, 3.0, "45×45mm heavy door stile — left hand"),
            ("DR 45x45mm STILE RH",          "frame",    "EST-D-004", 6000, 3.0, "45×45mm heavy door stile — right hand"),
            ("DR 40x40mm STILE NO LOCK",      "frame",    "EST-D-005", 6000, 3.0, "40×40mm plain door stile — no lock cutout"),
            # Door rail extrusions
            ("DR 40x40mm TOP RAIL",          "rail",     "ERA-D-001", 6000, 3.0, "40×40mm door top rail"),
            ("DR 40x40mm BOTTOM RAIL",       "rail",     "ERA-D-002", 6000, 3.0, "40×40mm door bottom rail with drainage groove"),
            ("DR 45x45mm TOP RAIL",           "rail",    "ERA-D-003", 6000, 3.0, "45×45mm heavy door top rail"),
            ("DR 45x45mm BOTTOM RAIL",       "rail",     "ERA-D-004", 6000, 3.0, "45×45mm heavy door bottom rail"),
            ("DR 40x40mm MID RAIL",          "rail",     "ERA-D-005", 6000, 3.0, "40×40mm door mid rail / transom"),
            # Window sash extrusions
            ("WDW 30x30mm SASH INNER",      "frame",     "ESA-W-001", 6000, 3.0, "30×30mm double-hung sash inner"),
            ("WDW 35x35mm SASH OUTER",       "frame",    "ESA-W-002", 6000, 3.0, "35×35mm double-hung sash outer frame"),
            ("WDW 25x40mm SASH T&T",          "frame",    "ESA-W-003", 6000, 3.0, "25×40mm tilt-and-turn sash"),
            # Track extrusions
            ("SLD 2-Rail TOP TRACK",          "track",   "ETK-S-001", 6000, 3.0, "2-rail sliding door top track"),
            ("SLD 3-Rail TOP TRACK",         "track",   "ETK-S-002", 6000, 3.0, "3-rail sliding door top track (triple)"),
            ("SLD BOTTOM GUIDE TRACK",       "track",   "ETK-S-003", 6000, 3.0, "Sliding door bottom guide track"),
            # Louvre blades
            ("LVR 150mm BLADE 0.9mm",        "blade",   "ELV-001",   6000, 3.0, "150mm wide louvre blade, 0.9mm wall"),
            ("LVR 150mm BLADE 1.2mm",         "blade",  "ELV-002",   6000, 3.0, "150mm wide louvre blade, 1.2mm heavy"),
            ("LVR 100mm BLADE",              "blade",   "ELV-003",   6000, 3.0, "100mm wide louvre blade"),
            # Hardware
            ("LOCK CYLINDER STANDARD",      "hardware", "EHD-001",      0, 0.0, "Standard cam lock cylinder"),
            ("HANDLE D-PULL 150mm",          "hardware", "EHD-002",      0, 0.0, "150mm D-pull door handle"),
            ("ROLLER SLIDING 20mm NYLON",   "hardware", "EHD-003",      0, 0.0, "20mm nylon roller for sliding doors"),
            ("HINGE PIANO 100mm",            "hardware", "EHD-004",      0, 0.0, "100mm piano hinge for doors"),
            ("LOCK DEADBOLT EURO",           "hardware", "EHD-005",      0, 0.0, "Euro profile deadbolt lock"),
            # Accessories
            ("SEAL FOAM DRAFT 10mm",        "hardware","EAC-001",       0, 0.0, "10mm foam draft seal (per metre)"),
            ("SEAL BRUSH DRAFT 12mm",        "hardware","EAC-002",       0, 0.0, "12mm brush draft seal (per metre)"),
            ("WEATHERSTRIP EPDM 15mm",       "hardware","EAC-003",      0, 0.0, "15mm EPDM weatherstrip (per metre)"),
            ("BEAD GLAZING 6mm",             "hardware","EAC-004",       0, 0.0, "6mm glazing bead"),
            ("SCREW M5x25 SS HEX BX100",    "hardware","EAC-005",       0, 0.0, "M5×25 SS hex head screw (box of 100)"),
            # Mesh
            ("MESH FG 18x14 ANTI-INSECT",    "hardware",    "EMH-001",       0, 0.0, "18×14 fibreglass insect mesh (per m²)"),
            ("MESH AL 9x9 HEAVY DUTY",       "hardware",    "EMH-002",       0, 0.0, "9×9 aluminium heavy-duty mesh (per m²)"),
            ("MESH SEC 1.6mm STEEL",         "hardware",    "EMH-003",       0, 0.0, "1.6mm steel security mesh (per m²)"),
            ("MESH PET FLYSCREEN",           "hardware",    "EMH-004",       0, 0.0, "PET mesh for flyscreen cutting (per m²)"),
        ]

        extr_objects = {}
        for name, cat_key, die, bar, kerf, desc in extr_data:
            extr, _ = ExtrusionType.objects.get_or_create(
                name=name,
                defaults={
                    "category":        cat_key,
                    "die_number":      die,
                    "standard_bar_mm": bar,
                    "kerf_mm":         kerf,
                    "description":     desc,
                },
            )
            extr_objects[name] = extr
        self.stdout.write(f"  {len(extr_objects)} extrusion types")

        # ── Products ────────────────────────────────────────────────────────
        # Product has: name, code (unique), category (FK), extrusion (FK),
        #   length_mm, colour, colour_code, unit_type, unit_cost, is_active
        products_data = [
            # Door frames
            ("STD DR 40x40 FRM MF 6M",   "PROD-EFL-D-001-M", "Frame", "STD DR 40x40mm Frame",        6000, "Mill",   "BAR"),
            ("STD DR 45x45 FRM MF 6M",   "PROD-EFL-D-002-M", "Frame", "STD DR 45x45mm Frame",        6000, "Mill",   "BAR"),
            ("HEAVY DR 50x50 FRM MF 6M",  "PROD-EFL-D-003-M", "Frame", "HEAVY DR 50x50mm Frame",      6000, "Mill",   "BAR"),
            ("SEC DR 40x40 FRM MF 6M",   "PROD-EFL-D-004-M", "Frame", "SEC DR 40x40mm Frame",        6000, "Mill",   "BAR"),
            # Window frames
            ("STD WDW 30x30 FRM MF 6M",   "PROD-EFL-W-001-M", "Frame", "STD WDW 30x30mm Frame",      6000, "Mill",   "BAR"),
            ("STD WDW 35x35 FRM MF 6M",  "PROD-EFL-W-002-M", "Frame", "STD WDW 35x35mm Frame",      6000, "Mill",   "BAR"),
            # Flyscreen frames
            ("FLY 20x10 SCR FRM MF 6M",   "PROD-EFL-F-001-M", "Frame", "FLY 20x10mm Screen Frame",   6000, "Mill",   "BAR"),
            ("FLY 25x10 SCR FRM MF 6M",   "PROD-EFL-F-002-M", "Frame", "FLY 25x10mm Screen Frame",   6000, "Mill",   "BAR"),
            ("FLY 25x25 CRN FRM MF 6M",  "PROD-EFL-F-003-M", "Frame", "FLY 25x25mm Corner Post",    6000, "Mill",   "BAR"),
            # Security frames
            ("SEC 50x50 FRM MF 6M",       "PROD-EFL-S-001-M", "Frame", "SEC 50x50mm Security Frame",  6000, "Mill",   "BAR"),
            ("SEC 40x40 FRM MF 6M",      "PROD-EFL-S-002-M", "Frame", "SEC 40x40mm Security Frame",  6000, "Mill",   "BAR"),
            # Door stiles
            ("DR 40x40 STL LH MF 6M",     "PROD-EST-D-001-M", "Stile", "DR 40x40mm STILE LH",       6000, "Mill",   "BAR"),
            ("DR 40x40 STL RH MF 6M",    "PROD-EST-D-002-M", "Stile", "DR 40x40mm STILE RH",       6000, "Mill",   "BAR"),
            ("DR 45x45 STL LH MF 6M",    "PROD-EST-D-003-M", "Stile", "DR 45x45mm STILE LH",       6000, "Mill",   "BAR"),
            ("DR 45x45 STL RH MF 6M",    "PROD-EST-D-004-M", "Stile", "DR 45x45mm STILE RH",       6000, "Mill",   "BAR"),
            ("DR 40x40 STL NL MF 6M",    "PROD-EST-D-005-M", "Stile", "DR 40x40mm STILE NO LOCK",  6000, "Mill",   "BAR"),
            # Door rails
            ("DR 40x40 TR MF 6M",        "PROD-ERA-D-001-M", "Rail",  "DR 40x40mm TOP RAIL",       6000, "Mill",   "BAR"),
            ("DR 40x40 BR MF 6M",         "PROD-ERA-D-002-M", "Rail",  "DR 40x40mm BOTTOM RAIL",    6000, "Mill",   "BAR"),
            ("DR 45x45 TR MF 6M",         "PROD-ERA-D-003-M", "Rail",  "DR 45x45mm TOP RAIL",       6000, "Mill",   "BAR"),
            ("DR 45x45 BR MF 6M",         "PROD-ERA-D-004-M", "Rail",  "DR 45x45mm BOTTOM RAIL",    6000, "Mill",   "BAR"),
            ("DR 40x40 MR MF 6M",         "PROD-ERA-D-005-M", "Rail",  "DR 40x40mm MID RAIL",       6000, "Mill",   "BAR"),
            # Window sashes
            ("WDW 30x30 SASH IN MF 6M",  "PROD-ESA-W-001-M", "Sash",  "WDW 30x30mm SASH INNER",   6000, "Mill",   "BAR"),
            ("WDW 35x35 SASH OUT MF 6M",  "PROD-ESA-W-002-M", "Sash",  "WDW 35x35mm SASH OUTER",   6000, "Mill",   "BAR"),
            # Sliding tracks
            ("SLD 2-RL TOP TRK 6M",       "PROD-ETK-S-001-M", "Track", "SLD 2-Rail TOP TRACK",      6000, "Mill",   "BAR"),
            ("SLD 3-RL TOP TRK 6M",      "PROD-ETK-S-002-M", "Track", "SLD 3-Rail TOP TRACK",      6000, "Mill",   "BAR"),
            # Louvre blades
            ("LVR 150mm BLADE 6M",        "PROD-ELV-001-M",   "Blade", "LVR 150mm BLADE 0.9mm",    6000, "Mill",   "BAR"),
            ("LVR 150mm BLADE 1.2mm 6M",  "PROD-ELV-002-M",   "Blade", "LVR 150mm BLADE 1.2mm",    6000, "Mill",   "BAR"),
            # Hardware
            ("LOCK CYL STD",             "PROD-EHD-001",     "Hardware","LOCK CYLINDER STANDARD",      0, "Mill",   "EACH"),
            ("HNDL D-PULL 150mm",         "PROD-EHD-002",     "Hardware","HANDLE D-PULL 150mm",          0, "Mill",   "EACH"),
            ("RLR SLIDE 20mm NYLON",      "PROD-EHD-003",     "Hardware","ROLLER SLIDING 20mm NYLON",   0, "Mill",   "EACH"),
            ("HNG PN 100mm",             "PROD-EHD-004",     "Hardware","HINGE PIANO 100mm",           0, "Mill",   "EACH"),
            # Mesh
            ("MESH FG 18x14 M2",          "PROD-EMH-001-M",  "Mesh",  "MESH FG 18x14 ANTI-INSECT",   0, "Mill",   "BAR"),
            ("MESH AL 9x9 M2",            "PROD-EMH-002-M",  "Mesh",  "MESH AL 9x9 HEAVY DUTY",      0, "Mill",   "BAR"),
            ("MESH SEC 1.6mm M2",         "PROD-EMH-003-M",  "Mesh",  "MESH SEC 1.6mm STEEL",         0, "Mill",   "BAR"),
            ("MESH PET FLY M2",           "PROD-EMH-004-M",  "Mesh",  "MESH PET FLYSCREEN",           0, "Mill",   "BAR"),
            # Accessories
            ("SCR M5x25 SS BX100",        "PROD-EAC-005",    "Accessory","SCREW M5x25 SS HEX BX100",    0, "Mill",   "EACH"),
        ]

        for name, code, cat_key, extr_name, length, colour, unit in products_data:
            extr = extr_objects.get(extr_name)
            if not extr:
                self.stdout.write(f"  WARNING: extrusion '{extr_name}' not found for {code}")
                continue
            Product.objects.get_or_create(
                code=code,
                defaults={
                    "name":        name,
                    "category":    cat_objects[cat_key],
                    "extrusion":   extr,
                    "colour":      colour,
                    "colour_code": "MILL" if colour == "Mill" else "RAL9003",
                    "unit_type":   unit,
                    "unit_cost":   "0.00",
                    "is_active":   True,
                },
            )

        prod_count = Product.objects.count()
        extr_count = ExtrusionType.objects.count()
        cat_count  = MaterialCategory.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f"\nDone — {cat_count} categories, {extr_count} extrusion types, {prod_count} products."
        ))