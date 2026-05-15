import { api } from './index'
import type {
  Division,
  MaterialCategory,
  ExtrusionType,
  Product,
  Supplier,
  StockItem,
  Offcut,
  PurchaseOrder,
  PurchaseInvoice,
  PurchasePriceHistory,
  Job,
  ControlSheet,
  ControlSheetLine,
} from '../types'

// ─── Core ───────────────────────────────────────────────────────────────────

export const divisions = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Division>>('/core/divisions/', { params }),
}

// ─── Products ───────────────────────────────────────────────────────────────

export const materialCategories = {
  list: () =>
    api.get<PaginatedResponse<MaterialCategory>>('/products/categories/'),
  get: (id: string) =>
    api.get<MaterialCategory>(`/products/categories/${id}/`),
  create: (data: Partial<MaterialCategory>) =>
    api.post<MaterialCategory>('/products/categories/', data),
  patch: (id: string, data: Partial<MaterialCategory>) =>
    api.patch<MaterialCategory>(`/products/categories/${id}/`, data),
}

export const extrusionTypes = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<ExtrusionType>>('/products/extrusion-types/', { params }),
  get: (id: string) =>
    api.get<ExtrusionType>(`/products/extrusion-types/${id}/`),
  create: (data: Partial<ExtrusionType>) =>
    api.post<ExtrusionType>('/products/extrusion-types/', data),
  patch: (id: string, data: Partial<ExtrusionType>) =>
    api.patch<ExtrusionType>(`/products/extrusion-types/${id}/`, data),
}

export const products = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Product>>('/products/products/', { params }),
  get: (id: string) =>
    api.get<Product>(`/products/products/${id}/`),
  create: (data: Partial<Product>) =>
    api.post<Product>('/products/products/', data),
  update: (id: string, data: Partial<Product>) =>
    api.put<Product>(`/products/products/${id}/`, data),
  patch: (id: string, data: Partial<Product>) =>
    api.patch<Product>(`/products/products/${id}/`, data),
}

// ─── Purchasing ──────────────────────────────────────────────────────────────

export const suppliers = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Supplier>>('/purchasing/suppliers/', { params }),
  get: (id: string) =>
    api.get<Supplier>(`/purchasing/suppliers/${id}/`),
  create: (data: Partial<Supplier>) =>
    api.post<Supplier>('/purchasing/suppliers/', data),
  update: (id: string, data: Partial<Supplier>) =>
    api.put<Supplier>(`/purchasing/suppliers/${id}/`, data),
  patch: (id: string, data: Partial<Supplier>) =>
    api.patch<Supplier>(`/purchasing/suppliers/${id}/`, data),
}

export const purchaseOrders = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<PurchaseOrder>>('/purchasing/purchase-orders/', { params }),
  get: (id: string) =>
    api.get<PurchaseOrder>(`/purchasing/purchase-orders/${id}/`),
  create: (data: Partial<PurchaseOrder>) =>
    api.post<PurchaseOrder>('/purchasing/purchase-orders/', data),
  patch: (id: string, data: Partial<PurchaseOrder>) =>
    api.patch<PurchaseOrder>(`/purchasing/purchase-orders/${id}/`, data),
  submitForApproval: (id: string) =>
    api.post<{ phase: string; po_number: string }>(`/purchasing/purchase-orders/${id}/submit_for_approval/`),
  approve: (id: string, data: { approved_by: string; is_eft: boolean }) =>
    api.post<PurchaseOrder>(`/purchasing/purchase-orders/${id}/approve/`, data),
  send: (id: string) =>
    api.post<PurchaseOrder>(`/purchasing/purchase-orders/${id}/send/`),
  receive: (id: string, data: { lines: Record<string, number>; notes?: string }) =>
    api.post<{ grn: string; phase: string; grn_id: string }>(`/purchasing/purchase-orders/${id}/receive/`, data),
  cancel: (id: string) =>
    api.post<{ phase: string }>(`/purchasing/purchase-orders/${id}/cancel/`),
}

