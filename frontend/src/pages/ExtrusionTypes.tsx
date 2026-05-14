import { useState } from 'react'
import { Table, Input, Select, Button, Space, Tag, Modal, Form, message, Switch } from 'antd'
import { PlusOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { extrusionTypes, materialCategories } from '../api'
import type { ExtrusionType } from '../types'

const CATEGORY_OPTIONS = [
  { value: 'frame', label: 'Frame' },
  { value: 'rail', label: 'Rail' },
  { value: 'blade', label: 'Blade/Louvre' },
  { value: 'track', label: 'Track' },
  { value: 'compensating', label: 'Compensating' },
  { value: 'rod', label: 'Rod' },
  { value: 'hardware', label: 'Hardware' },
]

const CATEGORY_COLORS: Record<string, string> = {
  frame: 'blue', rail: 'cyan', blade: 'green',
  track: 'orange', compensating: 'purple', rod: 'gold', hardware: 'default',
}

export default function ExtrusionTypes() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<ExtrusionType | null>(null)
  const [form] = Form.useForm()

  const { data: categoriesData } = useQuery({
    queryKey: ['material-categories'],
    queryFn: () => materialCategories.list(),
    select: (res) => res.data,
  })

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['extrusion-types'],
    queryFn: () => extrusionTypes.list(),
    select: (res) => res.data,
  })

  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (editing) return extrusionTypes.patch(editing.id, values)
      return extrusionTypes.create(values)
    },
    onSuccess: () => {
      messageApi.success(editing ? 'Extrusion updated' : 'Extrusion created')
      setModalOpen(false)
      form.resetFields()
      setEditing(null)
      qc.invalidateQueries({ queryKey: ['extrusion-types'] })
    },
    onError: () => messageApi.error('Failed to save'),
  })

  const handleEdit = (record: ExtrusionType) => {
    setEditing(record)
    form.setFieldsValue({
      name: record.name,
      category: record.category,
      description: record.description,
      die_number: record.die_number,
      standard_bar_mm: record.standard_bar_mm,
      kerf_mm: record.kerf_mm,
      weight_per_mm: record.weight_per_mm,
      is_active: record.is_active,
    })
    setModalOpen(true)
  }

  const handleCreate = () => { setEditing(null); form.resetFields(); setModalOpen(true) }
  const handleFormSubmit = (values: Record<string, unknown>) => saveMutation.mutate(values)

  const columns = [
    { title: 'Name', dataIndex: 'name', key: 'name' },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      width: 140,
      render: (val: string) => (
        <Tag color={CATEGORY_COLORS[val] ?? 'default'}>{val?.toUpperCase()}</Tag>
      ),
    },
    { title: 'Die Number', dataIndex: 'die_number', key: 'die_number', width: 120 },
    { title: 'Bar Length', dataIndex: 'standard_bar_mm', key: 'standard_bar_mm', width: 100 },
    { title: 'Kerf', dataIndex: 'kerf_mm', key: 'kerf_mm', width: 70 },
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
      render: (_: unknown, record: ExtrusionType) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {contextHolder}
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 16 }}>Extrusion Types</h1>

      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Add Extrusion</Button>
      </Space>

      <Table
        rowKey="id"
        loading={isLoading}
        dataSource={data?.results ?? []}
        columns={columns}
        pagination={{ total: data?.count ?? 0, showSizeChanger: true }}
      />

      <Modal
        open={modalOpen}
        title={editing ? 'Edit Extrusion Type' : 'Add Extrusion Type'}
        onCancel={() => { setModalOpen(false); form.resetFields() }}
        footer={null}
        width={560}
      >
        <Form form={form} layout="vertical" onFinish={handleFormSubmit} initialValues={{ is_active: true, standard_bar_mm: 6300, kerf_mm: 4 }}>
          <Space style={{ width: '100%' }} direction="vertical" size={12}>
            <Space style={{ width: '100%' }} wrap>
              <Form.Item label="Name" name="name" rules={[{ required: true }]} style={{ flex: 2 }}>
                <Input placeholder="e.g. 40mm End Cap" />
              </Form.Item>
              <Form.Item label="Category" name="category" rules={[{ required: true }]} style={{ flex: 1 }}>
                <Select placeholder="Select category" options={CATEGORY_OPTIONS} />
              </Form.Item>
            </Space>

            <Space style={{ width: '100%' }} wrap>
              <Form.Item label="Die Number" name="die_number" style={{ flex: 1 }}>
                <Input placeholder="e.g. D-4001" />
              </Form.Item>
              <Form.Item label="Bar Length (mm)" name="standard_bar_mm" style={{ flex: 1 }}>
                <Input type="number" placeholder="6300" />
              </Form.Item>
              <Form.Item label="Kerf (mm)" name="kerf_mm" style={{ flex: 1 }}>
                <Input type="number" placeholder="4" />
              </Form.Item>
            </Space>

            <Form.Item label="Weight per mm (kg)" name="weight_per_mm">
              <Input type="number" placeholder="e.g. 0.0012" step="0.000001" />
            </Form.Item>

            <Form.Item label="Description" name="description">
              <Input.TextArea rows={2} placeholder="Optional description..." />
            </Form.Item>

            <Form.Item label="Active" name="is_active" valuePropName="checked">
              <Switch />
            </Form.Item>

            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => { setModalOpen(false); form.resetFields() }}>Cancel</Button>
                <Button type="primary" htmlType="submit" loading={saveMutation.isPending}>
                  {editing ? 'Update' : 'Create'}
                </Button>
              </Space>
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}