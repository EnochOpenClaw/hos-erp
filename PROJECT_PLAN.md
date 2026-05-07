# OpenFactory ERP — Master Project Plan
**Last updated:** 2026-05-06  
**Author:** Enoch 👻 + Craig  
**Status:** PLANNING PHASE — DO NOT BUILD

---

## What We Now Know

### Material Flow (Full Cycle)

```
PURCHASE ORDER
    ↓
MATERIAL RECEIVED → sorted into groups:
    ├── CONSUMABLES       (Cleaning materials, silicone, etc.)
    ├── GEAR STOCK         (Screws, grommets, end caps, etc.)
    │       ├── Internal gear (assembly of products)
    │       └── External gear (sent in job packets)
    └── EXTRUSIONS/WOOD    (Aluminium or wood, mill or powdercoated)
            ↓
            Stored in stock
            ↓
            ↓  ← CONTROL SHEET arrives (sale with sizing)
            ↓
JOB DESIGN
    ├── System generates cut list (extrusion + length + quantity per opening)
    ├── System generates gear list (internal + external per opening)
    ├── Cut optimizer runs:
    │       1. Check offcut storage first → match suitable offcuts
    │       2. Only then assign full stock lengths
    │       → Output: cut plan with bar assignments + offcut labels
    ↓
ISSUE SHEET → issued to factory
    └── Specifies extrusion type + colour
            ↓
EXTRUSIONS SENT FOR POWDERCOATING (if required)
    ↓
RECEIVED BACK FROM POWDERCOATING
    ↓
RECEIVING QC CHECK
            ↓
CUTTING STAGE (cut optimizer applied again here)
            ↓
ASSEMBLY
            ↓
...rest of manufacturing flow to delivery
```

### Control Sheet
The document that arrives with a sale — contains the sizing for each opening. This is the trigger for the entire job design process. The system will use this to:
- Look up the product configuration
- Generate cut requirements
- Generate gear requirements
- Run the cut optimizer

### Issue Sheet
The document that pulls stock from the warehouse to the factory floor. Specifies what extrusions, what colour, what quantities.

### Cut Optimizer Role
1. **Design time:** First optimizer run when job is designed — determines how to cut each extrusion, preferring offcuts from storage
2. **Production time:** Second optimizer run at cutting stage — actual cutting list for the factory floor

### Offcut Strategy
- Offcuts are stored in labelled bin locations
- When designing a job, the optimizer must FIRST search available offcuts that match (extrusion type + finish + colour + adequate length)
- Only unmatched demand gets assigned to full stock lengths
- Offcuts below the minimum threshold for a given extrusion category are flagged or discarded

---

## Point 3 — Purchase Order Naming Convention

**Suggestion:** Format: `PO-{YEAR}{MONTH}-{SEQUENCE}`  
Example: `PO-202605-001`

This gives you:
- Year + month for easy filing/filtering
- Sequential number resets each month (or year if you prefer)
- Sortable, unique, meaningful

Alternative (if you prefer supplier-based):
`PO-{SUPPLIER_CODE}-{YEAR}{MONTH}-{SEQ}`  
Example: `PO-ALU-202605-001`

---

## Point 4 — Product Categorisation (NEEDS RESEARCH)

**The problem:** Not all gear has an extrusion type. Not all products are gear. A single hierarchical category may not fit.

**Research approach to take:**
- How do ERPs like Odoo, ERPNext, or DEAR Accounting handle this?
- Two-level categorisation: Type (Consumable / Hardware / Raw Material / Finished Goods) → Sub-category
- A product may have multiple "roles" — it can be a raw material, a component, and a finished product simultaneously
- Gear that is used in assembly = BOM component
- Gear that is sent in packets = listed on the job as a separate requirement, not in BOM

**Proposed research tasks:**
1. Look at how Odoo/ERPNext categorise products with multiple roles
2. Understand the difference between "Bill of Materials components" and "packet items"
3. Determine if Gear needs its own app or if it lives in products/inventory

---

## Architecture Decision

| Layer | Technology (confirmed) |
|-------|------------------------|
| Backend | Django 6 + DRF |
| Database | PostgreSQL 17 |
| Async Tasks | Celery + Redis |
| Frontend | React 19 + Vite + TypeScript + Ant Design |
| MILP Solver | PuLP |
| PDF | reportlab |
| QR Codes | qrcode + Pillow |

