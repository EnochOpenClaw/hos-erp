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
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PurchaseOrder {
  id: string
  po_number: string
  division: string
  division_code: string
  supplier: string
  supplier_name: string
  status: string
  order_date: string
  expected_date: string
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
}

// ─── Manufacturing ───────────────────────────────────────────────────────────

export interface Job {
  id: string
  job_number: string
  division: string
  status: string
  priority: number
  source_order: string
  created_at: string
  updated_at: string
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