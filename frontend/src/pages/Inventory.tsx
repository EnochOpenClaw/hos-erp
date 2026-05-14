import { useState } from 'react'
import { Table, Input, Select, Button, Space, Tag, Modal, Form, Switch, message, Drawer, Divider, Tooltip } from 'antd'
import { PlusOutlined, EditOutlined, ReloadOutlined, SearchOutlined, InboxOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { stockItems, offcuts, products as productsApi, divisions } from '../api'
import type { StockItem, Offcut, Product, Division } from '../types'

const STATE_OPTIONS = [
  { value: 'ordered',         label: 'On Order' },
  { value: 'received',       label: 'Received' },
  { value: 'stored',         label: 'In Store' },
  { value: 'cut',            label: 'Cut' },
  { value: 'prepared',       label: 'Prepared for Assembly' },
  { value: 'sent_powder',    label: 'Sent to Powder Coating' },
  { value: 'returned_powder',label: 'Returned from Powder Coating' },
  { value: 'assembled',      label: 'Assembled' },
  { value: 'cleaned',        label: 'Cleaned' },
  { value: 'packed',         label: 'Packed' },
  { value: 'installed',      label: 'Installed' },
  { value: 'consumed',       label: 'Consumed' },
  { value: 'discarded',      label: 'Discarded' },
]

const STATE_COLORS: Record<string, string> = {
  ordered: 'blue',
  received: 'cyan',
  stored: 'green',
  cut: 'orange',
  prepared: 'gold',
  sent_powder: 'purple',
  returned_powder: 'magenta',
  assembled: 'lime',
  cleaned: 'lime',
  packed: 'geekblue',
  installed: 'green',
  consumed: 'default',
  discarded: 'red',
}

const FINISH_OPTIONS = [
  { value: 'mill',          label: 'Mill Finish' },
  { value: 'powdercoated',  label: 'Powdercoated' },
]

const OFFCUT_LIST_TAB_KEY = 'offcuts'

export default function Inventory() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()

  // ── Filters ──────────────────────────────────────────────────────────────
  const [search, setSearch] = useState('')
  const [stateFilter, setStateFilter] = useState<string | null>(null)
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null)
  const [divisionFilter, setDivisionFilter] = useState<string | null>(null)

  // ── Active tab: stock | offcuts ─────────────────────────────────────────
  const [activeTab, setActiveTab] = useState<string>('stock')

  // ── Offcut filters ──────────────────────────────────────────────────────
  const [offcutSearch, setOffcutSearch] = useState('')
  const [reservedFilter, setReservedFilter] = useState<boolean | null>(null)

  // ── Drawer ────────────────────────────────────────────────────────────────
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [editingItem, setEditingItem] = useState<StockItem | null>(null)
  const [form] = Form.useForm()

  // ── Offcut modal ──────────────────────────────────────────────────────────
  const [offcutModalOpen, setOffcutModalOpen] = useState(false)
  const [editingOffcut, setEditingOffcut] = useState<Offcut | null>(null)
  const [offcutForm] = Form.useForm()

  // ── Data ─────────────────────────────────────────────────────────────────
  const { data: divisionsData } = useQuery({
    queryKey: ['divisions'],
    queryFn: () => divisions.list(),
    select: (res) => res.data,
  })

  const { data: productsData } = useQuery({
    queryKey: ['products'],
    queryFn: () => productsApi.list(),
    select: (res) => res.data,
  })

  const { data: stockData, isLoading: stockLoading, refetch: refetchStock } = useQuery({
    queryKey: ['stock-items', search, stateFilter, activeFilter],
    queryFn: () => stockItems.list({
      search: search || undefined,
      state: stateFilter || undefined,
      is_active: activeFilter !== null ? String(activeFilter) : undefined,
    }),
    select: (res) => res.data,
  })

  const { data: offcutData, isLoading: offcutLoading, refetch: refetchOffcuts } = useQuery({
    queryKey: ['offcuts', offcutSearch, reservedFilter],
    queryFn: () => offcuts.list({
      search: offcutSearch || undefined,
      is_reserved: reservedFilter !== null ? String(reservedFilter) : undefined,
    }),
    select: (res) => res.data,
  })

  // ── Mutations ────────────────────────────────────────────────────────────
  const saveStockMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (editingItem) {
        return stockItems.patch(editingItem.id, values)
      }
      return stockItems.create(values)
    },
    onSuccess: () => {
      messageApi.success(editingItem ? 'Stock item updated' : 'Stock item added')
      setDrawerOpen(false)
      form.resetFields()
      setEditingItem(null)
      qc.invalidateQueries({ queryKey: ['stock-items'] })
    },
    onError: () => messageApi.error('Failed to save stock item'),
  })

  const saveOffcutMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (editingOffcut) {
        return offcuts.patch(editingOffcut.id, values)
      }
      return offcuts.create(values)
    },
    onSuccess: () => {
      messageApi.success(editingOffcut ? 'Offcut updated' : 'Offcut added')
      setOffcutModalOpen(false)
      offcutForm.resetFields()
      setEditingOffcut(null)
      qc.invalidateQueries({ queryKey: ['offcuts'] })
    },
    onError: () => messageApi.error('Failed to save offcut'),
  })

  // ── Stock table columns ───────────────────────────────────────────────────
  const stockColumns = [
    {
      title: 'Code',
      dataIndex: 'product_code',
      key: 'product_code',
      width: 130,
      ellipsis: true,
      render: (v: string) => <Tag style={{ fontFamily: 'monospace' }}>{v}</Tag>,
    },
    {
      title: 'Name',
      dataIndex: 'product_name',
      key: 'product_name',
      width: 260,
      ellipsis: true,
    },
    {
      title: 'State',
      dataIndex: 'state_display',
      key: 'state',
      width: 160,
      render: (text: string, record: StockItem) => (
        <Tag color={STATE_COLORS[record.state]}>{text}</Tag>
      ),
    },
    {
      title: 'Qty',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 80,
      align: 'right' as const,
    },
    {
      title: 'Length',
      dataIndex: 'length_mm',
      key: 'length_mm',
      width: 90,
      align: 'right' as const,
      render: (v: number | null) => v ? `${v} mm` : '—',
    },
    {
      title: 'Location',
      dataIndex: 'bin_full_code',
      key: 'bin_location',
      width: 110,
      ellipsis: true,
      render: (v: string | null) => v ?? '—',
    },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 70,
      render: (val: boolean) => <Tag color={val ? 'green' : 'red'}>{val ? 'Yes' : 'No'}</Tag>,
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, record: StockItem) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => openEditDrawer(record)} />
      ),
    },
  ]

  // ── Offcut table columns ──────────────────────────────────────────────────
  const offcutColumns = [
    {
      title: 'Code',
      dataIndex: 'product_code',
      key: 'product_code',
      width: 130,
      ellipsis: true,
      render: (v: string) => <Tag style={{ fontFamily: 'monospace' }}>{v}</Tag>,
    },
    {
      title: 'Extrusion',
      dataIndex: 'extrusion_name',
      key: 'extrusion',
      width: 150,
      ellipsis: true,
      render: (v: string | null) => v ?? '—',
    },
    {
      title: 'Length',
      dataIndex: 'length_mm',
      key: 'length_mm',
      width: 100,
      align: 'right' as const,
      render: (v: number) => <strong>{v} mm</strong>,
    },
    {
      title: 'Qty',
      dataIndex: 'quantity',
      key: 'quantity',
      width: 70,
      align: 'right' as const,
    },
    {
      title: 'Finish',
      dataIndex: 'finish_display',
      key: 'finish',
      width: 120,
      render: (v: string, record: Offcut) =>
        record.finish === 'powdercoated'
          ? <Tag color="purple">{v}</Tag>
          : <Tag>{v}</Tag>,
    },
    {
      title: 'Colour',
      dataIndex: 'powder_color',
      key: 'powder_color',
      width: 130,
      ellipsis: true,
      render: (v: string) => v || '—',
    },
    {
      title: 'Location',
      dataIndex: 'bin_full_code',
      key: 'bin_location',
      width: 110,
      ellipsis: true,
      render: (v: string | null) => v ?? '—',
    },
    {
      title: 'Reserved',
      dataIndex: 'is_reserved',
      key: 'is_reserved',
      width: 90,
      render: (val: boolean) => <Tag color={val ? 'orange' : 'default'}>{val ? 'Yes' : 'No'}</Tag>,
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, record: Offcut) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => openEditOffcut(record)} />
      ),
    },
  ]

  // ── Open edit drawer ──────────────────────────────────────────────────────
  const openEditDrawer = (item: StockItem) => {
    setEditingItem(item)
    form.setFieldsValue({
      product: item.product,
      barcode: item.barcode,
      quantity: item.quantity,
      length_mm: item.length_mm,
      state: item.state,
      bin_location: item.bin_location,
      requires_powdercoat: item.requires_powdercoat,
      powder_color: item.powder_color,
      unit_cost: item.unit_cost,
      source_order: item.source_order,
      is_active: item.is_active,
    })
    setDrawerOpen(true)
  }

  const openNewDrawer = () => {
    setEditingItem(null)
    form.resetFields()
    setDrawerOpen(true)
  }

  const openEditOffcut = (item: Offcut) => {
    setEditingOffcut(item)
    offcutForm.setFieldsValue({
      product: item.product,
      length_mm: item.length_mm,
      quantity: item.quantity,
      finish: item.finish,
      powder_color: item.powder_color,
      bin_location: item.bin_location,
      is_reserved: item.is_reserved,
      is_active: item.is_active,
    })
    setOffcutModalOpen(true)
  }

  const openNewOffcut = () => {
    setEditingOffcut(null)
    offcutForm.resetFields()
    setOffcutModalOpen(true)
  }

  // ── Tab change handler ────────────────────────────────────────────────────
  const handleTabChange = (key: string) => {
    setActiveTab(key)
    if (key === OFFCUT_LIST_TAB_KEY) {
      setActiveTab('offcuts')
    } else {
      setActiveTab('stock')
    }
  }

  return (
    <div style={{ padding: 0 }}>
      {contextHolder}

      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: 0 }}>Inventory</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={() => activeTab === 'stock' ? refetchStock() : refetchOffcuts()}>
            Refresh
          </Button>
          {activeTab === 'stock' ? (
            <Button type="primary" icon={<PlusOutlined />} onClick={openNewDrawer}>
              Add Stock Item
            </Button>
          ) : (
            <Button type="primary" icon={<PlusOutlined />} onClick={openNewOffcut}>
              Add Offcut
            </Button>
          )}
        </Space>
      </div>

      {/* Tab buttons */}
      <div style={{ marginBottom: 16, borderBottom: '1px solid #f0f0f0' }}>
        <Space>
          <Button
            type={activeTab === 'stock' ? 'primary' : 'default'}
            onClick={() => setActiveTab('stock')}
          >
            Stock Items
          </Button>
          <Button
            type={activeTab === 'offcuts' ? 'primary' : 'default'}
            onClick={() => setActiveTab('offcuts')}
          >
            Offcuts
          </Button>
        </Space>
      </div>

      {/* ── Stock Items Tab ──────────────────────────────────────────────── */}
      {activeTab === 'stock' && (
        <>
          {/* Stock Filters */}
          <Space style={{ marginBottom: 12 }} wrap>
            <Input
              placeholder="Search product name or code…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 220 }}
              allowClear
              prefix={<SearchOutlined />}
            />
            <Select
              placeholder="All states"
              value={stateFilter}
              onChange={setStateFilter}
              style={{ width: 200 }}
              allowClear
              options={STATE_OPTIONS}
            />
            <Select
              placeholder="Active / Inactive"
              value={activeFilter}
              onChange={setActiveFilter}
              style={{ width: 150 }}
              allowClear
              options={[
                { value: true, label: 'Active only' },
                { value: false, label: 'Inactive only' },
              ]}
            />
          </Space>

          {/* Stock Table */}
          <Table
            rowKey="id"
            loading={stockLoading}
            dataSource={stockData?.results ?? []}
            columns={stockColumns}
            pagination={{
              total: stockData?.count ?? 0,
              showSizeChanger: true,
              showTotal: (total) => `${total} items`,
            }}
          />
        </>
      )}

      {/* ── Offcuts Tab ──────────────────────────────────────────────────── */}
      {activeTab === 'offcuts' && (
        <>
          {/* Offcut Filters */}
          <Space style={{ marginBottom: 12 }} wrap>
            <Input
              placeholder="Search offcuts…"
              value={offcutSearch}
              onChange={(e) => setOffcutSearch(e.target.value)}
              style={{ width: 220 }}
              allowClear
              prefix={<SearchOutlined />}
            />
            <Select
              placeholder="All offcuts"
              value={reservedFilter}
              onChange={setReservedFilter}
              style={{ width: 150 }}
              allowClear
              options={[
                { value: false, label: 'Available' },
                { value: true,  label: 'Reserved' },
              ]}
            />
          </Space>

          {/* Offcut Table */}
          <Table
            rowKey="id"
            loading={offcutLoading}
            dataSource={offcutData?.results ?? []}
            columns={offcutColumns}
            pagination={{
              total: offcutData?.count ?? 0,
              showSizeChanger: true,
              showTotal: (total) => `${total} offcuts`,
            }}
          />
        </>
      )}

      {/* ── Stock Item Drawer ────────────────────────────────────────────── */}
      <Drawer
        open={drawerOpen}
        title={editingItem ? 'Edit Stock Item' : 'Add Stock Item'}
        onClose={() => { setDrawerOpen(false); form.resetFields(); setEditingItem(null) }}
        width={520}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={(values) => saveStockMutation.mutate(values)}
          initialValues={{ is_active: true, requires_powdercoat: false, quantity: 1 }}
        >
          <Space style={{ width: '100%' }} direction="vertical" size={12}>

            <Form.Item label="Product" name="product" rules={[{ required: true }]}>
              <Select
                placeholder="Search and select a product…"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={productsData?.results.map((p: Product) => ({
                  value: p.id,
                  label: `${p.code} — ${p.name}`,
                }))}
              />
            </Form.Item>

            <Form.Item label="Barcode" name="barcode">
              <Input placeholder="Optional barcode or tag number" />
            </Form.Item>

            <div style={{ display: 'flex', gap: 12 }}>
              <Form.Item label="Quantity" name="quantity" rules={[{ required: true }]} style={{ flex: 1 }}>
                <Input type="number" min={0} placeholder="1" />
              </Form.Item>
              <Form.Item label="Length (mm)" name="length_mm" style={{ flex: 1 }}>
                <Input type="number" min={0} placeholder="6300" />
              </Form.Item>
            </div>

            <Form.Item label="State" name="state">
              <Select options={STATE_OPTIONS} />
            </Form.Item>

            <Form.Item label="Bin Location" name="bin_location">
              <Select
                placeholder="Select location…"
                allowClear
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={[]}
                dropdownRender={(menu) => (
                  <>
                    {menu}
                    <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
                      <Button size="small" onClick={() => messageApi.info('Bin locations managed via the Divisions page')} style={{ width: '100%' }}>
                        + Add Bin Location
                      </Button>
                    </div>
                  </>
                )}
              />
            </Form.Item>

            <Divider style={{ margin: '8px 0' }} />

            <Form.Item label="Requires Powder Coating" name="requires_powdercoat" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>

            <Form.Item label="Powder Colour" name="powder_color" dependencies={['requires_powdercoat']}>
              <Input
                placeholder="e.g. Signal Red RAL 3000"
                disabled={!form.getFieldValue('requires_powdercoat')}
              />
            </Form.Item>

            <Divider style={{ margin: '8px 0' }} />

            <div style={{ display: 'flex', gap: 12 }}>
              <Form.Item label="Unit Cost (R)" name="unit_cost" style={{ flex: 1 }}>
                <Input type="number" min={0} step={0.01} placeholder="0.00" />
              </Form.Item>
              <Form.Item label="Source Order" name="source_order" style={{ flex: 1 }}>
                <Input placeholder="PO or MO reference" />
              </Form.Item>
            </div>

            <Form.Item label="Active" name="is_active" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => { setDrawerOpen(false); form.resetFields() }}>Cancel</Button>
                <Button type="primary" htmlType="submit" loading={saveStockMutation.isPending}>
                  {editingItem ? 'Update' : 'Create'}
                </Button>
              </Space>
            </Form.Item>

          </Space>
        </Form>
      </Drawer>

      {/* ── Offcut Modal ──────────────────────────────────────────────────── */}
      <Modal
        open={offcutModalOpen}
        title={editingOffcut ? 'Edit Offcut' : 'Add Offcut'}
        onCancel={() => { setOffcutModalOpen(false); offcutForm.resetFields() }}
        footer={null}
        width={520}
      >
        <Form
          form={offcutForm}
          layout="vertical"
          onFinish={(values) => saveOffcutMutation.mutate(values)}
          initialValues={{ is_active: true, is_reserved: false, quantity: 1, finish: 'mill' }}
        >
          <Space style={{ width: '100%' }} direction="vertical" size={12}>

            <Form.Item label="Product" name="product" rules={[{ required: true }]}>
              <Select
                placeholder="Search and select a product…"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={productsData?.results.map((p: Product) => ({
                  value: p.id,
                  label: `${p.code} — ${p.name}`,
                }))}
              />
            </Form.Item>

            <div style={{ display: 'flex', gap: 12 }}>
              <Form.Item label="Length (mm)" name="length_mm" rules={[{ required: true }]} style={{ flex: 1 }}>
                <Input type="number" min={0} placeholder="e.g. 1800" />
              </Form.Item>
              <Form.Item label="Quantity" name="quantity" rules={[{ required: true }]} style={{ flex: 1 }}>
                <Input type="number" min={0} placeholder="1" />
              </Form.Item>
            </div>

            <Form.Item label="Finish" name="finish">
              <Select options={FINISH_OPTIONS} />
            </Form.Item>

            <Form.Item label="Powder Colour" name="powder_color">
              <Input placeholder="e.g. Matt Black RAL 9005" />
            </Form.Item>

            <Form.Item label="Bin Location" name="bin_location">
              <Select
                placeholder="Select bin…"
                allowClear
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
                options={[]}
                dropdownRender={(menu) => (
                  <>
                    {menu}
                    <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
                      <Button size="small" onClick={() => messageApi.info('Bin locations managed via the Divisions page')} style={{ width: '100%' }}>
                        + Add Bin Location
                      </Button>
                    </div>
                  </>
                )}
              />
            </Form.Item>

            <Form.Item label="Reserved" name="is_reserved" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>

            <Form.Item label="Active" name="is_active" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => { setOffcutModalOpen(false); offcutForm.resetFields() }}>Cancel</Button>
                <Button type="primary" htmlType="submit" loading={saveOffcutMutation.isPending}>
                  {editingOffcut ? 'Update' : 'Create'}
                </Button>
              </Space>
            </Form.Item>

          </Space>
        </Form>
      </Modal>
    </div>
  )
}