---

## Proposed App Structure

```
apps/
├── core/              Company, Warehouse, Zone, BinLocation
├── products/           Product, MaterialCategory, ExtrusionType
│                       (may split into products/ + gear/ after research)
├── inventory/          StockItem, Offcut, StockMovement
├── purchasing/         PurchaseOrder, PurchaseOrderLine, Supplier ← NEW
├── manufacturing/      Job, CutRequirement, CutPlan, CutBar, BOM, BOMLine
├── cutting/            CutOptimizerService, OffcutMatcher ← NEW (solver app)
├── powdercoat/         PowdercoatJob, PowdercoatReceive ← NEW
├── sales/              Customer, Quote, QuoteLine, SalesOrder, SalesOrderLine
│                       ControlSheet ← NEW
└── reports/            PDF generation, QR labels, cutting diagrams
```

**New apps to add:** `purchasing/`, `cutting/`, `powdercoat/`, `sales.ControlSheet`

---

## Proposed Data Model Extensions

### products/
- [x] `MaterialCategory` — groups extrusions (Shutters, Flyscreens, Builders Hardware)
- [x] `ExtrusionType` — Stile, Louvre, Rail, Bottom Track, etc. + category + standard_bar_mm + kerf_mm
- [x] `Product` — name, code, category, extrusion, unit_type (BAR/KG/EACH/SET)

**NEEDS RESEARCH — decide after study:**
- `GearCategory` — grouping for hardware items
- Whether Gear = separate model/app or same Product model with flags
- `ConsumableCategory` — grouping for consumables

### inventory/
- [x] `StockItem` — state machine (VALID_STATES as listed above)
- [x] `Offcut` — offcut with bin_location, is_reserved, finish, powder_color

**NEEDS DESIGN:**
- `StockMovement` — audit trail for all stock state transitions (WHO did WHAT to WHICH stock item and WHEN)
- Where does the Issue Sheet live? → manufacturing or inventory?
- Powdercoat receiving flow — does it create a new StockItem or update the existing one?

### purchasing/ ← NEW APP
- `Supplier` — name, code, email, phone, address, lead_time_days
- `PurchaseOrder` — po_number, supplier, status, order_date, expected_date
- `PurchaseOrderLine` — product, quantity, unit_price, received_qty
- `GoodsReceivedNote` — grn_number, po_reference, received_date, notes
- `GoodsReceivedNoteLine` — product, ordered_qty, received_qty, condition_notes

### manufacturing/
- [x] `Job` — job_number, status, source_order
- [x] `CutRequirement` — product, length_mm, quantity, finish, powder_color, allow_offcut_match
- [x] `CutPlan` — group_key, bars_used, waste_pct, status
- [x] `CutBar` — bar_length_mm, cuts_json, offcut_mm
- [x] `BOM` / `BOMLine` — recipe for finished product

**NEEDS DESIGN:**
- `IssueSheet` — links a Job to the StockItems issued from inventory to the factory
- `IssueSheetLine` — product, qty_issued, stock_item_reference
- How does a Job link to a SalesOrder? (sales_order FK)
- How does a Job get created from a Control Sheet? (service layer)

### powdercoat/ ← NEW APP
- `PowdercoatJob` — job_reference, supplier, status, sent_date, due_date, colour
- `PowdercoatReceive` — received_date, condition_check, notes, linked_powdercoat_job
- Should receiving create a new StockItem (now finished) or update the existing one?

### cutting/ ← NEW APP
- `CutOptimizerService` — port the PuLP MILP solver here
- Offcut matching logic (group by extrusion + finish + colour, match by length >= required)
- Design-phase optimizer vs production-phase optimizer — same service, different inputs?

### sales/
- [x] `Customer`, `Quote`, `QuoteLine`, `SalesOrder`, `SalesOrderLine`
- `ControlSheet` ← NEW — links to SalesOrder, captures per-opening sizing data
- `ControlSheetLine` ← NEW — per-opening details (width, height, product config, notes)

---

## Master Phased Build Plan

### PHASE 0: Foundation (Infrastructure)
*Goal: Confirm everything works before building features*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.1 | PostgreSQL 17 Docker container running | 🔄 | |
| 0.2 | Redis Docker container running | 🔄 | |
| 0.3 | Django connects to PostgreSQL | 🔄 | |
| 0.4 | All apps migrate cleanly | 🔄 | |
| 0.5 | Django admin accessible | 🔄 | |
| 0.6 | Frontend Vite server runs | 🔄 | |
| 0.7 | API base URL connected | 🔄 | |

