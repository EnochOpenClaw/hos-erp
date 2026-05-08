import { useState } from 'react'
import { Table, Input, Select, Button, Space, Tag, Modal, Form, InputNumber, Switch, message } from 'antd'
import { PlusOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { products, materialCategories, extrusionTypes } from '../api'
import type { Product, MaterialCategory, ExtrusionType } from '../types'

const UNIT_OPTIONS = [
  { value: 'BAR',  label: 'Bar (length)' },
  { value: 'KG',   label: 'Kilogram' },
  { value: 'EACH', label: 'Each' },
  { value: 'SET',  label: 'Set' },
]

const CATEGORY_OPTIONS_MAP: Record<string, { value: string; label: string }[]> = {
  frame:          [{ value: 'Stile', label: 'Stile' }, { value: 'Side Channel', label: 'Side Channel' }, { value: 'Hood Channel', label: 'Hood Channel' }],
  rail:           [{ value: 'Rail', label: 'Rail' }, { value: 'Battens', label: 'Battens' }],
  blade:          [{ value: 'Louvre', label: 'Louvre' }, { value: 'Slat', label: 'Slat' }],
  track:          [{ value: 'Bottom Track', label: 'Bottom Track' }, { value: 'Top Track', label: 'Top Track' }],
  compensating:   [{ value: 'Compensating', label: 'Compensating' }],
  rod:            [{ value: 'Rod', label: 'Rod' }, { value: 'Tie Bar', label: 'Tie Bar' }, { value: 'Flyscreen Brush', label: 'Flyscreen Brush' }, { value: 'Weather Seal', label: 'Weather Seal' }],
  hardware:       [{ value: 'Flyscreen Clip', label: 'Flyscreen Clip' }, { value: 'Clip Profile', label: 'Clip Profile' }],
}

export default function Products() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()

  // Filters
  const [search, setSearch] = useState('')
  const [categoryId, setCategoryId] = useState<string | null>(null)
  const [extrusionId, setExtrusionId] = useState<string | null>(null)

  // Modal state
  const [modalOpen, setModalOpen] = useState(false)
  const [editingProduct, setEditingProduct] = useState<Product | null>(null)
  const [form] = Form.useForm()

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

  // Create / update mutation
  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (editingProduct) {
        return products.patch(editingProduct.id, values)
      }
      return products.create(values as Partial<Product>)
    },
    onSuccess: () => {
      messageApi.success(editingProduct ? 'Product updated' : 'Product created')
      setModalOpen(false)
      form.resetFields()
      setEditingProduct(null)
      qc.invalidateQueries({ queryKey: ['products'] })
    },
    onError: () => {
      messageApi.error('Failed to save product')
    },
  })

  const handleEdit = (product: Product) => {
    setEditingProduct(product)
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
    setModalOpen(true)
  }

  const handleCreate = () => {
    setEditingProduct(null)
    form.resetFields()
    setModalOpen(true)
  }

  const handleFormSubmit = (values: Record<string, unknown>) => {
    saveMutation.mutate(values)
  }

  const columns = [
    { title: 'Code',     dataIndex: 'code',           key: 'code',       width: 120 },
    { title: 'Name',     dataIndex: 'name',           key: 'name' },
    { title: 'Category', dataIndex: 'category_name', key: 'category',   width: 180 },
    { title: 'Extrusion',dataIndex: 'extrusion_name', key: 'extrusion', width: 180 },
    { title: 'Unit',     dataIndex: 'unit_type_display', key: 'unit',  width: 120 },
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
          placeholder="Category"
          value={categoryId}
          onChange={(val) => { setCategoryId(val); setExtrusionId(null) }}
          style={{ width: 180 }}
          allowClear
          options={categoriesData?.results.map((c: MaterialCategory) => ({ value: c.id, label: c.name }))}
        />
        <Select
          placeholder="Extrusion Type"
          value={extrusionId}
          onChange={setExtrusionId}
          style={{ width: 200 }}
          allowClear
          options={extrusionsData?.results.map((e: ExtrusionType) => ({ value: e.id, label: `${e.name} (${e.category})` }))}
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
        onCancel={() => { setModalOpen(false); form.resetFields(); setEditingProduct(null) }}
        footer={null}
        width={560}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFormSubmit}
          initialValues={{ is_active: true, unit_type: 'BAR' }}
        >
          <Space style={{ width: '100%' }} direction="vertical" size={12}>
            <Space style={{ width: '100%' }} wrap>
              <Form.Item label="Product Code" name="code" rules={[{ required: true }]} style={{ flex: 1 }}>
                <Input placeholder="e.g. ALU-STILE-001" />
              </Form.Item>
              <Form.Item label="Name" name="name" rules={[{ required: true }]} style={{ flex: 2 }}>
                <Input placeholder="e.g. 40mm Aluminium Stile" />
              </Form.Item>
            </Space>

            <Space style={{ width: '100%' }} wrap>
              <Form.Item label="Category" name="category" style={{ flex: 1 }}>
                <Select
                  placeholder="Select category"
                  options={categoriesData?.results.map((c: MaterialCategory) => ({ value: c.id, label: c.name }))}
                  allowClear
                />
              </Form.Item>
              <Form.Item label="Extrusion Type" name="extrusion" style={{ flex: 1 }}>
                <Select
                  placeholder="Select extrusion"
                  options={extrusionsData?.results.map((e: ExtrusionType) => ({ value: e.id, label: `${e.name} (${e.category_display})` }))}
                  allowClear
                />
              </Form.Item>
            </Space>

            <Space style={{ width: '100%' }} wrap>
              <Form.Item label="Style" name="style" style={{ flex: 1 }}>
                <Input placeholder="e.g. standard" />
              </Form.Item>
              <Form.Item label="Colour" name="colour" style={{ flex: 1 }}>
                <Input placeholder="e.g. mill finish" />
              </Form.Item>
              <Form.Item label="Colour Code" name="colour_code" style={{ flex: 1 }}>
                <Input placeholder="e.g. MF" />
              </Form.Item>
            </Space>

            <Space style={{ width: '100%' }} wrap>
              <Form.Item label="Unit Type" name="unit_type" style={{ flex: 1 }}>
                <Select options={UNIT_OPTIONS} />
              </Form.Item>
              <Form.Item label="Active" name="is_active" valuePropName="checked" style={{ flex: 1 }}>
                <Switch />
              </Form.Item>
            </Space>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => { setModalOpen(false); form.resetFields(); setEditingProduct(null) }}>
                  Cancel
                </Button>
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