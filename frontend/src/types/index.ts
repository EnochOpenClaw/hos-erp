export interface Company {
  id: string
  name: string
  code: string
  tax_id: string
  email: string
  phone: string
  is_active: boolean
}

export interface Warehouse {
  id: string
  company: string  // UUID
  name: string
  code: string
  address: string
  is_active: boolean
}

export interface Zone {
  id: string
  warehouse: string
  name: string
  code: string
  zone_type: string
  is_active: boolean
}

export interface BinLocation {
  id: string
  zone: string
  name: string
  barcode: string
  is_active: boolean
  full_code: string
}

export interface Product {
  id: string
  name: string
  code: string
  category: string | null
  extrusion: string | null
  unit_type: 'BAR' | 'KG' | 'EACH' | 'SET'
  is_active: boolean
}

export interface ExtrusionType {
  id: string
  name: string
  category: string
  description: string
  weight_per_mm: string | null
  standard_bar_mm: number
  kerf_mm: number
  is_active: boolean
}

export interface StockItem {
  id: string
  company: string
  product: string
  barcode: string
  quantity: number
  length_mm: number | null
  state: string
  bin_location: string | null
  requires_powdercoat: boolean
  powder_color: string
  unit_cost: string | null
  source_order: string
  is_active: boolean
}

export interface Offcut {
  id: string
  company: string
  product: string
  length_mm: number
  quantity: number
  finish: 'mill' | 'powdercoated'
  powder_color: string
  bin_location: string | null
  is_reserved: boolean
  is_active: boolean
}

export interface Job {
  id: string
  company: string
  job_number: string
  description: string
  status: 'pending' | 'cutting' | 'completed' | 'cancelled'
  source_order: string
}

export interface CutRequirement {
  id: string
  job: string
  product: string
  length_mm: number
  quantity: number
  finish: 'mill' | 'powdercoated'
  powder_color: string
  allow_offcut_match: boolean
}

export interface CutPlan {
  id: string
  job: string
  group_key: string
  bars_used: number
  waste_pct: number
  status: 'pending' | 'cut' | 'completed'
}
