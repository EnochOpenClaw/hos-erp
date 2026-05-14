import { useState, useEffect } from 'react'
import { Table, Input, Select, Button, Space, Tag, Modal, Form, Switch, message, Divider } from 'antd'
import { PlusOutlined, EditOutlined, ReloadOutlined, ExportOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { products, materialCategories, extrusionTypes } from '../api'
import type { Product, MaterialCategory, ExtrusionType } from '../types'

const UNIT_OPTIONS = [
  { value: 'BAR',  label: 'Bar (length)' },
  { value: 'KG',   label: 'Kilogram' },
  { value: 'EACH', label: 'Each' },
  { value: 'SET',  label: 'Set' },
]

const STYLE_EXAMPLES = [
  { value: 'standard',     label: 'Standard' },
  { value: 'heavy-duty',   label: 'Heavy Duty' },
  { value: 'reinforced',   label: 'Reinforced' },
  { value: 'snap-in',      label: 'Snap-In' },
  { value: 'clip-on',      label: 'Clip-On' },
  { value: 'mortise',      label: 'Mortise' },
  { value: 't-slot',       label: 'T-Slot' },
  { value: 'u-channel',    label: 'U-Channel' },
  { value: 'tubular',      label: 'Tubular' },
  { value: 'extruded',     label: 'Extruded' },
  { value: 'cast',         label: 'Cast' },
  { value: 'fabricated',   label: 'Fabricated' },
]

const COLOUR_EXAMPLES = [
  { value: 'mill finish',        label: 'Mill Finish (MF)' },
  { value: 'powder white',       label: 'Powder White (PW)' },
  { value: 'powder black',       label: 'Powder Black (PB)' },
  { value: 'anodised clear',     label: 'Anodised Clear (ANO)' },
  { value: 'anodised bronze',    label: 'Anodised Bronze (BRZ)' },
  { value: 'anodised black',     label: 'Anodised Black (BLK)' },
  { value: '.raw aluminium',     label: 'Raw Aluminium' },
  { value: 'galvanised',         label: 'Galvanised (GALV)' },
  { value: 'zintec',             label: 'Zintec (ZNC)' },
  { value: 'paint finish',       label: 'Paint Finish' },
]

const COLOUR_CODE_EXAMPLES = [
  { value: 'MF',   label: 'MF — Mill Finish' },
  { value: 'PW',   label: 'PW — Powder White' },
  { value: 'PB',   label: 'PB — Powder Black' },
  { value: 'ANO',  label: 'ANO — Anodised Clear' },
  { value: 'BRZ',  label: 'BRZ — Bronze' },
  { value: 'BLK',  label: 'BLK — Black' },
  { value: 'RAL',  label: 'RAL — RAL Colour' },
  { value: 'GALV', label: 'GALV — Galvanised' },
  { value: 'ZNC',  label: 'ZNC — Zintec' },
  { value: 'RAW',  label: 'RAW — Raw' },
]

export default function Products() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const [messageApi, contextHolder] = message.useMessage()

  // Filters
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<string | null>(null)
  const [extrusionId, setExtrusionId] = useState<string | null>(null)

  // Modal state
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [form] = Form.useForm()

  // Live category/extrusion refs for code generation
  const [selectedCategory, setSelectedCategory] = useState<MaterialCategory | null>(null)
  const [selectedExtrusion, setSelectedExtrusion] = useState<ExtrusionType | null>(null)

  // Data queries
  const { data: categoriesData } = useQuery({
    queryKey: ['material-categories'],
    queryFn: () => materialCategories.list(),
    select: (res) => res.data,
  })

  const { data: extrusionsData } = useQuery({
    queryKey: ['extrusion-types'],
    queryFn: () => extrusionTypes.list(),
    select: (res) => res.data,
  })

  const { data: productsData, isLoading, refetch } = useQuery({
    queryKey: ['products', search, categoryId, extrusionId],
    queryFn: () => products.list({
      search: search || undefined,
      category: categoryId || undefined,
      extrusion: extrusionId || undefined,
    }),
    select: (res) => res.data,
  })

  // Build auto-code preview whenever key fields change
  const [codePreview, setCodePreview] = useState('')
  useEffect(() => {
    if (!selectedCategory && !selectedExtrusion && !form.getFieldValue('colour_code') && !form.getFieldValue('style')) {
      setCodePreview('')
      return
    }
    const cat = selectedCategory ?? categoriesData?.results.find((c: MaterialCategory) => c.id === form.getFieldValue('category'))
    const ext = selectedExtrusion ?? extrusionsData?.results.find((e: ExtrusionType) => e.id === form.getFieldValue('extrusion'))
    const colour_code = form.getFieldValue('colour_code') ?? ''
    const style = form.getFieldValue('style') ?? ''

    const stripWords = ['type','profile','channel','track','stile','rail','louvre','slat','rod','bar']
    const catPart = cat ? cat.name.toUpperCase().slice(0, 3) : 'GEN'
    let extPart = 'UNK'
    if (ext) {
      const words = ext.name.toUpperCase().split()
      const meaningful = words.filter((w: string) => !stripWords.includes(w.toLowerCase()))
      extPart = (meaningful.length ? meaningful : words).map((w: string) => w.slice(0, 4)).join('').slice(0, 4)
    }
    const colPart = colour_code ? colour_code.toUpperCase().slice(0, 3) : (style ? style.toUpperCase().slice(0, 2) : 'NC')
    setCodePreview(`${catPart}-${extPart}-${colPart}`)
  }, [selectedCategory, selectedExtrusion, form.getFieldValue('colour_code'), form.getFieldValue('style')])

  // Create / update mutation
  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (editingProduct) {
        return products.patch(editingProduct.id, values)
      }
      return products.create(values)
    },
    onSuccess: () => {
      messageApi.success(editingProduct ? 'Product updated' : 'Product created')
      closeModal()
      qc.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => {
      messageApi.error('Failed to save product')
    },
  })

  const closeModal = () => {
    setModalOpen(false)
    form.resetFields()
    setEditingProduct(null)
    setSelectedCategory(null)
    setSelectedExtrusion(null)
    setCodePreview('')
  }

  const handleEdit = (product: Product) => {
    setEditingProduct(product)
    const cat = categoriesData?.results.find((c: MaterialCategory) => c.id === product.category)
    const ext = extrusionsData?.results.find((e: ExtrusionType) => e.id === product.extrusion)
    form.setFieldsValue({
      name: product.name,
      code: product.code,
      category: product.category,
      extrusion: product.extrusion,
      style: product.style,
      colour: product.colour,
      colour_code: product.colour_code,
      unit_type: product.unit_type,
      is_active: product.is_active,
    })
    setSelectedCategory(cat ?? null)
    setSelectedExtrusion(ext ?? null)
    setModalOpen(true)
  }

  const handleCreate = () => {
    setEditingProduct(null)
    form.resetFields()
    setSelectedCategory(null)
    setSelectedExtrusion(null)
    setCodePreview('')
    setModalOpen(true)
  }

  const handleFormSubmit = (values: Record<string, unknown>) => {
    if (!editingProduct && !values.code) {
      values.code = 'TMP-' + Date.now()
    }
    saveMutation.mutate(values)
  }

  const columns = [
    { title: 'Code',      dataIndex: 'code',            key: 'code',       width: 140 },
    { title: 'Name',      dataIndex: 'name',            key: 'name',       width: 280, ellipsis: true },
    { title: 'Category',  dataIndex: 'category_name',   key: 'category',   width: 160 },
    { title: 'Extrusion',dataIndex: 'extrusion_name',   key: 'extrusion',  width: 160 },
    { title: 'Unit',      dataIndex: 'unit_type_display', key: 'unit',     width: 110 },
    {
      title: 'Active',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 80,
      render: (val: boolean) => <Tag color={val ? 'green' : 'red'}>{val ? 'Yes' : 'No'}</Tag>,
    },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, record: Product) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
      ),
    },
  ]

  // Dropdown with add button helper
  const dropdownWithAdd = (
    menu: React.ReactNode,
    onAddClick: () => void
  ) => (
    <>
      {menu}
      <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
        <Button size="small" icon={<ExportOutlined />} onClick={onAddClick} style={{ width: '100%' }}>
          + Add new
        </Button>
      </div>
    </>
  )

  return (
    <div style={{ padding: 24 }}>
      {contextHolder}
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 16 }}>Products</h1>

      {/* Filters */}
      <Space style={{ marginBottom: 16 }} wrap>
        <Input
          placeholder="Search name or code..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: 220 }}
          allowClear
        />
        <Select
          placeholder="Category (all)"
          value={categoryId}
          onChange={(val) => { setCategoryId(val); setExtrusionId(null) }}
          style={{ width: 200 }}
          allowClear
          options={categoriesData?.results.map((c: MaterialCategory) => ({ value: c.id, label: c.name }))}
        />
        <Select
          placeholder="Extrusion Type (all)"
          value={extrusionId}
          onChange={setExtrusionId}
          style={{ width: 220 }}
          allowClear
          options={extrusionsData?.results.map((e: ExtrusionType) => ({ value: e.id, label: e.name }))}
        />
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
          Add Product
        </Button>
      </Space>

      {/* Table */}
      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={productsData?.results ?? []}
        columns={columns}
        pagination={{
          total: productsData?.count ?? 0,
          showSizeChanger: true,
          showTotal: (total) => `${total} products`,
        }}
      />

      {/* Create / Edit Modal */}
      <Modal
        open={modalOpen}
        title={editingProduct ? 'Edit Product' : 'Add Product'}
        onCancel={closeModal}
        footer={null}
        width={680}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFormSubmit}
          initialValues={{ is_active: true, unit_type: 'BAR' }}
        >
          <Space style={{ width: '100%' }} direction="vertical" size={12}>

            {/* Name — full width */}
            <Form.Item label="Name" name="name" rules={[{ required: true }]}>
              <Input placeholder="e.g. 40mm Aluminium End Stile" style={{ width: '100%' }} />
            </Form.Item>

            {/* Auto-code preview (new) | code field (edit only) */}
            <Space style={{ width: '100%' }} wrap>
              {!editingProduct && codePreview && (
                <div style={{ padding: '8px 12px', background: '#f0f5ff', borderRadius: 6, fontSize: 13, color: '#1677ff', fontFamily: 'monospace', alignSelf: 'flex-end', whiteSpace: 'nowrap' }}>
                  Will generate: {codePreview}
                </div>
              )}
              <Form.Item label="Product Code" name="code" style={{ flex: 1, marginBottom: 0 }}>
                <Input
                  placeholder={editingProduct ? 'e.g. SHU-ENDST-NC' : 'Auto-generated on save — leave blank'}
                  disabled={!editingProduct}
                />
              </Form.Item>
            </Space>

            {/* Category (left) | Extrusion Type (right) — two-column split */}
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <Form.Item label="Category" name="category" style={{ marginBottom: 8 }}>
                  <Select
                    placeholder="Select category"
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={categoriesData?.results.map((c: MaterialCategory) => ({ value: c.id, label: c.name }))}
                    onChange={(val) => {
                      const cat = categoriesData?.results.find((c: MaterialCategory) => c.id === val)
                      setSelectedCategory(cat ?? null)
                    }}
                    dropdownRender={(menu) => dropdownWithAdd(menu, () => { closeModal(); navigate('/products/categories') })}
                  />
                </Form.Item>
              </div>
              <div style={{ flex: 1 }}>
                <Form.Item label="Extrusion Type" name="extrusion" style={{ marginBottom: 8 }}>
                  <Select
                    placeholder="Select extrusion type"
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={extrusionsData?.results.map((e: ExtrusionType) => ({ value: e.id, label: e.name }))}
                    onChange={(val) => {
                      const ext = extrusionsData?.results.find((e: ExtrusionType) => e.id === val)
                      setSelectedExtrusion(ext ?? null)
                    }}
                    dropdownRender={(menu) => dropdownWithAdd(menu, () => { closeModal(); navigate('/products/extrusions') })}
                  />
                </Form.Item>
              </div>
            </div>

            {/* Style — with + Add button */}
            <div style={{ display: 'flex', gap: 16, alignItems: 'flex-end' }}>
              <Form.Item label="Style" name="style" style={{ flex: 1, marginBottom: 0 }}>
                <Select
                  placeholder="Select or type style"
                  options={STYLE_EXAMPLES}
                  allowClear
                  showSearch
                  filterOption={(input, option) =>
                    (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                  }
                  dropdownRender={(menu) => (
                    <>
                      {menu}
                      <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
                        <Button size="small" icon={<PlusOutlined />} onClick={() => messageApi.info('Add new style via Extrusion Types page')} style={{ width: '100%' }}>
                          + Add new Style
                        </Button>
                      </div>
                      <div style={{ padding: '4px 12px 8px', fontSize: 12, color: '#999' }}>
                        Tip: standard, heavy-duty, reinforced, snap-in, clip-on, mortise, t-slot
                      </div>
                    </>
                  )}
                />
              </Form.Item>
            </div>

            {/* Colour (left) | Colour Code (right) — editable with examples */}
            <div style={{ display: 'flex', gap: 16 }}>
              <div style={{ flex: 1 }}>
                <Form.Item label="Colour" name="colour">
                  <Select
                    placeholder="Select or type a colour — e.g. 'Signal Red RAL 3000'"
                    allowClear
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={COLOUR_EXAMPLES}
                    tokenSeparators={[',', ' ', ';']}
                    notFoundContent={null}
                    dropdownRender={(menu) => (
                      <>
                        {menu}
                        <div style={{ borderTop: '1px solid #f0f0f0', padding: '4px 12px 8px', fontSize: 12, color: '#999' }}>
                          Type a custom colour and press Enter, comma or space to add it
                        </div>
                      </>
                    )}
                  />
                </Form.Item>
              </div>
              <div style={{ flex: 1 }}>
                <Form.Item label="Colour Code" name="colour_code">
                  <Select
                    placeholder="Select or type a code — e.g. 'RAL3000'"
                    allowClear
                    showSearch
                    filterOption={(input, option) =>
                      (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                    }
                    options={COLOUR_CODE_EXAMPLES}
                    tokenSeparators={[',', ' ', ';']}
                    notFoundContent={null}
                    dropdownRender={(menu) => (
                      <>
                        {menu}
                        <div style={{ borderTop: '1px solid #f0f0f0', padding: '4px 12px 8px', fontSize: 12, color: '#999' }}>
                          Type a custom code and press Enter, comma or space to add it
                        </div>
                      </>
                    )}
                  />
                </Form.Item>
              </div>
            </div>

            {/* Unit Type — editable */}
            <Form.Item label="Unit Type" name="unit_type">
              <Select
                options={UNIT_OPTIONS}
                dropdownRender={(menu) => (
                  <>
                    {menu}
                    <div style={{ borderTop: '1px solid #f0f0f0', padding: '8px 12px' }}>
                      <Button size="small" icon={<PlusOutlined />} onClick={() => messageApi.info('Unit types managed via system settings')} style={{ width: '100%' }}>
                        + Add new Unit Type
                      </Button>
                    </div>
                  </>
                )}
              />
            </Form.Item>

            {/* Active toggle */}
            <Form.Item label="Active" name="is_active" valuePropName="checked" style={{ marginBottom: 0 }}>
              <Switch />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={closeModal}>Cancel</Button>
                <Button type="primary" htmlType="submit" loading={saveMutation.isPending}>
                  {editingProduct ? 'Update' : 'Create'}
                </Button>
              </Space>
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}