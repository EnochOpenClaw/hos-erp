# OpenFactory ERP — Project Plan

**Created:** 2026-05-06  
**Prepared by:** Enoch 👻  
**Based on:** `D:\OpenClawDev` (clean start) + `D:\Backup OC` (previous installation)

---

## What Is This?

**OpenFactory ERP** is a custom ERP system for **House of Supreme** — a Johannesburg-based aluminium shutter and louvre manufacturer. It manages:
- Product catalog (extrusions, hardware)
- Inventory (stock, offcuts, powder coating)
- Manufacturing (cutting optimization, assembly orders)
- Sales (quotes, orders)
- PDF reports, QR labels, cutting diagrams

---

## Source Code Review

### D:\OpenClawDev (Clean Foundation)
The clean initial development setup — good starting point.
- **Backend:** Django 6.0 + DRF, PostgreSQL 17
- **Frontend:** React 19 + Vite + TypeScript + Ant Design
- **Database:** 4 apps (core, inventory, manufacturing, sales), 24 models
- **Python venv:** Dependencies installed (PuLP, openpyxl, pandas, reportlab, qrcode)
- **Status:** Partial — API endpoints and frontend pages not yet connected

### D:\Backup OC (Previous Installation)
The more mature version with deeper implementation.
- **Backend:** Django apps with full manufacturing workflow
- **Cutting Optimizer:** MILP solver (PuLP), offcut tracking, waste calculation
- **Manufacturing → Cutting Job link:** Service layer with API actions
- **CLI commands:** `process_manufacturing_order`
- **PDF output:** Cutting diagrams, offcut labels, QR codes
- **Docs:** ERD, workflow diagrams, phase designs, offcut classification
- **Database:** SQLite with products, stock, cutting jobs, BOMs, assembly orders

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6.0 + Django REST Framework |
| Database | PostgreSQL 17 (dev: SQLite) |
| Async Tasks | Celery + Redis |
| Frontend | React 19 + TypeScript + Vite |
| UI Library | Ant Design 5 + Pro Components |
| State/Fetch | TanStack Query + Axios |
| MILP Solver | PuLP 3.x |
| Excel | openpyxl + pandas |
| PDF | reportlab |
| QR Codes | qrcode + Pillow |

---

## Recommended Architecture

```
openfactory-erp/
├── backend/
│   ├── apps/
│   │   ├── core/           # Company, Location, User, Role, Audit
│   │   ├── products/        # Product, ProductVariant, Category
│   │   ├── inventory/      # Stock, Offcut, StockMovement
│   │   ├── manufacturing/   # Job, CutPlan, BOM, AssemblyOrder
│   │   ├── cutting/        # MILP solver, patterns, offcut matcher
│   │   ├── sales/          # Customer, Quote, SalesOrder
│   │   └── reports/        # PDF generation, QR labels
│   ├── config/             # Django settings
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── pages/          # Dashboard, Products, Jobs, Inventory
│   │   ├── components/     # Reusable UI components
│   │   ├── api/            # Axios + TanStack Query hooks
│   │   └── types/          # TypeScript interfaces
│   └── package.json
├── docs/                   # Architecture, ERD, workflows
└── scripts/                # Setup, migration, seeding
```

---

## Phase 1: Foundation & Tools ✅ READY TO START

**Goal:** Get the development environment fully operational on WSL2.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Verify PostgreSQL 17 runs on WSL2 | 🔄 | Need to confirm |
| 1.2 | Confirm Python 3.14+ available | 🔄 | |
| 1.3 | Confirm Node.js 25 + npm available | 🔄 | |
| 1.4 | Clone/import project into WSL2 workspace | 🔄 | |
| 1.5 | Set up Python venv with all dependencies | 🔄 | |
| 1.6 | Run Django check, confirm DB connection | 🔄 | |
| 1.7 | Verify PuLP solver works | 🔄 | |
| 1.8 | Set up GitHub repo for the project | 🔄 | |

---

## Phase 2: Data Model & Database

**Goal:** Establish clean database models, migrate from SQLite backup if needed.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | Import models from `D:\OpenClawDev` (24 models) | 🔄 | Clean foundation |
| 2.2 | Apply simplified model from `SIMPLIFIED_MODEL.md` | 🔄 | Flatten Product/UnitType |
| 2.3 | Run migrations on PostgreSQL | 🔄 | |
| 2.4 | Load product fixtures (18 extrusions) | 🔄 | Already have products.json |
| 2.5 | Import existing data from `D:\Backup OC/db.sqlite3` | 🔄 | If needed |

---

## Phase 3: Backend API

**Goal:** Build REST API endpoints for all models.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Create serializers for all models | 🔄 | |
| 3.2 | Build ViewSets with CRUD + filters | 🔄 | |
| 3.3 | URL routing and API root | 🔄 | |
| 3.4 | Add authentication (JWT via `djangorestframework-simplejwt`) | 🔄 | |
| 3.5 | API documentation (Swagger/ReDoc) | 🔄 | |
| 3.6 | Connect frontend to API (Axios base URL) | 🔄 | |

---

## Phase 4: Frontend Foundation

