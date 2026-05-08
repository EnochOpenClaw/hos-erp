"""
Seed data: Material Categories + Extrusion Types
Run with: python manage.py shell < apps/products/seed_data.py
"""
from apps.products.models import MaterialCategory, ExtrusionType


def run():
    print("Seeding material categories and extrusion types...")

    # ── Material Categories ─────────────────────────────────────────────────
    categories = [
        ("Shutters",    "Aluminium shutter components",       1),
        ("Flyscreens",  "Flyscreen frame and mesh components", 2),
        ("Builders Hardware", "General hardware and fasteners", 3),
    ]

    cats = {}
    for name, desc, order in categories:
        cat, created = MaterialCategory.objects.get_or_create(
            name=name,
            defaults={"description": desc, "sort_order": order}
        )
        cats[name] = cat
        print(f"  {'Created' if created else 'Exists'} MaterialCategory: {name}")

    # ── Extrusion Types ─────────────────────────────────────────────────────
    extrusions = [
        # Shutters (frame category)
        ("Stile",             "frame",   6300, 4, "Standard stile profile"),
        ("Louvre",            "blade",   6300, 4, "Louvre/blade extrusion"),
        ("Rail",              "rail",    6300, 4, "Horizontal rail"),
        ("Bottom Track",      "track",   6300, 4, "Bottom mounting track"),
        ("Top Track",         "track",   6300, 4, "Top track for shutter"),
        ("Compensating",      "compensating", 6300, 4, "Compensating profile"),
        ("Side Channel",      "frame",   6300, 4, "Vertical side channel"),
        ("Hood Channel",      "frame",   6300, 4, "Top hood/channel"),
        # Flyscreens (track + frame)
        ("Flyscreen Frame",   "frame",   6300, 4, "Standard flyscreen frame"),
        ("Flyscreen Rail",    "rail",    6300, 4, "Flyscreen rail"),
        ("Flyscreen Brush",   "rod",     6300, 4, "Brush strip for flyscreen"),
        ("Flyscreen Clip",    "hardware", 1000, 2, "Flyscreen clip/holder"),
        # Builders hardware
        ("Rod",               "rod",     1000, 3, "General rod stock"),
        ("Tie Bar",          "rod",     1000, 3, "Tie bar for shutter"),
        ("Battens",          "rail",    6000, 4, "Wood or aluminium battens"),
        # Additional profiles
        ("Slat",              "blade",   6300, 4, "Slat profile for blinds/shutters"),
        ("Weather Seal",      "rod",     1000, 2, "Rubber/silicone weather seal"),
        ("Clip Profile",      "hardware", 1000, 2, "General purpose clip profile"),
    ]

    for name, category, std_bar, kerf, desc in extrusions:
        ext, created = ExtrusionType.objects.get_or_create(
            name=name,
            defaults={
                "category": category,
                "standard_bar_mm": std_bar,
                "kerf_mm": kerf,
                "description": desc,
            }
        )
        print(f"  {'Created' if created else 'Exists'} ExtrusionType: {name} ({category})")

    print("\n✅ Product seed complete!")


if __name__ == "__main__":
    run()