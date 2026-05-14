import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import Products from './pages/Products'
import MaterialCategories from './pages/MaterialCategories'
import ExtrusionTypes from './pages/ExtrusionTypes'
import Inventory from './pages/Inventory'
import Purchasing from './pages/Purchasing'
import Manufacturing from './pages/Manufacturing'

const Dashboard = () => <div style={{ padding: 24, fontSize: 18 }}>Dashboard — coming soon</div>
const Sales = () => <div style={{ padding: 24, fontSize: 18 }}>Sales — coming soon</div>

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="products/categories" element={<MaterialCategories />} />
        <Route path="products/extrusions" element={<ExtrusionTypes />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="purchasing" element={<Purchasing />} />
        <Route path="manufacturing" element={<Manufacturing />} />
        <Route path="sales" element={<Sales />} />
      </Route>
    </Routes>
  )
}