**Goal:** Get React app talking to Django API.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | Verify Vite dev server runs | 🔄 | |
| 4.2 | Set up Axios with base URL + auth interceptor | 🔄 | |
| 4.3 | Build layout (sidebar, header, content area) | 🔄 | |
| 4.4 | Create Dashboard page | 🔄 | |
| 4.5 | Create Products page (table + filters) | 🔄 | |
| 4.6 | Create Inventory page | 🔄 | |
| 4.7 | Create Jobs page | 🔄 | |

---

## Phase 5: Cutting Optimization (Core Feature)

**Goal:** Port the MILP solver and integrate into the web app.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5.1 | Port MILP solver from `D:\Backup OC/cutoptimizer` | 🔄 | PuLP-based |
| 5.2 | Create `CutOptimizerService` in Django | 🔄 | |
| 5.3 | Build API endpoint: `POST /api/cutting/optimize/` | 🔄 | |
| 5.4 | Group optimization by (Extrusion \| Style \| Colour) | 🔄 | |
| 5.5 | Offcut tracking and reuse logic | 🔄 | |
| 5.6 | Display cutting plan in frontend | 🔄 | |

---

## Phase 6: Manufacturing Workflow

**Goal:** Full order-to-delivery workflow.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 6.1 | Quote → Sales Order flow | 🔄 | |
| 6.2 | Sales Order → Manufacturing Order | 🔄 | |
| 6.3 | Manufacturing Order → Cutting Job (service layer) | 🔄 | From `MANUFACTURING_TO_CUTTING_LINK.md` |
| 6.4 | CLI command: `process_manufacturing_order` | 🔄 | Already exists in backup |
| 6.5 | Assembly Order workflow | 🔄 | |
| 6.6 | Quality Control checkpoints | 🔄 | |

---

## Phase 7: PDF & Labels

**Goal:** Generate cutting diagrams and offcut labels.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7.1 | PDF cutting diagrams (visual bar layouts) | 🔄 | Uses reportlab |
| 7.2 | Cut list tables in PDF | 🔄 | |
| 7.3 | Offcut QR labels with bin locations | 🔄 | Uses qrcode + Pillow |
| 7.4 | Material summary reports | 🔄 | |
| 7.5 | Download from frontend | 🔄 | |

---

## Phase 8: Production Hardening

**Goal:** Get it ready for real use.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 8.1 | Switch from SQLite to PostgreSQL | 🔄 | |
| 8.2 | Set up Celery + Redis for async tasks | 🔄 | |
| 8.3 | Environment-based config (.env) | 🔄 | |
| 8.4 | Logging + error handling | 🔄 | |
| 8.5 | User permissions (RBAC by company) | 🔄 | |
| 8.6 | Staff training / handover docs | 🔄 | |

---

## Phase 9: Offcut Management System

**Goal:** Full offcut lifecycle.

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9.1 | Offcut classification thresholds | 🔄 | Per extrusion type |
| 9.2 | Storage location assignment (C1, C2...) | 🔄 | Sequential bin labeling |
| 9.3 | Offcut matching to new demand | 🔄 | Reuse logic |
| 9.4 | Offcut inventory UI | 🔄 | |

---

## Phase 10: Future Modules

| # | Module | Notes |
|---|--------|-------|
| 10.1 | Supplier portal | Supplier pricing, purchase orders |
| 10.2 | Production scheduling | Calendar view |
| 10.3 | Dashboard & analytics | Charts, KPIs |
| 10.4 | Email notifications | Customer/staff alerts |
| 10.5 | E-commerce product configurator | DIY website |

---

## Key Files Reference

**From D:\OpenClawDev:**
- `openfactory_erp/backend/settings.py` — Django settings
- `openfactory_erp/core/models.py` — 24 models across 4 apps
- `openfactory_erp/requirements.txt` — all Python deps
- `openfactory_erp/manufacturing/cutting/solver.py` — MILP optimizer
- `openfactory_erp/frontend/src/` — React app structure

**From D:\Backup OC (reference/implementation guide):**
- `docs/ERD.md` — Complete entity relationship diagram
- `docs/WORKFLOW_DIAGRAM.md` — Full manufacturing workflow
- `docs/SIMPLIFIED_MODEL.md` — Recommended simplified data model
- `docs/PHASE2_DESIGN.md` — Product & inventory design
- `MANUFACTURING_TO_CUTTING_LINK.md` — Service layer design
- `backend/apps/manufacturing/services.py` — ManufacturingService class
- `output/` — Sample PDFs and QR labels (demonstrates what's working)

---

## Decision Points Before We Start

1. **Database:** Stick with SQLite for dev, or go straight to PostgreSQL?
2. **Model complexity:** Use the 24-model structure from `D:\OpenClawDev`, or simplify per `SIMPLIFIED_MODEL.md`?
3. **Frontend:** Start from `D:\OpenClawDev`'s React app, or build fresh?
4. **GitHub:** Create a new repo or clone into `enoch-agent` workspace?
5. **Cutting optimizer:** Start with a working solver (from backup) or rebuild/test-first?

---

*Let's go through this together and decide the approach.*
