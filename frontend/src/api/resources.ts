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
}

export const extrusionTypes = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<ExtrusionType>>('/products/extrusion-types/', { params }),
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
}

// ─── Inventory ───────────────────────────────────────────────────────────────

export const stockItems = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<StockItem>>('/inventory/stock-items/', { params }),
}

export const offcuts = {
  list: (params?: Record<string, string>) =>
    api.get<PaginatedResponse<Offcut>>('/inventory/offcuts/', { params }),
}

// ─── Generic paginated response ─────────────────────────────────────────────

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}