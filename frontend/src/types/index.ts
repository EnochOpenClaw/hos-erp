// ─── Core ─────────────────────────────────────────────────────────────────────

export interface Company {
  id: string
  name: string
  code: string
  tax_id: string
  email: string
  phone: string
  address: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Division {
  id: string
  name: string
  code: string
  division_type: 'head_office' | 'factory'
  division_type_display: string
  factory_type: 'alu' | 'fly' | 'wdw' | null
  factory_type_display: string | null
  parent: string | null
  is_active: boolean
  sort_order: number
  is_factory: boolean
  location_count: number
  created_at: string
  updated_at: string
}

export interface Location {
  id: string
  division: string
  division_code: string
  division_name: string
  parent: string | null
  name: string
  code: string
  location_type: string
  location_type_display: string
  is_active: boolean
  full_path: string
  bin_count: number
  created_at: string
  updated_at: string
}

export interface BinLocation {
  id: string
  location: string
  division_code: string
  location_code: string
  location_name: string
  name: string
  barcode: string
  is_active: boolean
  full_code: string
  full_path: string
  created_at: string
  updated_at: string
}

// ─── Products ────────────────────────────────────────────────────────────────

export interface MaterialCategory {
  id: string
  name: string
  description: string
  sort_order: number
  product_count: number
  default_markup_pct: string
  created_at: string
  updated_at: string
}

export interface ExtrusionType {
  id: string
  name: string
  category: 'frame' | 'rail' | 'blade' | 'track' | 'compensating' | 'rod' | 'hardware'
  category_display: string
  description: string
  weight_per_mm: string | null
  die_number: string
  standard_bar_mm: number
  kerf_mm: number
  is_active: boolean
  product_count: number
  created_at: string
  updated_at: string
}

export type UnitType = 'BAR' | 'KG' | 'EACH' | 'SET'

export interface Product {
  id: string
  name: string
  code: string
  category: string | null
  category_name: string | null
  extrusion: string | null
  extrusion_name: string | null
  style: string
  colour: string
  colour_code: string
  description: string
  unit_type: UnitType
  unit_type_display: string
  unit_cost: string | null
  selling_price: string | null
  markup_override: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

// ─── Inventory ───────────────────────────────────────────────────────────────

export interface StockItem {
  id: string
  company: string
  product: string
  product_code: string
  product_name: string
  extrusion_name: string | null
  barcode: string
  quantity: number
  length_mm: number | null
  state: string
  state_display: string
  bin_location: string | null
  bin_full_code: string | null
  requires_powdercoat: boolean
  powder_color: string
  unit_cost: string | null
  source_order: string
  is_active: boolean
  is_offcut: boolean
  created_at: string
  updated_at: string
}

export interface Offcut {
  id: string
  company: string
  product: string
  product_code: string
  extrusion_name: string | null
  length_mm: number
  quantity: number
  finish: 'mill' | 'powdercoated'
  finish_display: string
  powder_color: string
  bin_location: string | null
  bin_full_code: string | null
  is_reserved: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

// ─── Purchasing ──────────────────────────────────────────────────────────────

export interface Supplier {
  id: string
  name: string
  code: string
  email: string
  phone: string
  address: string
  lead_time_days: number
  payment_terms: string
  contact_name: string
  vat_number: string
  account_number: string
  account_name: string
  account_email: string
  registration_number: string
  bank_name: string
  bank_branch: string
  bank_code: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export type POPhase = 'requisition' | 'pending_approval' | 'approved' | 'ordered' | 'partial' | 'received' | 'cancelled'
export type POReason = 'stock_reorder' | 'job_request' | 'special_order' | 'blanket' | 'other'

export interface PurchaseOrder {
  id: string
  po_number: string
  division: string
  division_code: string
  supplier: string
  supplier_name: string
  phase: POPhase
  reason: POReason | null
  requires_quote: boolean
  job: string | null
  approved_by: string
  approved_at: string | null
  is_eft: boolean
  order_date: string
  expected_date: string | null
  notes: string
  lines: PurchaseOrderLine[]
  total_value: string
  created_at: string
  updated_at: string
}

export interface PurchaseOrderLine {
  id: string
  product: string
  product_code: string
  product_name: string
  description: string
  ordered_qty: number
  unit_price: string
  received_qty: number
  total: string
  is_complete: boolean
  job: string | null
  job_number: string | null
}

export interface PurchaseInvoice {
  id: string
  invoice_number: string
  supplier_inv_number: string
  po: string
  po_number: string
  grn: string
  grn_number: string
  supplier_name: string
  invoice_date: string
  due_date: string | null
  subtotal: string
  vat: string
  total: string
  status: 'draft' | 'posted' | 'discrepancy'
  notes: string
  price_variance_json: Record<string, { product: string; old_price: string; new_price: string; variance: string; variance_pct: string }>
  posted_by: string
  posted_at: string | null
  lines: PurchaseInvoiceLine[]
}

export interface PurchaseInvoiceLine {
  id: string
  po_line: string
  product_code: string
  product_name: string
  po_line_ordered: number
  invoiced_qty: number
  po_unit_price: string
  unit_price: string
  price_variance: string
  variance_pct: string
  line_total: string
  notes: string
}

// ─── Manufacturing ───────────────────────────────────────────────────────────

export type JobStatus = 'draft' | 'confirmed' | 'ready' | 'cutting' | 'completed' | 'cancelled'

export interface Job {
  id: string
  job_number: string
  division: string
  division_code: string
  description: string
  customer_name: string
  customer_ref: string
  status: JobStatus
  priority: number
  cut_design: string | null
  cut_design_id: string | null
  cut_design_status: string | null
  notes: string
  control_sheet_count: number
  control_sheets: ControlSheet[]
  created_at: string
  updated_at: string
}

export interface ControlSheetLine {
  id: string
  product: string
  product_code: string
  product_name: string
  length_mm: number | null
  quantity: number
  finish: string
  powder_color: string
  position: string
  notes: string
}

export interface ControlSheet {
  id: string
  job: string
  job_number: string
  job_status: string
  sheet_number: number
  name: string
  status: string
  is_final: boolean
  opening_type: string
  width_mm: number | null
  height_mm: number | null
  lock_type: string
  colour_name: string
  colour_code: string
  powder_coat: boolean
  mesh_type: string
  has_top_rail: boolean
  has_bottom_rail: boolean
  rail_width_mm: number
  hardware_notes: string
  signed_off_by: string
  signed_off_at: string | null
  lines: ControlSheetLine[]
  created_at: string
}

// ─── Powdercoat ───────────────────────────────────────────────────────────────

export interface PowdercoatJob {
  id: string
  job_reference: string
  supplier: string
  status: string
  colour: string
  sent_date: string
  due_date: string
  created_at: string
  updated_at: string
}

// ─── Sales ───────────────────────────────────────────────────────────────────

export interface Customer {
  id: string
  company: string
  name: string
  code: string
  email: string
  phone: string
  address: string
  is_active: boolean
  created_at: string
  updated_at: string
}