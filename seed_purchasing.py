#!/usr/bin/env python
"""
Seed script for HOS Purchasing workflow testing.
Run: python seed_purchasing.py
"""
import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'hos_erp.settings'
import django
django.setup()
from datetime import date

from apps.core.models import Company, Division
from apps.products.models import Product, MaterialCategory
from apps.purchasing.models import Supplier, PurchaseOrder, PurchaseOrderLine

COMPANY = Company.objects.get(name="OpenFactory Systems")

def ensure_division(code, name):
    div, _ = Division.objects.get_or_create(code=code, defaults={'name': name})
    return div

def ensure_category(name, markup=25):
    cat, _ = MaterialCategory.objects.get_or_create(name=name, defaults={'default_markup_pct': markup})
    return cat

def ensure_product(code, name, category, unit_cost=0, selling_price=0):
    prod, created = Product.objects.get_or_create(
        code=code,
        defaults={
            'name': name,
            'category': category,
            'unit_cost': unit_cost,
            'selling_price': selling_price,
        }
    )
    if not created:
        prod.category = category
        prod.unit_cost = unit_cost
        prod.selling_price = selling_price
        prod.save()
    return prod

def ensure_supplier(name, email='orders@supplier.com'):
    sup, _ = Supplier.objects.get_or_create(company=COMPANY, name=name, defaults={'email': email})
    return sup

def seed():
    print("Seeding divisions...")
    ensure_division('HW', 'Hardware')
    extrusion = ensure_division('EX', 'Extrusions')

    print("Seeding categories...")
    cat_hardware = ensure_category('Hardware', markup=30)
    cat_fasteners = ensure_category('Fasteners', markup=20)

    print("Seeding products...")
    p1 = ensure_product('MESH-001', 'PET Mesh 6mm 1220x2440', cat_hardware, unit_cost=285, selling_price=390)
    p2 = ensure_product('SCREW-001', 'Stainless Steel Screw 8g x 25mm (box/500)', cat_fasteners, unit_cost=95, selling_price=125)
    p3 = ensure_product('HWF-001', 'Corner Bracket 40x40 SS (box/100)', cat_hardware, unit_cost=145, selling_price=195)

    print("Seeding suppliers...")
    sup1 = ensure_supplier('Glass&Mesh Pro', 'orders@glassmeshpro.co.za')
    sup2 = ensure_supplier('FastenMaster SA', 'sales@fastenmaster.co.za')

    print("Creating test PO...")
    if PurchaseOrder.objects.filter(phase='requisition').count() == 0:
        po = PurchaseOrder.objects.create(
            company=COMPANY,
            division=extrusion,
            supplier=sup1,
            phase='requisition',
            reason='special_order',
            requires_quote=False,
            order_date=date.today(),
            notes='Test PO for workflow validation',
        )
        PurchaseOrderLine.objects.create(po=po, product=p1, ordered_qty=10, unit_price=285)
        PurchaseOrderLine.objects.create(po=po, product=p2, ordered_qty=5, unit_price=95)
        print("Created PO: " + po.po_number)
    else:
        po = PurchaseOrder.objects.filter(phase='requisition').first()
        print("Using existing PO: " + po.po_number)

    print("\nSeeded successfully!")
    print("  Divisions: " + str(Division.objects.count()))
    print("  Products: " + str(Product.objects.count()))
    print("  Suppliers: " + str(Supplier.objects.count()))
    print("  POs: " + str(PurchaseOrder.objects.count()))

if __name__ == '__main__':
    seed()