# HOS ERP

> House of Supreme — Manufacturing & Inventory Management System

## Stack

- **Backend:** Django 6 + Django REST Framework + PostgreSQL 17
- **Frontend:** React 19 + Vite + TypeScript + Ant Design
- **Solver:** PuLP (cutting optimizer)
- **Cache/Workers:** Redis + Celery

## Quick Start

```bash
# 1. Clone
git clone https://github.com/EnochOpenClaw/hos-erp.git
cd hos-erp

# 2. Python venv
python3 -m venv ~/.venv/hos-erp
source ~/.venv/hos-erp/bin/activate
pip install -r requirements.txt

# 3. PostgreSQL (Docker)
docker run -d --name hos-postgres -p 5432:5432 \
  -e POSTGRES_DB=hos_erp -e POSTGRES_USER=hos_erp \
  -e POSTGRES_PASSWORD=H0s3rp\!SQL postgres:17-alpine

# 4. Redis (Docker)
docker run -d --name hos-redis -p 6379:6379 redis:7-alpine

# 5. Django
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser   # admin / H0s3rp!Admin
python manage.py runserver 0.0.0.0:8000

# 6. Frontend (new terminal)
cd frontend && npm install && npm run dev
```

- Django API: http://localhost:8000
- Admin UI: http://localhost:8000/admin
- Frontend: http://localhost:5173

## App Structure

| App | Purpose |
|---|---|
| `core` | Company, Warehouse, Zone, BinLocation |
| `products` | MaterialCategory, ExtrusionType, Product |
| `inventory` | StockItem, Offcut |
| `manufacturing` | Job, CutRequirement, CutPlan, CutBar, BOM |
| `sales` | Customer, Quote, SalesOrder |
| `reports` | PDF generation, QR labels, cutting diagrams |

## Architecture Notes

**Start simple, grow up:** The data model begins at Materials and builds up in layers:

```
Material → StockItem (with state machine) → Manufacturing
         → Assembly → Finished Product → Sales → Online Sales
```

**Cutting optimizer:** Built from scratch using PuLP. Works per-extrusion-type + finish + colour group.

**State machine:** StockItems track state transitions (stored → cut → prepared → assembled → etc.)

## Repo

https://github.com/EnochOpenClaw/hos-erp