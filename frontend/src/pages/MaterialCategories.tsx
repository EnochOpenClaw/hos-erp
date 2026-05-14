import { useState } from 'react'
import { Table, Input, Button, Space, Tag, Modal, Form, message } from 'antd'
import { PlusOutlined, EditOutlined, ReloadOutlined } from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { materialCategories } from '../api'
import type { MaterialCategory } from '../types'

export default function MaterialCategories() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()

  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<MaterialCategory | null>(null)
  const [form] = Form.useForm()

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['material-categories'],
    queryFn: () => materialCategories.list(),
    select: (res) => res.data,
  })

  const saveMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (editing) return materialCategories.patch(editing.id, values)
      return materialCategories.create(values)
    },
    onSuccess: () => {
      messageApi.success(editing ? 'Category updated' : 'Category created')
      setModalOpen(false)
      form.resetFields()
      setEditing(null)
      qc.invalidateQueries({ queryKey: ['material-categories'] })
    },
    onError: () => messageApi.error('Failed to save'),
  })

  const handleEdit = (record: MaterialCategory) => {
    setEditing(record)
    form.setFieldsValue({ name: record.name, description: record.description, sort_order: record.sort_order })
    setModalOpen(true)
  }

  const handleCreate = () => { setEditing(null); form.resetFields(); setModalOpen(true) }
  const handleFormSubmit = (values: Record<string, unknown>) => saveMutation.mutate(values)

  const columns = [
    { title: 'Sort', dataIndex: 'sort_order', key: 'sort_order', width: 70 },
    { title: 'Name', dataIndex: 'name', key: 'name' },
    { title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true },
    {
      title: 'Products',
      dataIndex: 'product_count',
      key: 'product_count',
      width: 100,
      render: (n: number) => <Tag>{n ?? 0}</Tag>,
    },
    { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 120 },
    {
      title: '',
      key: 'actions',
      width: 60,
      render: (_: unknown, record: MaterialCategory) => (
        <Button icon={<EditOutlined />} size="small" onClick={() => handleEdit(record)} />
      ),
    },
  ]

  return (
    <div style={{ padding: 24 }}>
      {contextHolder}
      <h1 style={{ fontSize: 24, fontWeight: 600, marginBottom: 16 }}>Material Categories</h1>

      <Space style={{ marginBottom: 16 }}>
        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>Add Category</Button>
      </Space>

      <Table rowKey="id" loading={isLoading} dataSource={data?.results ?? []} columns={columns} pagination={{ total: data?.count ?? 0 }} />

      <Modal open={modalOpen} title={editing ? 'Edit Category' : 'Add Category'} onCancel={() => { setModalOpen(false); form.resetFields() }} footer={null} width={480}>
        <Form form={form} layout="vertical" onFinish={handleFormSubmit} initialValues={{ sort_order: 0 }}>
          <Space style={{ width: '100%' }} direction="vertical" size={12}>
            <Form.Item label="Name" name="name" rules={[{ required: true }]}>
              <Input placeholder="e.g. Frame" />
            </Form.Item>
            <Form.Item label="Description" name="description">
              <Input.TextArea rows={3} placeholder="Optional description..." />
            </Form.Item>
            <Form.Item label="Sort Order" name="sort_order">
              <Input type="number" placeholder="0" />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
              <Space>
                <Button onClick={() => { setModalOpen(false); form.resetFields() }}>Cancel</Button>
                <Button type="primary" htmlType="submit" loading={saveMutation.isPending}>{editing ? 'Update' : 'Create'}</Button>
              </Space>
            </Form.Item>
          </Space>
        </Form>
      </Modal>
    </div>
  )
}