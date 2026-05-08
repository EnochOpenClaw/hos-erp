import { Routes, Route, Navigate } from 'react-router-dom'
import { AppLayout } from './layouts/AppLayout'
import Products from './pages/Products'

const Dashboard     = () => <div style={{ padding: 24, fontSize: 18 }}>Dashboard — coming soon</div>
const Inventory     = () => <div style={{ padding: 24, fontSize: 18 }}>Inventory — coming soon</div>
const Manufacturing = () => <div style={{ padding: 24, fontSize: 18 }}>Manufacturing — coming soon</div>
const Sales         = () => <div style={{ padding: 24, fontSize: 18 }}>Sales — coming soon</div>

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="products" element={<Products />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="manufacturing" element={<Manufacturing />} />
        <Route path="sales" element={<Sales />} />
      </Route>
    </Routes>
  )
}