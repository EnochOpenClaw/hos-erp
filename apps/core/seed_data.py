"""
Seed data: Company, Divisions, Locations, BinLocations
Run with: python manage.py shell < apps/core/seed_data.py
"""
from apps.core.models import Company, Division, Location, BinLocation

def run():
    print("Seeding company and divisions...")

    # ── Company ──────────────────────────────────────────────────────────────
    company, _ = Company.objects.get_or_create(
        code="OFS",
        defaults={
            "name": "OpenFactory Systems",
            "tax_id": "",
            "email": "",
            "address": "",
        }
    )
    print(f"  Company: {company.name} ({company.code})")

    # ── Divisions ─────────────────────────────────────────────────────────────
    divisions = {}

    ho_divisions = [
        ("INT", "Internal Sales",      "head_office", None, 1),
        ("EXT", "External Sales",      "head_office", None, 2),
        ("MGT", "Management",         "head_office", None, 3),
        ("FAC", "Factory Management",  "head_office", None, 4),
        ("ADM", "Admin",               "head_office", None, 5),
        ("ACC", "Accounts",            "head_office", None, 6),
        ("REC", "Reception",           "head_office", None, 7),
    ]

    factory_divisions = [
        ("ALU", "Aluminium Shutter Factory", "factory", "alu",  10),
        ("FLY", "Flyscreen Factory",          "factory", "fly",  11),
        ("WDW", "Wood Factory",               "factory", "wdw",  12),
    ]

    for code, name, div_type, factory_type, order in ho_divisions + factory_divisions:
        div, created = Division.objects.get_or_create(
            code=code,
            defaults={
                "name": name,
                "division_type": div_type,
                "factory_type": factory_type,
                "parent": None,
                "sort_order": order,
            }
        )
        divisions[code] = div
        print(f"  {'Created' if created else 'Exists'} Division: {code} — {name}")

    # ── Locations ─────────────────────────────────────────────────────────────
    FACTORY_SECTIONS = [
        ("CUT",  "Cutting",             "factory_section"),
        ("PREP", "Preparation",         "factory_section"),
        ("ASSY", "Assembly",           "factory_section"),
        ("PACK", "Packing/Distribution","factory_section"),
    ]

    def create_location(div_code, loc_code, name, loc_type, parent=None):
        div = divisions[div_code]
        loc, created = Location.objects.get_or_create(
            division=div,
            code=loc_code,
            defaults={
                "name": name,
                "location_type": loc_type,
                "parent": parent,
            }
        )
        print(f"  {'Created' if created else 'Exists'} Location: {div_code}/{loc_code} — {name}")
        return loc

    locs = {}

    # Factory sections + storage
    for factory_code, _, _, _, _ in factory_divisions:
        # Sections
        for sec_code, sec_name, sec_type in FACTORY_SECTIONS:
            loc = create_location(factory_code, sec_code, sec_name, sec_type)
            locs[f"{factory_code}/{sec_code}"] = loc

        # General storage
        gen_store = create_location(factory_code, "GEN", "General Storage", "general_storage")
        locs[f"{factory_code}/GEN"] = gen_store

        # Offcut storage
        off_store = create_location(factory_code, "OFF", "Offcut Storage", "offcut_storage")
        locs[f"{factory_code}/OFF"] = off_store

    # Standalone stores
    standalone_stores = [
        ("WDW", "WDW_STORE", "Wood Store",     "store"),
        ("ALU", "ALU_STORE", "Aluminium Store", "store"),
        ("ALU", "GEAR",     "Gear Store",      "store"),
    ]
    for div_code, store_code, store_name, store_type in standalone_stores:
        loc = create_location(div_code, store_code, store_name, store_type)
        locs[f"{div_code}/{store_code}"] = loc

    # ── Bin Locations ──────────────────────────────────────────────────────────
    # 20 offcut bins per factory offcut storage
    for factory_code, _, _, _, _ in factory_divisions:
        off_loc = locs.get(f"{factory_code}/OFF")
        if off_loc:
            for i in range(1, 21):
                bin_name = f"OFF-{i:02d}"
                b, created = BinLocation.objects.get_or_create(
                    location=off_loc,
                    name=bin_name,
                    defaults={"barcode": f"{factory_code}-OFF-{i:02d}"}
                )
            print(f"  Created 20 offcut bins for {factory_code}/OFF")

    # 15 bins per standalone store
    store_bin_prefixes = {
        "WDW_STORE": "WDW-",
        "ALU_STORE": "ALU-",
        "GEAR":      "GR-",
    }
    for store_code, prefix in store_bin_prefixes.items():
        store_loc = locs.get(f"WDW/{store_code}") or locs.get(f"ALU/{store_code}")
        if store_loc:
            for i in range(1, 16):
                bin_name = f"{prefix}{i:02d}"
                b, created = BinLocation.objects.get_or_create(
                    location=store_loc,
                    name=bin_name,
                    defaults={"barcode": bin_name}
                )
            print(f"  Created 15 bins for {store_code}")

    print("\n✅ Seed complete!")


if __name__ == "__main__":
    run()