### PHASE 1: Core Reference Data
*Goal: Build the foundation that all other modules depend on*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 1.1 | Material entry (CRUD) — products/Product + MaterialCategory + ExtrusionType | 🔄 | **Craig priority start** — for invoice entry |
| 1.2 | Seed data: existing 18 extrusion types | 🔄 | |
| 1.3 | Location entry (CRUD) — core/Warehouse + Zone + BinLocation | 🔄 | |
| 1.4 | Seed data: bin locations | 🔄 | |
| 1.5 | Supplier CRUD — purchasing/Supplier | 🔄 | |
| 1.6 | **Research: Gear categorisation** — determine model for hardware items | 🔄 | **Do this before building gear** |
| 1.7 | Gear entry (CRUD) — based on research outcome | 🔄 | |

### PHASE 2: Purchasing & Receiving
*Goal: Material ordering and receiving workflow*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 2.1 | PurchaseOrder CRUD + lines | 🔄 | |
| 2.2 | PO → auto-create Product entry if new material | 🔄 | Tied to point 1.1 |
| 2.3 | GoodsReceivedNote (GRN) workflow | 🔄 | |
| 2.4 | GRN → auto-create StockItem (state = received → stored) | 🔄 | |
| 2.5 | Invoice entry → select from existing Product list | 🔄 | **Craig priority** |
| 2.6 | Receiving QC check step | 🔄 | |

### PHASE 3: Cutting Optimizer Core
*Goal: The heart of the system — MILP solver + offcut matching*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 3.1 | Port PuLP MILP solver to `cutting/` app | 🔄 | |
| 3.2 | `OffcutMatcher` service — match offcuts before full stock | 🔄 | |
| 3.3 | API endpoint: `POST /api/cutting/optimize/` | 🔄 | |
| 3.4 | Design-phase optimizer (offcut-first, generates CutPlan) | 🔄 | |
| 3.5 | Production-phase optimizer (cutting list for factory floor) | 🔄 | |
| 3.6 | Offcut lifecycle: creation → storage → matching → reservation → use | 🔄 | |
| 3.7 | Offcut minimum thresholds per extrusion category | 🔄 | |

### PHASE 4: Job Design & Issue Sheets
*Goal: Control Sheet → Job Design → Issue Sheet flow*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 4.1 | ControlSheet model + CRUD | 🔄 | |
| 4.2 | ControlSheetLine model + per-opening sizing | 🔄 | |
| 4.3 | JobDesignService — generates CutRequirements from ControlSheet | 🔄 | |
| 4.4 | Gear list generation (internal + external per opening) | 🔄 | |
| 4.5 | IssueSheet model + CRUD | 🔄 | |
| 4.6 | IssueSheet → deduct StockItem quantities | 🔄 | |
| 4.7 | Job → auto-generate CutRequirements + GearRequirements | 🔄 | |
| 4.8 | Job status transitions (pending → cutting → completed) | 🔄 | |

### PHASE 5: Powder Coating Workflow
*Goal: Send stock out → receive it back finished*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 5.1 | PowdercoatJob model + CRUD | 🔄 | |
| 5.2 | Mark StockItems as `sent_powder` (state transition) | 🔄 | |
| 5.3 | PowdercoatReceive workflow | 🔄 | |
| 5.4 | Receive → update StockItem state + powder_color | 🔄 | |
| 5.5 | QC check on receive | 🔄 | |

### PHASE 6: Manufacturing Workflow
*Goal: Full order-to-delivery flow*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 6.1 | SalesOrder → ManufacturingOrder link | 🔄 | |
| 6.2 | ManufacturingOrder → Job creation | 🔄 | |
| 6.3 | BOM per finished product | 🔄 | |
| 6.4 | BOMLine — internal gear + external gear + extrusion requirements | 🔄 | |
| 6.5 | AssemblyOrder workflow | 🔄 | |
| 6.6 | StockItem state transitions (cut → prepared → assembled → etc.) | 🔄 | |

### PHASE 7: PDF & Labels
*Goal: Generate the physical documents*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 7.1 | Cutting diagram PDF (visual bar layouts) | 🔄 | Uses reportlab |
| 7.2 | Issue Sheet PDF | 🔄 | |
| 7.3 | Offcut QR labels with bin locations | 🔄 | |
| 7.4 | Control Sheet PDF | 🔄 | |
| 7.5 | Download from frontend | 🔄 | |