export const invoices = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<PurchaseInvoice>>('/purchasing/invoices/', { params }),
  get: (id: string) =>
    api.get<PurchaseInvoice>(`/purchasing/invoices/${id}/`),
  create: (data: Partial<PurchaseInvoice>) =>
    api.post<PurchaseInvoice>('/purchasing/invoices/', data),
  post: (id: string, data: { lines: Array<{ po_line: string; invoiced_qty: number; unit_price: string }>; posted_by: string }) =>
    api.post<{ status: string; subtotal: string; vat: string; total: string; price_variances: Record<string, unknown> }>(
      `/purchasing/invoices/${id}/post/`, data),
}

export const priceHistory = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<PurchasePriceHistory>>('/purchasing/price-history/', { params }),
}

// ─── Inventory ───────────────────────────────────────────────────────────────

export const stockItems = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<StockItem>>('/inventory/stock-items/', { params }),
  get: (id: string) =>
    api.get<StockItem>(`/inventory/stock-items/${id}/`),
  create: (data: Partial<StockItem>) =>
    api.post<StockItem>('/inventory/stock-items/', data),
  patch: (id: string, data: Partial<StockItem>) =>
    api.patch<StockItem>(`/inventory/stock-items/${id}/`, data),
}

export const offcuts = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Offcut>>('/inventory/offcuts/', { params }),
  get: (id: string) =>
    api.get<Offcut>(`/inventory/offcuts/${id}/`),
  create: (data: Partial<Offcut>) =>
    api.post<Offcut>('/inventory/offcuts/', data),
  patch: (id: string, data: Partial<Offcut>) =>
    api.patch<Offcut>(`/inventory/offcuts/${id}/`, data),
}

// ─── Manufacturing ──────────────────────────────────────────────────────────

export const jobs = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Job>>('/manufacturing/jobs/', { params }),
  get: (id: string) =>
    api.get<Job>(`/manufacturing/jobs/${id}/`),
  create: (data: Partial<Job>) =>
    api.post<Job>('/manufacturing/jobs/', data),
  patch: (id: string, data: Partial<Job>) =>
    api.patch<Job>(`/manufacturing/jobs/${id}/`, data),
  delete: (id: string) =>
    api.delete(`/manufacturing/jobs/${id}/`),
  generateRequirements: (id: string) =>
    api.post<{ requirements_created: number }>(`/manufacturing/jobs/${id}/generate_requirements/`, { division_id: '' }),
  runOptimizer: (id: string) =>
    api.post<{ status: string }>(`/manufacturing/jobs/${id}/run_optimizer/`),
  markComplete: (id: string) =>
    api.post<Job>(`/manufacturing/jobs/${id}/mark_complete/`),
  addControlSheet: (id: string, data: Record<string, unknown>) =>
    api.post<ControlSheet>(`/manufacturing/jobs/${id}/add_control_sheet/`, data),
}

export const controlSheets = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<ControlSheet>>('/manufacturing/control-sheets/', { params }),
  get: (id: string) =>
    api.get<ControlSheet>(`/manufacturing/control-sheets/${id}/`),
  create: (data: Partial<ControlSheet>) =>
    api.post<ControlSheet>('/manufacturing/control-sheets/', data),
  patch: (id: string, data: Partial<ControlSheet>) =>
    api.patch<ControlSheet>(`/manufacturing/control-sheets/${id}/`, data),
  delete: (id: string) =>
    api.delete(`/manufacturing/control-sheets/${id}/`),
  finalize: (id: string) =>
    api.post<ControlSheet>(`/manufacturing/control-sheets/${id}/finalize/`),
}

// ─── Generic paginated response ─────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

// ─── Factory / Cutting Queue ─────────────────────────────────────────────

export const factory = {
  queue: (params?: Record<string, string>) =>
    api.get<any[]>('/manufacturing/factory/', { params }),
  job: (id: string) =>
    api.get<any>(`/manufacturing/factory/${id}/`),
  reorder: (job_ids: string[]) =>
    api.post('/manufacturing/factory/reorder/', { job_ids }),
  flipBar: (jobId: string, barId: string) =>
    api.post(`/manufacturing/factory/${jobId}/flip_bar/${barId}/`),
  markCut: (jobId: string, cutId: string) =>
    api.post(`/manufacturing/factory/${jobId}/mark_cut/${cutId}/`),
  resetBar: (jobId: string, barId: string) =>
    api.post(`/manufacturing/factory/${jobId}/reset_bar/${barId}/`),
}