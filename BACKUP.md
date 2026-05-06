# HOS ERP — Backup & Restore Guide
**Last updated:** 2026-05-06 01:52 PDT

## GitHub
- **Repo:** https://github.com/EnochOpenClaw/hos-erp
- **Branch:** master
- Commits (newest first):
  1. `85491648` — Add README, start script, env example
  2. `7f939163` — Add proper .gitignore
  3. `b9618b86` — Add frontend scaffold: React 19 + Vite + Ant Design + TypeScript
  4. `afcc1682` — Initial commit: HOS ERP foundation — Django 6 + PostgreSQL 17 + React ready

## Clone (after reboot / fresh clone)
```bash
git clone https://github.com/EnochOpenClaw/hos-erp.git
cd hos-erp
```

## Docker Services (start first)
```bash
# PostgreSQL 17
docker run -d --name hos-postgres -p 5432:5432 \
  -e POSTGRES_DB=hos_erp -e POSTGRES_USER=hos_erp \
  -e POSTGRES_PASSWORD=H0s3rp\!SQL \
  -v hos_postgres_data:/var/lib/postgresql/data \
  postgres:17-alpine

# Redis 7
docker run -d --name hos-redis -p 6379:6379 redis:7-alpine
```

## Python Setup
```bash
python3 -m venv ~/.venv/hos-erp
source ~/.venv/hos-erp/bin/activate
pip install -r requirements.txt
```

## Django Setup
```bash
cp .env.example .env
python manage.py migrate        # DB schema already created, idempotent
# Superuser (already exists, recreate if needed):
python manage.py shell -c "from django.contrib.auth import get_user_model; \
  User = get_user_model(); \
  User.objects.filter(username='admin').delete(); \
  User.objects.create_superuser('admin', 'admin@houseofsupreme.co.za', 'H0s3rp!Admin')"
python manage.py runserver 0.0.0.0:8000
```

## Frontend
```bash
cd frontend && npm install && npm run dev
```

## What's in the DB (seed data — already loaded)
- Company: HOS (House of Supreme)
- 2 Warehouses: SHUTTER (Shutter Factory), FLY (Flyscreen Factory)
- 9 Zones: RACK_A/B/C, TABLE_A, STAGING, POWDER_IN/OUT, RACK_1, TABLE_1
- 18 ExtrusionTypes: Stile, L-Frame, Z-Frame, Louvre, Louvre Holder,
  Large Rails, Small Rails, Midrail, Top Track, Bottom Track,
  Top F/U Compensating, J/U Compensating Channel, Tension/Tilt/Push Rod, Rail Covers
- 3 MaterialCategories: Aluminium Shutters, Flyscreen, Hardware
- Superuser: admin / H0s3rp!Admin

## Project Structure
```
hos-erp/
├── apps/
│   ├── core/          # Company, Warehouse, Zone, BinLocation
│   ├── products/      # MaterialCategory, ExtrusionType, Product
│   ├── inventory/     # StockItem (state machine), Offcut
│   ├── manufacturing/ # Job, CutRequirement, CutPlan, CutBar, BOM
│   ├── sales/          # Customer, Quote, SalesOrder
│   └── reports/       # PDF / QR (placeholder)
├── frontend/          # React 19 + Vite + AntD + TypeScript
├── hos_erp/           # Django project settings
├── manage.py
├── requirements.txt
├── start.sh
└── .env.example
```

## Redis (already running)
```bash
docker run -d --name hos-redis -p 6379:6379 redis:7-alpine
```

## Questions to answer after reboot
1. Cutting optimizer — server-side or frontend-callable? Offcut matching before or inside optimizer?
2. Stock state machine — review the 12 states?
3. PO / MO number format?
4. ProductVariant for colours/sizes now or later?
5. Frontend page build order — Inventory → Manufacturing first?