### PHASE 8: Sales & Quotes
*Goal: Quote → Order → Control Sheet flow*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 8.1 | Quote CRUD + lines | 🔄 | |
| 8.2 | Quote → SalesOrder conversion | 🔄 | |
| 8.3 | Control Sheet generation from SalesOrder | 🔄 | |
| 8.4 | Sales dashboard | 🔄 | |

### PHASE 9: Stock Movement Audit Trail
*Goal: Every stock state change is logged*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 9.1 | StockMovement model + auto-log on every transition | 🔄 | |
| 9.2 | Stock history view (per StockItem) | 🔄 | |
| 9.3 | Audit trail in admin | 🔄 | |

### PHASE 10: Frontend — Full UI
*Goal: All modules have UI pages*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 10.1 | Dashboard | 🔄 | |
| 10.2 | Products page (table + filters + create) | 🔄 | |
| 10.3 | Inventory page (stock table + state filters) | 🔄 | |
| 10.4 | Purchasing pages (PO + GRN) | 🔄 | |
| 10.5 | Jobs page (kanban or table + CutPlan view) | 🔄 | |
| 10.6 | Cutting optimizer UI (input + results + cutting diagram) | 🔄 | |
| 10.7 | Powder coating pages | 🔄 | |
| 10.8 | Sales pages | 🔄 | |
| 10.9 | Reports pages | 🔄 | |

### PHASE 11: Production Hardening
*Goal: Production-ready*

| # | Task | Status | Notes |
|---|------|--------|-------|
| 11.1 | Celery + Redis for async tasks | 🔄 | |
| 11.2 | JWT authentication | 🔄 | |
| 11.3 | User permissions (RBAC by company) | 🔄 | |
| 11.4 | Environment config (.env) | 🔄 | |
| 11.5 | Error handling + logging | 🔄 | |
| 11.6 | API documentation (Swagger/ReDoc) | 🔄 | |

---

## Decisions Still Needed Before Phase 1

### D1: PO Naming Convention
**Recommendation:** `PO-{YYYYMM}-{NNN}` e.g. `PO-202605-001`  
Craig — confirm or choose your own format.

### D2: Product Categorisation (Research Required)
**Recommend we pause Phase 1.1 (Products) briefly to do the research first.**  
Once we know whether gear is a separate model or a flag on Product, we can seed all products correctly the first time and avoid data migrations later.

**Research question:** Should we tackle this ourselves using web search + reasoning, or do you want me to look at how an established ERP (Odoo/ERPNext) solves this, then adapt from there?

### D3: Issue Sheet Storage
Where should Issue Sheet records live?
- **Option A:** `manufacturing/` app (Job issues stock to factory floor)
- **Option B:** `inventory/` app (stock movement from store)
- **Option C:** Separate `logistics/` app

**My recommendation:** `manufacturing/` — it's tied to a job and the factory flow.

### D4: StockItem — One Record Per Batch or Per Bar?
When you receive a PO, is each bar a separate StockItem, or do you batch them into one record with quantity > 1?
- **One record per bar** — easier to track individually, barcodes make this manageable
- **One record per batch** — less records, harder to track individual cuts

**My recommendation:** One record per bar. Simpler to track, easier to handle offcuts, barcode-ready.

### D5: Gear List — Where Does It Live in the Data Model?
The gear list (internal + external) is generated at job design time. It is:
- Listed on the **Issue Sheet** alongside extrusion requirements
- **Not a StockItem deduction** at design time — it gets deducted from stock at packing/shipping

**My recommendation:** `JobGearRequirement` model in `manufacturing/` with a flag `is_external` (goes in job packets vs stays for assembly).

---

## Immediate Next Steps (if you agree)

1. **Confirm PO naming convention (D1)**
2. **I do research on product categorisation (D2)**
3. **Once D1+D2 are resolved → build Phase 1 (Core Reference Data)**
4. **Phase 2 (Purchasing & Receiving) — invoice entry start**
5. **Phase 3 (Cutting Optimizer) — the core engine**
6. Then Phase 4+ (Job Design, Powdercoat, Manufacturing, Sales)

---

*This plan is a living document. Update it as we go.*
