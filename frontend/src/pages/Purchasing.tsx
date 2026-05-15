import { useState } from 'react'
import {
  Table, Input, Select, Button, Space, Tag, Modal, Form, Switch, message,
  Drawer, Divider, Row, Col, InputNumber, Alert, Tabs, Card, Upload, Badge, Steps,
} from 'antd'
import {
  PlusOutlined, EditOutlined, ReloadOutlined, SearchOutlined,
  DeleteOutlined, CheckCircleOutlined, FileTextOutlined, UploadOutlined,
  SendOutlined, CloseCircleOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { suppliers as suppliersApi, purchaseOrders, divisions, invoices, priceHistory, products as productsApi } from '../api'
import type { Supplier, PurchaseOrder, PurchaseOrderLine, Division, Product, PurchaseInvoice } from '../types'
import type { UploadFile } from 'antd/es/upload/interface'

const PHASE_OPTIONS = [
  { value: 'requisition',      label: 'Requisition' },
  { value: 'pending_approval',  label: 'Awaiting Approval' },
  { value: 'approved',         label: 'Approved' },
  { value: 'ordered',          label: 'Sent to Supplier' },
  { value: 'partial',          label: 'Partially Received' },
  { value: 'received',         label: 'Received' },
  { value: 'cancelled',        label: 'Cancelled' },
]

const PHASE_COLORS: Record<string, string> = {
  requisition:      'default',
  pending_approval: 'warning',
  approved:         'processing',
  ordered:          'blue',
  partial:          'orange',
  received:         'green',
  cancelled:        'red',
}

const REASON_OPTIONS = [
  { value: 'stock_reorder', label: 'Stock Reorder (Min Reached)' },
  { value: 'job_request',   label: 'Job Request (Manufacturing)' },
  { value: 'special_order', label: 'Special Order' },
  { value: 'blanket',       label: 'Blanket / Planned Order' },
  { value: 'other',         label: 'Other' },
]

const LEAD_TIME_OPTIONS = [
  { value: 3,  label: '3 days' },
  { value: 7,  label: '1 week' },
  { value: 14, label: '2 weeks' },
  { value: 21, label: '3 weeks' },
  { value: 28, label: '4 weeks' },
  { value: 42, label: '6 weeks' },
]

// ─── Helpers ─────────────────────────────────────────────────────────────────
const SUPPLIER_TABS_KEY = 'suppliers'
const PO_TABS_KEY = 'orders'

const phaseLabel = (phase: string) =>
  PHASE_OPTIONS.find(p => p.value === phase)?.label ?? phase

const phaseColor = (phase: string) =>
  PHASE_COLORS[phase] ?? 'default'

export default function Purchasing() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [activeTab, setActiveTab] = useState<string>(PO_TABS_KEY)

  // ── Filters ─────────────────────────────────────────────────────────────────
  const [supplierSearch, setSupplierSearch] = useState('')
  const [supplierActive, setSupplierActive] = useState<boolean | null>(null)
  const [poSearch, setPoSearch] = useState('')
  const [poPhase, setPoPhase] = useState<string | null>(null)

  // ── Supplier drawer ───────────────────────────────────────────────────────
  const [supplierDrawerOpen, setSupplierDrawerOpen] = useState(false)
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null)
  const [supplierForm] = Form.useForm()

  // ── PO modal ─────────────────────────────────────────────────────────────
  const [poModalOpen, setPoModalOpen] = useState(false)
  const [editingPO, setEditingPO] = useState<PurchaseOrder | null>(null)
  const [poForm] = Form.useForm()
  const [lineItems, setLineItems] = useState<any[]>([{ product: undefined, description: '', ordered_qty: 1, unit_price: 0 }])

  // ── View PO modal ─────────────────────────────────────────────────────────
  const [viewPO, setViewPO] = useState<PurchaseOrder | null>(null)

  // ── Approve modal ─────────────────────────────────────────────────────────
  const [approveModalOpen, setApproveModalOpen] = useState(false)
  const [approvePO, setApprovePO] = useState<PurchaseOrder | null>(null)
  const [approveForm] = Form.useForm()

  // ── Invoice entry modal ───────────────────────────────────────────────────
  const [invoiceModalOpen, setInvoiceModalOpen] = useState(false)
  const [invoicePO, setInvoicePO] = useState<PurchaseOrder | null>(null)
  const [invoiceForm] = Form.useForm()
  const [invoiceLines, setInvoiceLines] = useState<any[]>([])

  // ── Data ─────────────────────────────────────────────────────────────────
  const { data: divisionsData } = useQuery({
    queryKey: ['divisions'],
    queryFn: () => divisions.list(),
    select: (res) => res.data,
  })

  const { data: suppliersData, isLoading: suppliersLoading, refetch: refetchSuppliers } = useQuery({
    queryKey: ['suppliers', supplierSearch, supplierActive],
    queryFn: () => suppliersApi.list({
      search: supplierSearch || undefined,
      is_active: supplierActive !== null ? String(supplierActive) : undefined,
    }),
    select: (res) => res.data,
  })

  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.list(),
    select: (res) => res.data,
  })

  const { data: poData, isLoading: poLoading, refetch: refetchPOs } = useQuery({
    queryKey: ['purchase-orders', poSearch, poPhase],
    queryFn: () => purchaseOrders.list({
      search: poSearch || undefined,
      phase: poPhase || undefined,
    }),
    select: (res) => res.data,
  })

  // ── Mutations ────────────────────────────────────────────────────────────

  const saveSupplierMutation = useMutation({
    mutationFn: (values: any) =>
      editingSupplier
        ? suppliersApi.patch(editingSupplier.id, values)
        : suppliersApi.create(values),
    onSuccess: () => {
      messageApi.success(editingSupplier ? 'Supplier updated' : 'Supplier created')
      setSupplierDrawerOpen(false)
      supplierForm.resetFields()
      qc.invalidateQueries({ queryKey: ['suppliers'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Save failed')
    },
  })

  const savePOMutation = useMutation({
    mutationFn: (values: any) => {
      const payload = { ...values }
      if (editingPO) {
        return purchaseOrders.patch(editingPO.id, payload)
      }
      return purchaseOrders.create(payload)
    },
    onSuccess: () => {
      messageApi.success(editingPO ? 'PO updated' : 'PO created')
      setPoModalOpen(false)
      poForm.resetFields()
      setLineItems([{ product: undefined, description: '', ordered_qty: 1, unit_price: 0 }])
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? JSON.stringify(err?.response?.data) ?? 'Save failed')
    },
  })

  const submitForApprovalMutation = useMutation({
    mutationFn: (id: string) => purchaseOrders.submitForApproval(id),
    onSuccess: (res) => {
      messageApi.success(`PO ${res.po_number} submitted for approval`)
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Submit failed')
    },
  })

  const approvePOMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      purchaseOrders.approve(id, data),
    onSuccess: () => {
      messageApi.success('PO approved')
      setApproveModalOpen(false)
      approveForm.resetFields()
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Approval failed')
    },
  })

  const sendPOMutation = useMutation({
    mutationFn: (id: string) => purchaseOrders.send(id),
    onSuccess: () => {
      messageApi.success('PO sent to supplier')
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Send failed')
    },
  })

  const cancelPOMutation = useMutation({
    mutationFn: (id: string) => purchaseOrders.cancel(id),
    onSuccess: () => {
      messageApi.success('PO cancelled')
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Cancel failed')
    },
  })

  const receivePOMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      purchaseOrders.receive(id, data),
    onSuccess: (res: any) => {
      messageApi.success(`Goods received — GRN ${res.grn} created`)
      setViewPO(null)
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Receive failed')
    },
  })

  const postInvoiceMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) =>
      invoices.post(id, data),
    onSuccess: (res: any) => {
      const variances = res.price_variances
      if (Object.keys(variances).length > 0) {
        const lines = Object.entries(variances)
          .map(([code, v]: [string, any]) => `${code}: ${v.old_price} → ${v.new_price} (${v.variance_pct})`)
          .join('\n')
        Modal.success({
          title: 'Invoice Posted — Price Changes Detected',
          content: (
            <div>
              <p>Selling prices have been updated automatically:</p>
              <pre style={{ fontSize: 12, background: '#f5f5f5', padding: 8 }}>{lines}</pre>
            </div>
          ),
        })
      } else {
        messageApi.success('Invoice posted — no price changes detected')
      }
      setInvoiceModalOpen(false)
      invoiceForm.resetFields()
      qc.invalidateQueries({ queryKey: ['purchase-orders'] })
      qc.invalidateQueries({ queryKey: ['products'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Post failed')
    },
  })

  // ── Supplier table columns ────────────────────────────────────────────────
  const supplierColumns = [
    { title: 'Name',       dataIndex: 'name',          key: 'name' },
    { title: 'Code',       dataIndex: 'code',          key: 'code', width: 80 },
    { title: 'Email',      dataIndex: 'email',         key: 'email', ellipsis: true },
    { title: 'Phone',      dataIndex: 'phone',         key: 'phone', width: 130 },
    { title: 'Pay Terms',  dataIndex: 'payment_terms',  key: 'pay_terms', width: 110 },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'active',
      width: 80,
      render: (v: boolean) => v ? <Badge status="success" text="Yes" /> : <Badge status="default" text="No" />,
    },
    {
      title: '',
      key: 'actions',
      width: 80,
      render: (_: unknown, s: Supplier) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => openEditSupplier(s)} />
      ),
    },
  ]

  // ── PO table columns ──────────────────────────────────────────────────────
  const poColumns = [
    {
      title: 'PO Number',
      dataIndex: 'po_number',
      key: 'po_number',
      width: 140,
      render: (v: string, r: PurchaseOrder) => (
        <Button type="link" style={{ padding: 0, fontWeight: 600 }} onClick={() => setViewPO(r)}>
          {v}
        </Button>
      ),
    },
    {
      title: 'Phase',
      dataIndex: 'phase',
      key: 'phase',
      width: 160,
      render: (v: string) => (
        <Tag color={phaseColor(v)} style={{ fontSize: 12 }}>
          {phaseLabel(v)}
        </Tag>
      ),
    },
    { title: 'Supplier', dataIndex: 'supplier_name', key: 'supplier', ellipsis: true },
    { title: 'Div',     dataIndex: 'division_code', key: 'div',     width: 70 },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      width: 160,
      render: (v: string) => v ? REASON_OPTIONS.find(o => o.value === v)?.label : '—',
    },
    {
      title: 'EFT?',
      dataIndex: 'is_eft',
      key: 'eft',
      width: 60,
      render: (v: boolean) => v ? <Tag color="cyan">EFT</Tag> : null,
    },
    { title: 'Order Date', dataIndex: 'order_date', key: 'order_date', width: 110,
      render: (v: string) => new Date(v).toLocaleDateString() },
    { title: 'Expected',   dataIndex: 'expected_date', key: 'expected', width: 110,
      render: (v: string | null) => v ? new Date(v).toLocaleDateString() : '—' },
    {
      title: 'Total',
      dataIndex: 'total_value',
      key: 'total_value',
      width: 120,
      align: 'right' as const,
      render: (v: string) => v ? `R ${parseFloat(v).toFixed(2)}` : '—',
    },
    {
      title: 'Lines',
      dataIndex: 'line_count',
      key: 'line_count',
      width: 60,
      align: 'center' as const,
    },
    {
      title: '',
      key: 'actions',
      width: 120,
      render: (_: unknown, po: PurchaseOrder) => (
        <Space size={4}>
          <Button size="small" onClick={() => setViewPO(po)}>View</Button>
          {po.phase !== 'cancelled' && po.phase !== 'received' && (
            <Button icon={<EditOutlined />} size="small" onClick={() => openEditPO(po)} />
          )}
        </Space>
      ),
    },
  ]

  // ── Supplier handlers ────────────────────────────────────────────────────
  const openEditSupplier = (s: Supplier) => {
    setEditingSupplier(s)
    supplierForm.setFieldsValue({
      name: s.name, code: s.code, email: s.email,
      phone: s.phone, address: s.address,
      lead_time_days: s.lead_time_days,
      payment_terms: s.payment_terms,
      contact_name: s.contact_name,
      vat_number: s.vat_number,
      account_number: s.account_number,
      bank_name: s.bank_name,
      bank_branch: s.bank_branch,
      bank_code: s.bank_code,
      account_name: s.account_name,
      account_email: s.account_email,
      registration_number: s.registration_number,
      is_active: s.is_active,
    })
    setSupplierDrawerOpen(true)
  }

  const openNewSupplier = () => {
    setEditingSupplier(null)
    supplierForm.resetFields()
    setSupplierDrawerOpen(true)
  }

  // ── PO handlers ──────────────────────────────────────────────────────────
  const openEditPO = (po: PurchaseOrder) => {
    setEditingPO(po)
    poForm.setFieldsValue({
      division: po.division,
      supplier: po.supplier,
      phase: po.phase,
      reason: po.reason,
      requires_quote: po.requires_quote,
      order_date: po.order_date,
      expected_date: po.expected_date,
      notes: po.notes,
    })
    setLineItems(po.lines.map(l => ({
      product: l.product,
      description: l.description,
      ordered_qty: l.ordered_qty,
      unit_price: parseFloat(l.unit_price),
    })))
    setPoModalOpen(true)
  }

  const openNewPO = () => {
    setEditingPO(null)
    poForm.resetFields()
    setLineItems([{ product: undefined, description: '', ordered_qty: 1, unit_price: 0 }])
    setPoModalOpen(true)
  }

  const handlePOSubmit = (values: Record<string, unknown>) => {
    const validLines = lineItems.filter(l => l.product && l.ordered_qty > 0)
    if (validLines.length === 0) {
      messageApi.error('Add at least one line item')
      return
    }
    const payload = { ...values, lines: validLines }
    savePOMutation.mutate(payload)
  }

  // ── View PO handler ──────────────────────────────────────────────────────
  const handleViewPO = (po: PurchaseOrder) => {
    setViewPO(po)
  }

  // ── Approve handler ─────────────────────────────────────────────────────
  const openApproveModal = (po: PurchaseOrder) => {
    setApprovePO(po)
    approveForm.resetFields()
    setApproveModalOpen(true)
  }

  const handleApprove = (values: { approved_by: string; is_eft: boolean }) => {
    if (!approvePO) return
    approvePOMutation.mutate({ id: approvePO.id, data: values })
  }

  // ── Receive handler ───────────────────────────────────────────────────────
  const handleReceive = (po: PurchaseOrder) => {
    const linesMap: Record<string, number> = {}
    po.lines.forEach(l => {
      const remaining = parseFloat(String(l.ordered_qty)) - parseFloat(String(l.received_qty))
      if (remaining > 0) linesMap[l.id] = remaining
    })
    receivePOMutation.mutate({ id: po.id, data: { lines: linesMap } })
  }

  // ── Invoice entry handler ────────────────────────────────────────────────
  const openInvoiceModal = (po: PurchaseOrder) => {
    setInvoicePO(po)
    invoiceForm.resetFields()
    const lines = po.lines.map(l => ({
      po_line: l.id,
      product_code: l.product_code,
      product_name: l.product_name,
      ordered: l.ordered_qty,
      received: l.received_qty,
      invoiced_qty: parseFloat(String(l.ordered_qty)),
      po_unit_price: l.unit_price,
      unit_price: l.unit_price,
      variance: 0,
    }))
    setInvoiceLines(lines)
    setInvoiceModalOpen(true)
  }

  const handleInvoiceLineChange = (idx: number, field: string, value: any) => {
    const updated = [...invoiceLines]
    const line = updated[idx]
    if (field === 'invoiced_qty') line.invoiced_qty = value
    if (field === 'unit_price') line.unit_price = value
    const poPrice = parseFloat(line.po_unit_price)
    const invPrice = parseFloat(line.unit_price)
    line.variance = parseFloat((invPrice - poPrice).toFixed(4))
    setInvoiceLines(updated)
  }

  const handlePostInvoice = (values: { invoice_number: string; supplier_inv_number: string; invoice_date: string }) => {
    if (!invoicePO) return
    const lines = invoiceLines.map(l => ({
      po_line: l.po_line,
      invoiced_qty: l.invoiced_qty,
      unit_price: l.unit_price,
    }))
    postInvoiceMutation.mutate({
      id: invoicePO.id,
      data: { lines, posted_by: values.invoice_number },
    })
  }

  // ── Render helpers ───────────────────────────────────────────────────────
  const phaseSteps = (po: PurchaseOrder) => {
    const stepMap: Record<string, number> = {
      requisition: 0, pending_approval: 1, approved: 2,
      ordered: 3, partial: 4, received: 5,
    }
    return stepMap[po.phase] ?? 0
  }

  // ─── RETURN ─────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: 0 }}>
      {contextHolder}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: 0 }}>Purchasing</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() =>
            activeTab === SUPPLIER_TABS_KEY ? refetchSuppliers() : refetchPOs()
          }>Refresh</Button>
          {activeTab === SUPPLIER_TABS_KEY ? (
            <Button type="primary" icon={<PlusOutlined />} onClick={openNewSupplier}>Add Supplier</Button>
          ) : (
            <Button type="primary" icon={<PlusOutlined />} onClick={openNewPO}>New PO</Button>
          )}
        </Space>
      </div>

      {/* Tab buttons */}
      <div style={{ marginBottom: 16, borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          <Button
            type={activeTab === PO_TABS_KEY ? 'primary' : 'default'}
            onClick={() => setActiveTab(PO_TABS_KEY)}
          >
            Purchase Orders
          </Button>
          <Button
            type={activeTab === SUPPLIER_TABS_KEY ? 'primary' : 'default'}
            onClick={() => setActiveTab(SUPPLIER_TABS_KEY)}
          >
            Suppliers
          </Button>
        </Space>
      </div>

      {/* ── Purchase Orders ─────────────────────────────────────────────── */}
      {activeTab === PO_TABS_KEY && (
        <>
          <Space style={{ marginBottom: 12 }} wrap>
            <Input
              placeholder="Search PO number or supplier…"
              value={poSearch}
              onChange={(e) => setPoSearch(e.target.value)}
              style={{ width: 230 }}
              allowClear prefix={<SearchOutlined />}
            />
            <Select
              placeholder="All phases"
              value={poPhase}
              onChange={setPoPhase}
              style={{ width: 190 }}
              allowClear
              options={PHASE_OPTIONS}
            />
          </Space>

          <Table
            rowKey="id"
            loading={poLoading}
            dataSource={poData?.results ?? []}
            columns={poColumns}
            pagination={{ total: poData?.count ?? 0, showSizeChanger: true, showTotal: (t) => `${t} orders` }}
          />
        </>
      )}

      {/* ── Suppliers ────────────────────────────────────────────────────── */}
      {activeTab === SUPPLIER_TABS_KEY && (
        <>
          <Space style={{ marginBottom: 12 }} wrap>
            <Input
              placeholder="Search suppliers…"
              value={supplierSearch}
              onChange={(e) => setSupplierSearch(e.target.value)}
              style={{ width: 220 }}
              allowClear prefix={<SearchOutlined />}
            />
            <Select
              placeholder="Active / Inactive"
              value={supplierActive}
              onChange={setSupplierActive}
              style={{ width: 150 }}
              allowClear
              options={[
                { value: true,  label: 'Active only' },
                { value: false, label: 'Inactive only' },
              ]}
            />
          </Space>

          <Table
            rowKey="id"
            loading={suppliersLoading}
            dataSource={suppliersData?.results ?? []}
            columns={supplierColumns}
            pagination={{ total: suppliersData?.count ?? 0, showSizeChanger: true, showTotal: (t) => `${t} suppliers` }}
          />
        </>
      )}

      {/* ── Supplier Drawer ──────────────────────────────────────────────── */}
      <Drawer
        open={supplierDrawerOpen}
        title={editingSupplier ? 'Edit Supplier' : 'Add Supplier'}
        onClose={() => { setSupplierDrawerOpen(false); supplierForm.resetFields() }}
        width={480}
      >
        <Form
          form={supplierForm}
          layout="vertical"
          onFinish={(values) => saveSupplierMutation.mutate(values)}
          initialValues={{ is_active: true, lead_time_days: 7 }}
        >
          <Space style={{ width: '100%' }} direction="vertical" size={12}>
            <Row gutter={12}>
              <Col span={12}>
                <Form.Item label="Name" name="name" rules={[{ required: true }]}>
                  <Input placeholder="e.g. Aluminium Express" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Supplier Code" name="code">
                  <Input placeholder="Auto-generated from name" disabled />
                </Form.Item>
              </Col>
            </Row>

            <Row gutter={12}>
              <Col span={12}>
                <Form.Item label="Email" name="email">
                  <Input type="email" placeholder="orders@aluminium.co.za" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Phone" name="phone">
                  <Input placeholder="+27 11 000 0000" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="Address" name="address">
              <Input.TextArea rows={2} placeholder="Physical address…" />
            </Form.Item>

            <Divider style={{ margin: '4px 0 12px' }} orientation="left" plain>Contact Details</Divider>
            <Row gutter={12}>
              <Col span={12}>
                <Form.Item label="Contact Person" name="contact_name">
                  <Input placeholder="e.g. Johan Smith" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Payment Terms" name="payment_terms">
                  <Select
                    allowClear showSearch filterOption={(i, o) => (o?.label ?? '').toLowerCase().includes(i.toLowerCase())}
                    placeholder="e.g. 30 days"
                    options={[
                      { value: '30 days',   label: '30 days' },
                      { value: '60 days',   label: '60 days' },
                      { value: '90 days',   label: '90 days' },
                      { value: 'COD',       label: 'Cash on Delivery' },
                      { value: 'EFT',      label: 'EFT (Electronic Transfer)' },
                      { value: 'PIA',      label: 'Payment in Advance' },
                      { value: '2/10 N/30', label: '2/10 Net 30' },
                      { value: 'EOM',      label: 'End of Month' },
                    ]}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Divider style={{ margin: '4px 0 12px', textAlign: 'center' }} plain>Banking Details</Divider>
            <Form.Item label="Account Name" name="account_name">
              <Input placeholder="e.g. Aluminium Express CC" />
            </Form.Item>
            <Form.Item label="Account Email" name="account_email">
              <Input type="email" placeholder="e.g. accounts@aluminium.co.za" />
            </Form.Item>
            <Row gutter={12}>
              <Col span={12}>
                <Form.Item label="Bank Name" name="bank_name">
                  <Input placeholder="e.g. First National Bank" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item label="Account Number" name="account_number">
                  <Input placeholder="e.g. 1234567890" />
                </Form.Item>
              </Col>
            </Row>
            <Row gutter={12}>
              <Col span={8}>
                <Form.Item label="Branch" name="bank_branch">
                  <Input placeholder="e.g. Sandton" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="Branch Code" name="bank_code">
                  <Input placeholder="e.g. 250655" />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label="VAT Number" name="vat_number">
                  <Input placeholder="e.g. 4740123456" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item label="Registration Number" name="registration_number">
              <Input placeholder="e.g. 2021/123456/07" />
            </Form.Item>

            <Form.Item label="Active" name="is_active" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => setSupplierDrawerOpen(false)}>Cancel</Button>
                <Button
                  type="primary"
                  loading={saveSupplierMutation.isPending}
                  onClick={() => supplierForm.submit()}
                  style={{ minWidth: 80 }}
                >
                  {saveSupplierMutation.isPending ? 'Saving…' : (editingSupplier ? 'Update' : 'Create')}
                </Button>
              </Space>
            </Form.Item>
          </Space>
        </Form>
      </Drawer>

      {/* ── PO Create / Edit Modal ───────────────────────────────────────── */}
      <Modal
        open={poModalOpen}
        title={editingPO ? `Edit PO ${editingPO.po_number}` : 'New Purchase Order'}
        onCancel={() => { setPoModalOpen(false); poForm.resetFields(); setLineItems([{ product: undefined }]) }}
        footer={null}
        width={800}
      >
        <Form
          form={poForm}
          layout="vertical"
          onFinish={handlePOSubmit}
          initialValues={{
            phase: 'requisition',
            order_date: new Date().toISOString().slice(0, 10),
            requires_quote: false,
          }}
        >
          {/* Phase indicator */}
          {editingPO && (
            <Alert
              message={<span>Phase: <Tag color={phaseColor(editingPO.phase)} style={{ marginLeft: 4 }}>{phaseLabel(editingPO.phase)}</Tag></span>}
              type="info"
              showIcon
              style={{ marginBottom: 16 }}
            />
          )}

          {/* PO Header */}
          <Row gutter={12}>
            <Col span={10}>
              <Form.Item label="Division" name="division" rules={[{ required: true }]}>
                <Select
                  placeholder="Select division…"
                  showSearch filterOption={(i, o) => (o?.label ?? '').toLowerCase().includes(i.toLowerCase())}
                  options={divisionsData?.results
                    .filter((d: Division) => d.is_factory)
                    .map((d: Division) => ({ value: d.id, label: d.name }))}
                />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item label="Supplier" name="supplier" rules={[{ required: true }]}>
                <Select
                  placeholder="Select supplier…"
                  showSearch filterOption={(i, o) => (o?.label ?? '').toLowerCase().includes(i.toLowerCase())}
                  options={suppliersData?.results
                    .filter((s: Supplier) => s.is_active)
                    .map((s: Supplier) => ({ value: s.id, label: s.name }))}
                />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item label="EFT?" name="is_eft" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={8}>
              <Form.Item label="Reason" name="reason">
                <Select placeholder="Select reason…" options={REASON_OPTIONS} allowClear />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Order Date" name="order_date">
                <Input type="date" />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item label="Expected Date" name="expected_date">
                <Input type="date" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item label="Quote needed?" name="requires_quote" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          {/* Line items */}
          <Divider style={{ margin: '0 0 12px' }}>Line Items</Divider>

          {lineItems.map((line, idx) => (
            <div key={idx} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <Form.Item label="Product" style={{ flex: 2, minWidth: 180, marginBottom: 0 }}
                rules={[{ required: true, message: 'Required' }]}>
                <Select
                  placeholder="Product…"
                  showSearch filterOption={(i, o) => (o?.label ?? '').toLowerCase().includes(i.toLowerCase())}
                  value={line.product}
                  onChange={val => {
                    const updated = [...lineItems]
                    updated[idx].product = val
                    setLineItems(updated)
                  }}
                  options={productsData?.results.map((p: Product) => ({
                    value: p.id,
                    label: `${p.code} — ${p.name}`,
                  }))}
                />
              </Form.Item>

              <Form.Item label="Description" style={{ flex: 1, minWidth: 120, marginBottom: 0 }}>
                <Input
                  placeholder="Line note…"
                  value={line.description}
                  onChange={e => {
                    const updated = [...lineItems]
                    updated[idx].description = e.target.value
                    setLineItems(updated)
                  }}
                />
              </Form.Item>

              <Form.Item label="Qty" style={{ width: 80, marginBottom: 0 }}
                rules={[{ required: true, message: 'Required' }]}>
                <InputNumber
                  min={0}
                  value={line.ordered_qty}
                  onChange={val => {
                    const updated = [...lineItems]
                    updated[idx].ordered_qty = val ?? 0
                    setLineItems(updated)
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item label="Unit Price (R)" style={{ width: 110, marginBottom: 0 }}
                rules={[{ required: true, message: 'Required' }]}>
                <InputNumber
                  min={0} step={0.01}
                  value={line.unit_price}
                  onChange={val => {
                    const updated = [...lineItems]
                    updated[idx].unit_price = val ?? 0
                    setLineItems(updated)
                  }}
                  style={{ width: '100%' }}
                />
              </Form.Item>

              <Form.Item label="Total" style={{ width: 100, marginBottom: 0 }}>
                <div style={{ padding: '0 8px', fontWeight: 600, whiteSpace: 'nowrap' }}>
                  R {((line.ordered_qty || 0) * (line.unit_price || 0)).toFixed(2)}
                </div>
              </Form.Item>

              <Button
                icon={<DeleteOutlined />}
                danger
                onClick={() => setLineItems(lineItems.filter((_, i) => i !== idx))}
                disabled={lineItems.length === 1}
              />
            </div>
          ))}

          <Button
            size="small"
            icon={<PlusOutlined />}
            onClick={() => setLineItems([...lineItems, { product: undefined, description: '', ordered_qty: 1, unit_price: 0 }])}
            style={{ marginBottom: 16 }}
          >
            Add Line
          </Button>

          <Form.Item label="Notes" name="notes">
            <Input.TextArea rows={2} placeholder="Delivery instructions, special requirements…" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => { setPoModalOpen(false); poForm.resetFields() }}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={savePOMutation.isPending}>
                {editingPO ? 'Update PO' : 'Create PO'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ── View PO Detail Modal ───────────────────────────────────────────── */}
      <Modal
        open={!!viewPO}
        title={`PO ${viewPO?.po_number ?? ''}`}
        onCancel={() => setViewPO(null)}
        width={760}
        footer={
          viewPO ? (
            <Space wrap>
              {viewPO.phase === 'requisition' && (
                <Button
                  type="primary"
                  onClick={() => {
                    setViewPO(null)
                    openEditPO(viewPO)
                  }}
                >
                  Edit PO
                </Button>
              )}
              {viewPO.phase === 'requisition' && (
                <Button
                  type="primary"
                  onClick={() => submitForApprovalMutation.mutate(viewPO.id)}
                  loading={submitForApprovalMutation.isPending}
                >
                  Submit for Approval
                </Button>
              )}
              {viewPO.phase === 'pending_approval' && (
                <Button type="primary" onClick={() => { setViewPO(null); openApproveModal(viewPO) }}>
                  Approve PO
                </Button>
              )}
              {viewPO.phase === 'approved' && (
                <Button icon={<SendOutlined />} onClick={() => sendPOMutation.mutate(viewPO.id)} loading={sendPOMutation.isPending}>
                  Send to Supplier
                </Button>
              )}
              {(viewPO.phase === 'ordered' || viewPO.phase === 'partial') && (
                <Button onClick={() => handleReceive(viewPO)} loading={receivePOMutation.isPending}>
                  Mark Received
                </Button>
              )}
              {(viewPO.phase === 'ordered' || viewPO.phase === 'partial') && (
                <Button onClick={() => openInvoiceModal(viewPO)} icon={<FileTextOutlined />}>
                  Enter Invoice
                </Button>
              )}
              {viewPO.phase !== 'cancelled' && viewPO.phase !== 'received' && (
                <Button danger icon={<CloseCircleOutlined />} onClick={() => cancelPOMutation.mutate(viewPO.id)}
                  loading={cancelPOMutation.isPending}>
                  Cancel
                </Button>
              )}
            </Space>
          ) : null
        }
      >
        {viewPO && (
          <div>
            {/* Phase steps */}
            <Steps
              current={phaseSteps(viewPO)}
              size="small"
              style={{ marginBottom: 16 }}
              items={[
                { title: 'Requisition' },
                { title: 'Pending Approval' },
                { title: 'Approved' },
                { title: 'Sent' },
                { title: 'Partial' },
                { title: 'Received' },
              ]}
            />

            <Space style={{ marginBottom: 12 }} wrap>
              <Tag color={phaseColor(viewPO.phase)}>{phaseLabel(viewPO.phase)}</Tag>
              {viewPO.is_eft && <Tag color="cyan">EFT — POP Required</Tag>}
              <span style={{ color: '#666' }}>{viewPO.supplier_name}</span>
              <span style={{ color: '#999' }}>·</span>
              <span style={{ color: '#666' }}>{viewPO.division_code}</span>
              <span style={{ color: '#999' }}>·</span>
              <span style={{ color: '#666' }}>Order: {new Date(viewPO.order_date).toLocaleDateString()}</span>
              {viewPO.expected_date && <><span style={{ color: '#999' }}>·</span><span style={{ color: '#666' }}>Expected: {new Date(viewPO.expected_date).toLocaleDateString()}</span></>}
              {viewPO.approved_by && <><span style={{ color: '#999' }}>·</span><span style={{ color: '#666' }}>Approved: {viewPO.approved_by}</span></>}
            </Space>

            {viewPO.requires_quote && (
              <Alert message="Quote request — awaiting supplier pricing before ordering" type="warning" showIcon style={{ marginBottom: 12 }} />
            )}

            {viewPO.notes && (
              <Alert message={viewPO.notes} type="info" showIcon style={{ marginBottom: 12 }} />
            )}

            <Table
              rowKey="id"
              dataSource={viewPO.lines}
              columns={[
                { title: 'Product', dataIndex: 'product_name', key: 'product', width: 200, ellipsis: true },
                { title: 'Description', dataIndex: 'description', key: 'desc', width: 130, ellipsis: true },
                { title: 'Ordered', dataIndex: 'ordered_qty', key: 'ordered_qty', width: 80, align: 'right' as const },
                { title: 'Received', dataIndex: 'received_qty', key: 'received_qty', width: 90, align: 'right' as const },
                { title: 'Unit Price', dataIndex: 'unit_price', key: 'unit_price', width: 100, align: 'right' as const,
                  render: (v: string) => `R ${parseFloat(v).toFixed(2)}` },
                { title: 'Total', dataIndex: 'total', key: 'total', width: 110, align: 'right' as const,
                  render: (v: string) => <strong>R {parseFloat(v).toFixed(2)}</strong> },
                {
                  title: '', dataIndex: 'is_complete', key: 'done', width: 50,
                  render: (v: boolean) => v ? <CheckCircleOutlined style={{ color: '#52c41a' }} /> : null,
                },
              ]}
              pagination={false}
              size="small"
              summary={() => (
                <Table.Summary fixed>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={5} align="right"><strong>PO Total</strong></Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right">
                      <strong>R {parseFloat(viewPO.total_value || '0').toFixed(2)}</strong>
                    </Table.Summary.Cell>
                  </Table.Summary.Row>
                </Table.Summary>
              )}
            />
          </div>
        )}
      </Modal>

      {/* ── Approve PO Modal ────────────────────────────────────────────────── */}
      <Modal
        open={approveModalOpen}
        title={`Approve PO ${approvePO?.po_number ?? ''}`}
        onCancel={() => setApproveModalOpen(false)}
        footer={null}
        width={480}
      >
        <Form
          form={approveForm}
          layout="vertical"
          onFinish={handleApprove}
          initialValues={{ is_eft: false }}
        >
          <Alert
            message="Review the PO before approving. This moves it to Approved status, ready to send to the supplier."
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item label="Approved By (full name)" name="approved_by"
            rules={[{ required: true, message: 'Required — who is approving?' }]}>
            <Input placeholder="e.g. Sarah Nkosi" />
          </Form.Item>

          <Form.Item label="Payment Method" name="is_eft" valuePropName="checked">
            <Switch checkedChildren="EFT" unCheckedChildren="On Account" />
          </Form.Item>

          {approveForm.getFieldValue('is_eft') && (
            <Alert
              message="EFT selected — proof of payment (POP) must be uploaded before sending the PO."
              type="warning"
              showIcon
              style={{ marginBottom: 12 }}
            />
          )}

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setApproveModalOpen(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={approvePOMutation.isPending}>
                Approve PO
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ── Invoice Entry Modal ────────────────────────────────────────────── */}
      <Modal
        open={invoiceModalOpen}
        title={`Invoice Entry — ${invoicePO?.po_number ?? ''}`}
        onCancel={() => setInvoiceModalOpen(false)}
        footer={null}
        width={820}
      >
        <Form
          form={invoiceForm}
          layout="vertical"
          onFinish={handlePostInvoice}
        >
          <Row gutter={12} style={{ marginBottom: 16 }}>
            <Col span={8}>
              <Form.Item label="Invoice Number" name="invoice_number" rules={[{ required: true }]}>
                <Input placeholder="e.g. INV-2024-001" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Supplier Invoice #" name="supplier_inv_number">
                <Input placeholder="Supplier's ref" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Invoice Date" name="invoice_date" rules={[{ required: true }]}
                initialValue={new Date().toISOString().slice(0, 10)}>
                <Input type="date" />
              </Form.Item>
            </Col>
          </Row>

          <Divider style={{ margin: '0 0 12px' }}>Invoice Lines</Divider>

          <Table
            rowKey={(r: any) => r.po_line}
            dataSource={invoiceLines}
            columns={[
              { title: 'Product', dataIndex: 'product_name', key: 'product', width: 160, ellipsis: true },
              { title: 'Ordered', dataIndex: 'ordered', key: 'ordered', width: 70, align: 'right' as const },
              { title: 'Received', dataIndex: 'received', key: 'received', width: 80, align: 'right' as const },
              {
                title: 'Invoiced Qty',
                key: 'invoiced_qty',
                width: 110,
                render: (_: unknown, record: any, idx: number) => (
                  <InputNumber
                    min={0}
                    value={record.invoiced_qty}
                    onChange={v => handleInvoiceLineChange(idx, 'invoiced_qty', v)}
                    style={{ width: '100%' }}
                  />
                ),
              },
              {
                title: 'PO Unit Price',
                dataIndex: 'po_unit_price',
                key: 'po_price',
                width: 100,
                align: 'right' as const,
                render: (v: string) => `R ${parseFloat(v).toFixed(2)}`,
              },
              {
                title: 'Invoice Price',
                key: 'unit_price',
                width: 110,
                render: (_: unknown, record: any, idx: number) => (
                  <InputNumber
                    min={0} step={0.01}
                    value={record.unit_price}
                    onChange={v => handleInvoiceLineChange(idx, 'unit_price', v)}
                    style={{ width: '100%' }}
                  />
                ),
              },
              {
                title: 'Variance',
                dataIndex: 'variance',
                key: 'variance',
                width: 90,
                align: 'right' as const,
                render: (v: number) => {
                  if (v === 0) return <span style={{ color: '#52c41a' }}>—</span>
                  return <span style={{ color: v > 0 ? '#fa8c16' : '#ff4d4f', fontWeight: 600 }}>
                    {v > 0 ? '+' : ''}{v.toFixed(2)}
                  </span>
                },
              },
              {
                title: 'Line Total',
                key: 'line_total',
                width: 100,
                align: 'right' as const,
                render: (_: unknown, record: any) => {
                  const total = record.invoiced_qty * parseFloat(record.unit_price)
                  return <strong>R {total.toFixed(2)}</strong>
                },
              },
            ]}
            pagination={false}
            size="small"
            summary={(data: any[]) => {
              const subtotal = data.reduce((sum, l) => sum + l.invoiced_qty * parseFloat(l.unit_price), 0)
              const vat = subtotal * 0.15
              const total = subtotal + vat
              return (
                <Table.Summary fixed>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={7} align="right">Subtotal</Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right"><strong>R {subtotal.toFixed(2)}</strong></Table.Summary.Cell>
                  </Table.Summary.Row>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={7} align="right">VAT (15%)</Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right"><strong>R {vat.toFixed(2)}</strong></Table.Summary.Cell>
                  </Table.Summary.Row>
                  <Table.Summary.Row>
                    <Table.Summary.Cell index={0} colSpan={7} align="right">Total</Table.Summary.Cell>
                    <Table.Summary.Cell index={1} align="right">
                      <strong style={{ fontSize: 15 }}>R {total.toFixed(2)}</strong>
                    </Table.Summary.Cell>
                  </Table.Summary.Row>
                </Table.Summary>
              )
            }}
          />

          <Form.Item label="Notes" name="notes" style={{ marginTop: 12 }}>
            <Input.TextArea rows={2} placeholder="Any discrepancies or notes…" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setInvoiceModalOpen(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={postInvoiceMutation.isPending}>
                Post Invoice
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

    </div>
  )
}