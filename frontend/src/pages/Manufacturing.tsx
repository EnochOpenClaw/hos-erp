import { useState } from 'react'
import {
  Table, Input, Select, Button, Space, Tag, Modal, Form, Switch, message,
  Drawer, Divider, Row, Col, InputNumber, Alert, Steps, Card, Popconfirm,
  Descriptions, Badge, Tabs, Tooltip, Typography,
} from 'antd'
import {
  PlusOutlined, EditOutlined, ReloadOutlined, SearchOutlined,
  DeleteOutlined, CheckCircleOutlined, FileTextOutlined, PlayCircleOutlined,
  LockOutlined, UnorderedListOutlined, FlagOutlined,
} from '@ant-design/icons'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { jobs as jobsApi, controlSheets, divisions, products as productsApi } from '../api'
import type { Job, Division, Product } from '../types'

const { Text } = Typography

// ─── Constants ────────────────────────────────────────────────────────────────

const JOB_STATUSES = [
  { value: 'draft',     label: 'Draft',            color: 'default' },
  { value: 'confirmed', label: 'Confirmed',         color: 'processing' },
  { value: 'ready',     label: 'Ready to Cut',      color: 'warning' },
  { value: 'cutting',   label: 'In Cutting',        color: 'blue' },
  { value: 'completed', label: 'Completed',        color: 'green' },
  { value: 'cancelled', label: 'Cancelled',        color: 'red' },
]

const OPENING_TYPES = [
  { value: 'door',      label: 'Door' },
  { value: 'window',    label: 'Window' },
  { value: 'flyscreen', label: 'Flyscreen' },
  { value: 'security',  label: 'Security Barrier' },
  { value: 'other',     label: 'Other' },
]

const LOCK_TYPES = [
  { value: 'none',     label: 'No Lock' },
  { value: 'standard', label: 'Standard Lock' },
  { value: 'deadbolt', label: 'Deadbolt' },
  { value: 'key',      label: 'Key Operated' },
  { value: 'thumb',    label: 'Thumb Turn' },
]

const MESH_TYPES = [
  { value: 'none',       label: 'No Mesh' },
  { value: 'fibreglass', label: 'Fibreglass' },
  { value: 'aluminium',  label: 'Aluminium' },
  { value: 'security',   label: 'Security Mesh' },
]

const FINISH_TYPES = [
  { value: 'mill',         label: 'Mill (Uncoated)' },
  { value: 'powdercoated', label: 'Powdercoated' },
]

const POSITION_TYPES = [
  { value: 'left',   label: 'Left Stile' },
  { value: 'right',  label: 'Right Stile' },
  { value: 'top',    label: 'Top Rail' },
  { value: 'bottom', label: 'Bottom Rail' },
  { value: 'mid',    label: 'Mid Rail' },
  { value: 'louvre', label: 'Louvre' },
  { value: 'track',  label: 'Track' },
  { value: 'other',  label: 'Other' },
]

const STATUS_STEPS = ['draft', 'confirmed', 'ready', 'cutting', 'completed']

const jobStatusColor = (s: string) => JOB_STATUSES.find(x => x.value === s)?.color ?? 'default'
const jobStatusLabel = (s: string) => JOB_STATUSES.find(x => x.value === s)?.label ?? s
const currentStep = (s: string) => STATUS_STEPS.indexOf(s)

// ─── Types ────────────────────────────────────────────────────────────────────

interface CSLineItem {
  product?: string
  length_mm?: number
  quantity: number
  finish: string
  powder_color: string
  position: string
  notes: string
}

// ─── Component ────────────────────────────────────────────────────────────────

export default function Manufacturing() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()

  const [jobSearch, setJobSearch] = useState('')
  const [jobStatus, setJobStatus] = useState<string | null>(null)

  const [jobModalOpen, setJobModalOpen] = useState(false)
  const [editingJob, setEditingJob] = useState<Job | null>(null)
  const [jobForm] = Form.useForm()

  const [jobDrawer, setJobDrawer] = useState<Job | null>(null)
  const [activeCsTab, setActiveCsTab] = useState<string>('')

  const [csModalOpen, setCsModalOpen] = useState(false)
  const [editingCS, setEditingCS] = useState<any | null>(null)
  const [csJob, setCsJob] = useState<Job | null>(null)
  const [csForm] = Form.useForm()
  const [csLines, setCsLines] = useState<CSLineItem[]>([
    { product: undefined, quantity: 1, finish: 'mill', powder_color: '', position: '', notes: '' },
  ])

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

  const { data: jobsData, isLoading: jobsLoading, refetch: refetchJobs } = useQuery({
    queryKey: ['jobs', jobSearch, jobStatus],
    queryFn: () => jobsApi.list({
      search: jobSearch || undefined,
      status: jobStatus || undefined,
    }),
    select: (res) => res.data,
  })

  // ── Mutations ─────────────────────────────────────────────────────────────

  const saveJobMutation = useMutation({
    mutationFn: (values: any) =>
      editingJob
        ? jobsApi.patch(editingJob.id, values)
        : jobsApi.create(values),
    onSuccess: (res: any) => {
      messageApi.success(editingJob ? 'Job updated' : 'Job created')
      setJobModalOpen(false)
      jobForm.resetFields()
      qc.invalidateQueries({ queryKey: ['jobs'] })
      const job = res.data ?? res
      setJobDrawer(job)
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Save failed')
    },
  })

  const saveCSMutation = useMutation({
    mutationFn: ({ jobId, data, csId }: { jobId: string; data: any; csId?: string }) =>
      csId
        ? controlSheets.patch(csId, data)
        : controlSheets.create({ ...data, job: jobId }),
    onSuccess: () => {
      messageApi.success('Control sheet saved')
      setCsModalOpen(false)
      csForm.resetFields()
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Save failed')
    },
  })

  const deleteCSMutation = useMutation({
    mutationFn: (id: string) => controlSheets.delete(id),
    onSuccess: () => {
      messageApi.success('Control sheet deleted')
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Delete failed')
    },
  })

  const generateReqMutation = useMutation({
    mutationFn: (id: string) => jobsApi.generateRequirements(id),
    onSuccess: (res: any) => {
      messageApi.success(`Generated ${res.requirements_created} cut requirements`)
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Generation failed')
    },
  })

  const runOptimizerMutation = useMutation({
    mutationFn: (id: string) => jobsApi.runOptimizer(id),
    onSuccess: (res: any) => {
      messageApi.success('Optimization complete')
      qc.invalidateQueries({ queryKey: ['jobs'] })
      if (res.data?.error) messageApi.warning(res.data.error)
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Optimizer failed')
    },
  })

  const markCompleteMutation = useMutation({
    mutationFn: (id: string) => jobsApi.markComplete(id),
    onSuccess: () => {
      messageApi.success('Job marked complete')
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Failed')
    },
  })

  const addCSMutation = useMutation({
    mutationFn: (jobId: string) => jobsApi.addControlSheet(jobId, {}),
    onSuccess: (res: any) => {
      qc.invalidateQueries({ queryKey: ['jobs'] })
      openEditCS(res, jobDrawer!)
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Failed')
    },
  })

  const confirmJobMutation = useMutation({
    mutationFn: (job: Job) => jobsApi.patch(job.id, { ...job, status: 'confirmed' }),
    onSuccess: (res: any) => {
      messageApi.success('Job confirmed')
      const updated = res.data ?? res
      setJobDrawer(updated)
      qc.invalidateQueries({ queryKey: ['jobs'] })
    },
    onError: (err: any) => {
      messageApi.error(err?.response?.data?.detail ?? 'Failed')
    },
  })

  // ── Table columns ─────────────────────────────────────────────────────────
  const jobColumns = [
    {
      title: 'Job Number', dataIndex: 'job_number', key: 'job_number', width: 140,
      render: (v: string, r: Job) => (
        <Button type="link" style={{ padding: 0, fontWeight: 600 }} onClick={() => openJobDrawer(r)}>{v}</Button>
      ),
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 140,
      render: (v: string) => <Tag color={jobStatusColor(v)}>{jobStatusLabel(v)}</Tag>,
    },
    {
      title: 'Description', dataIndex: 'description', key: 'description', ellipsis: true,
      render: (v: string, r: Job) => (
        <span>
          {v || <span style={{ color: '#bbb' }}>No description</span>}
          {r.priority > 0 && (
            <Tooltip title={`Priority ${r.priority}`}><FlagOutlined style={{ color: '#fa8c16', marginLeft: 6 }} /></Tooltip>
          )}
        </span>
      ),
    },
    { title: 'Customer', dataIndex: 'customer_name', key: 'customer', width: 150, ellipsis: true },
    { title: 'Cust. Ref', dataIndex: 'customer_ref', key: 'cust_ref', width: 100, ellipsis: true },
    { title: 'Div', dataIndex: 'division_code', key: 'div', width: 70 },
    {
      title: 'Sheets', dataIndex: 'control_sheet_count', key: 'cs_count', width: 70, align: 'center' as const,
      render: (v: number) => v > 0 ? <Badge count={v} style={{ backgroundColor: '#1890ff' }} /> : '—',
    },
    {
      title: 'Cut Design', dataIndex: 'cut_design_status', key: 'cut_design', width: 110,
      render: (v: string | null) => {
        if (!v) return <span style={{ color: '#bbb' }}>Not run</span>
        const colors: Record<string, string> = { draft: 'default', optimized: 'blue', released: 'processing', cut: 'green' }
        return <Tag color={colors[v] ?? 'default'}>{v}</Tag>
      },
    },
    {
      title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 110,
      render: (v: string) => new Date(v).toLocaleDateString(),
    },
    {
      title: '', key: 'actions', width: 100,
      render: (_: unknown, job: Job) => (
        <Space size={4}>
          <Button size="small" onClick={() => openJobDrawer(job)}>View</Button>
          {job.status !== 'completed' && job.status !== 'cancelled' && (
            <Button icon={<EditOutlined />} size="small" onClick={() => openEditJob(job)} />
          )}
        </Space>
      ),
    },
  ]

  // ── Handlers ─────────────────────────────────────────────────────────────
  const openJobDrawer = (job: Job) => {
    jobsApi.get(job.id).then(res => {
      setJobDrawer(res.data)
      setActiveCsTab(res.data.control_sheets?.[0]?.id ?? '')
    })
  }

  const openEditJob = (job: Job) => {
    setEditingJob(job)
    jobForm.setFieldsValue({
      division: job.division,
      description: job.description,
      customer_name: job.customer_name,
      customer_ref: job.customer_ref,
      priority: job.priority,
      notes: job.notes,
    })
    setJobModalOpen(true)
  }

  const openNewJob = () => {
    setEditingJob(null)
    jobForm.resetFields()
    setJobModalOpen(true)
  }

  const handleJobSubmit = (values: Record<string, unknown>) => {
    saveJobMutation.mutate(values)
  }

  const openNewCS = (job: Job) => {
    setEditingCS(null)
    setCsJob(job)
    csForm.resetFields()
    setCsLines([{ product: undefined, quantity: 1, finish: 'mill', powder_color: '', position: '', notes: '' }])
    setCsModalOpen(true)
  }

  const openEditCS = (cs: any, job: Job) => {
    setEditingCS(cs)
    setCsJob(job)
    csForm.setFieldsValue({
      name: cs.name,
      opening_type: cs.opening_type,
      width_mm: cs.width_mm,
      height_mm: cs.height_mm,
      lock_type: cs.lock_type,
      colour_name: cs.colour_name,
      colour_code: cs.colour_code,
      powder_coat: cs.powder_coat,
      mesh_type: cs.mesh_type,
      has_top_rail: cs.has_top_rail,
      has_bottom_rail: cs.has_bottom_rail,
      rail_width_mm: cs.rail_width_mm,
      hardware_notes: cs.hardware_notes,
    })
    setCsLines(cs.lines?.map((l: any) => ({
      product: l.product,
      length_mm: l.length_mm,
      quantity: l.quantity,
      finish: l.finish,
      powder_color: l.powder_color,
      position: l.position,
      notes: l.notes,
    })) ?? [{ product: undefined, quantity: 1, finish: 'mill', powder_color: '', position: '', notes: '' }])
    setCsModalOpen(true)
  }

  const handleCSSubmit = (values: Record<string, unknown>) => {
    if (!csJob) return
    const validLines = csLines.filter(l => l.product && l.quantity > 0)
    saveCSMutation.mutate({ jobId: csJob.id, data: { ...values, lines: validLines }, csId: editingCS?.id })
  }

  // ─── Render ─────────────────────────────────────────────────────────────
  return (
    <div style={{ padding: 0 }}>
      {contextHolder}

      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <h1 style={{ fontSize: 24, fontWeight: 600, margin: 0 }}>Manufacturing</h1>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={refetchJobs}>Refresh</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={openNewJob}>New Job</Button>
        </Space>
      </div>

      <Space style={{ marginBottom: 12 }} wrap>
        <Input
          placeholder="Search job number or customer…"
          value={jobSearch}
          onChange={(e) => setJobSearch(e.target.value)}
          style={{ width: 240 }}
          allowClear prefix={<SearchOutlined />}
        />
        <Select
          placeholder="All statuses"
          value={jobStatus}
          onChange={setJobStatus}
          style={{ width: 170 }}
          allowClear
          options={JOB_STATUSES.map(s => ({ value: s.value, label: s.label }))}
        />
      </Space>

      <Table
        rowKey="id"
        loading={jobsLoading}
        dataSource={jobsData?.results ?? []}
        columns={jobColumns}
        pagination={{ total: jobsData?.count ?? 0, showSizeChanger: true, showTotal: t => `${t} jobs` }}
      />

      {/* ── Job Create / Edit Modal ──────────────────────────────────────── */}
      <Modal
        open={jobModalOpen}
        title={editingJob ? `Edit Job ${editingJob.job_number}` : 'New Manufacturing Job'}
        onCancel={() => { setJobModalOpen(false); jobForm.resetFields() }}
        footer={null}
        width={620}
      >
        <Form
          form={jobForm}
          layout="vertical"
          onFinish={handleJobSubmit}
          initialValues={{ priority: 0 }}
        >
          <Row gutter={12}>
            <Col span={12}>
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
            <Col span={12}>
              <Form.Item label="Priority" name="priority" help="0 = normal, 1+ = urgent">
                <InputNumber min={0} max={99} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} placeholder="e.g. Aluminium doors for Garden City project" />
          </Form.Item>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Customer Name" name="customer_name">
                <Input placeholder="e.g. Garden City Developments" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Customer Ref / PO" name="customer_ref">
                <Input placeholder="e.g. GCD-2024-001" />
              </Form.Item>
            </Col>
          </Row>

          {editingJob && (
            <Form.Item label="Status" name="status">
              <Select options={JOB_STATUSES.map(s => ({ value: s.value, label: s.label }))} />
            </Form.Item>
          )}

          <Form.Item label="Notes" name="notes">
            <Input.TextArea rows={2} placeholder="Special instructions, site info…" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => { setJobModalOpen(false); jobForm.resetFields() }}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={saveJobMutation.isPending}>
                {editingJob ? 'Update Job' : 'Create Job'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* ── Job Detail Drawer ────────────────────────────────────────────── */}
      <Drawer
        open={!!jobDrawer}
        title={jobDrawer ? `Job ${jobDrawer.job_number}` : ''}
        onClose={() => { setJobDrawer(null); setActiveCsTab('') }}
        width={900}
        extra={
          jobDrawer && (jobDrawer.status === 'draft' || jobDrawer.status === 'confirmed') ? (
            <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => openNewCS(jobDrawer!)}>
              Add Control Sheet
            </Button>
          ) : null
        }
      >
        {jobDrawer && (
          <div>
            <Steps
              current={currentStep(jobDrawer.status)}
              size="small"
              style={{ marginBottom: 16 }}
              items={JOB_STATUSES.filter(s => STATUS_STEPS.includes(s.value)).map(s => ({
                title: s.label,
                icon: s.value === 'ready' ? <PlayCircleOutlined /> :
                      s.value === 'cutting' ? <FileTextOutlined /> :
                      s.value === 'completed' ? <CheckCircleOutlined /> : undefined,
              }))}
            />

            <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Description">{jobDrawer.description || '—'}</Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={jobStatusColor(jobDrawer.status)}>{jobStatusLabel(jobDrawer.status)}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Customer">{jobDrawer.customer_name || '—'}</Descriptions.Item>
              <Descriptions.Item label="Customer Ref">{jobDrawer.customer_ref || '—'}</Descriptions.Item>
              <Descriptions.Item label="Division">{jobDrawer.division_code}</Descriptions.Item>
              <Descriptions.Item label="Priority">
                {jobDrawer.priority > 0
                  ? <Badge count={`${jobDrawer.priority}`} style={{ backgroundColor: '#fa8c16' }} />
                  : 'Normal'}
              </Descriptions.Item>
            </Descriptions>

            {jobDrawer.notes && (
              <Alert message={jobDrawer.notes} type="info" showIcon style={{ marginBottom: 12 }} />
            )}

            {/* Action buttons */}
            <Space style={{ marginBottom: 16 }} wrap>
              {jobDrawer.status === 'draft' && (
                <Button icon={<CheckCircleOutlined />} onClick={() => confirmJobMutation.mutate(jobDrawer)} loading={confirmJobMutation.isPending}>
                  Confirm Job
                </Button>
              )}
              {(jobDrawer.status === 'confirmed' || jobDrawer.status === 'ready') && (
                <Button type="primary" icon={<FileTextOutlined />} onClick={() => generateReqMutation.mutate(jobDrawer.id)} loading={generateReqMutation.isPending}>
                  Generate Cut Requirements
                </Button>
              )}
              {jobDrawer.status === 'ready' && (
                <Button icon={<PlayCircleOutlined />} onClick={() => runOptimizerMutation.mutate(jobDrawer.id)} loading={runOptimizerMutation.isPending}>
                  Run Optimizer
                </Button>
              )}
              {jobDrawer.status === 'cutting' && (
                <Button icon={<UnorderedListOutlined />} onClick={() => window.open(`/factory/${jobDrawer.id}`, '_blank')}>
                  Open Cutting Queue
                </Button>
              )}
              {jobDrawer.status === 'cutting' && (
                <Popconfirm title="Mark job as completed?" onConfirm={() => markCompleteMutation.mutate(jobDrawer.id)}>
                  <Button type="primary" icon={<CheckCircleOutlined />}>Mark Complete</Button>
                </Popconfirm>
              )}
            </Space>

            <Divider orientation="left" plain style={{ margin: '8px 0' }}>
              Control Sheets ({jobDrawer.control_sheets?.length ?? 0})
            </Divider>

            {!jobDrawer.control_sheets || jobDrawer.control_sheets.length === 0 ? (
              <Card size="small" style={{ textAlign: 'center' }}>
                <div style={{ color: '#999', marginBottom: 8 }}>No control sheets yet.</div>
                <Button size="small" icon={<PlusOutlined />} onClick={() => openNewCS(jobDrawer)}>Add First Sheet</Button>
              </Card>
            ) : (
              <Tabs
                activeKey={activeCsTab}
                onChange={setActiveCsTab}
                type="card"
                items={jobDrawer.control_sheets.map((cs: any) => ({
                  key: cs.id,
                  label: cs.name || `Opening ${cs.sheet_number}`,
                  children: (
                    <CSView
                      cs={cs}
                      job={jobDrawer}
                      onEdit={() => openEditCS(cs, jobDrawer)}
                      onFinalize={() => {
                        controlSheets.finalize(cs.id).then(() => {
                          messageApi.success('Sheet finalized')
                          jobsApi.get(jobDrawer.id).then(r => setJobDrawer(r.data))
                        })
                      }}
                      onDelete={() => deleteCSMutation.mutate(cs.id)}
                    />
                  ),
                }))}
                extra={
                  <Button size="small" icon={<PlusOutlined />} onClick={() => openNewCS(jobDrawer)}>Sheet</Button>
                }
              />
            )}
          </div>
        )}
      </Drawer>

      {/* ── Control Sheet Create / Edit Modal ────────────────────────────── */}
      <Modal
        open={csModalOpen}
        title={editingCS
          ? `Edit — ${editingCS.name || `Opening ${editingCS.sheet_number}`}`
          : `New Control Sheet — ${csJob?.job_number ?? ''}`}
        onCancel={() => { setCsModalOpen(false); csForm.resetFields() }}
        footer={null}
        width={820}
      >
        <Form
          form={csForm}
          layout="vertical"
          onFinish={handleCSSubmit}
          initialValues={{
            opening_type: 'door',
            has_top_rail: true,
            has_bottom_rail: true,
            powder_coat: false,
            mesh_type: 'none',
          }}
        >
          <Row gutter={12}>
            <Col span={8}>
              <Form.Item label="Opening Name" name="name">
                <Input placeholder="e.g. Front Door, Window A" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Opening Type" name="opening_type">
                <Select options={OPENING_TYPES} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Lock Type" name="lock_type">
                <Select placeholder="Select…" options={LOCK_TYPES} allowClear />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={8}>
              <Form.Item label="Width (mm)" name="width_mm">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="e.g. 1200" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Height (mm)" name="height_mm">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="e.g. 2100" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Rail Width (mm)" name="rail_width_mm">
                <InputNumber min={0} style={{ width: '100%' }} placeholder="e.g. 50" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={8}>
              <Form.Item label="Colour Name" name="colour_name">
                <Input placeholder="e.g. Charcoal" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Colour Code" name="colour_code">
                <Input placeholder="e.g. 8712123456" />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item label="Powder Coat?" name="powder_coat" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={4}>
              <Form.Item label="Mesh Type" name="mesh_type">
                <Select options={MESH_TYPES} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={12}>
            <Col span={8}>
              <Form.Item label="Top Rail?" name="has_top_rail" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Bottom Rail?" name="has_bottom_rail" valuePropName="checked">
                <Switch />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item label="Hardware Notes" name="hardware_notes">
            <Input.TextArea rows={2} placeholder="Lock set, handles, hinges, screws…" />
          </Form.Item>

          {/* Extrusion lines */}
          <Divider style={{ margin: '0 0 12px' }}>Extrusion Requirements</Divider>

          <div style={{ display: 'flex', gap: 8, marginBottom: 4, fontWeight: 600, fontSize: 12, color: '#666', alignItems: 'flex-end' }}>
            <div style={{ flex: 2 }}>Product</div>
            <div style={{ width: 80 }}>Length (mm)</div>
            <div style={{ width: 60 }}>Qty</div>
            <div style={{ width: 110 }}>Finish</div>
            <div style={{ width: 110 }}>Position</div>
            <div style={{ flex: 1 }}>Notes</div>
            <div style={{ width: 32 }}></div>
          </div>

          {csLines.map((line, idx) => (
            <div key={idx} style={{ display: 'flex', gap: 8, marginBottom: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
              <div style={{ flex: 2 }}>
                <Select
                  placeholder="Product…"
                  showSearch filterOption={(i, o) => (o?.label ?? '').toLowerCase().includes(i.toLowerCase())}
                  value={line.product}
                  onChange={val => { const u = [...csLines]; u[idx].product = val; setCsLines(u) }}
                  style={{ width: '100%' }}
                  options={productsData?.results.map((p: Product) => ({
                    value: p.id,
                    label: `${p.code} — ${p.name} (${p.length_mm ?? '?'}mm)`,
                  }))}
                />
              </div>
              <div style={{ width: 80 }}>
                <InputNumber
                  min={0}
                  value={line.length_mm}
                  onChange={val => { const u = [...csLines]; u[idx].length_mm = val ?? undefined; setCsLines(u) }}
                  style={{ width: '100%' }}
                  placeholder="mm"
                />
              </div>
              <div style={{ width: 60 }}>
                <InputNumber
                  min={1}
                  value={line.quantity}
                  onChange={val => { const u = [...csLines]; u[idx].quantity = val ?? 1; setCsLines(u) }}
                  style={{ width: '100%' }}
                />
              </div>
              <div style={{ width: 110 }}>
                <Select
                  value={line.finish}
                  onChange={val => { const u = [...csLines]; u[idx].finish = val; setCsLines(u) }}
                  style={{ width: '100%' }}
                  options={FINISH_TYPES}
                />
              </div>
              <div style={{ width: 110 }}>
                <Select
                  placeholder="Position…"
                  value={line.position}
                  onChange={val => { const u = [...csLines]; u[idx].position = val; setCsLines(u) }}
                  style={{ width: '100%' }}
                  options={POSITION_TYPES}
                  allowClear
                />
              </div>
              <div style={{ flex: 1 }}>
                <Input
                  placeholder="Note…"
                  value={line.notes}
                  onChange={e => { const u = [...csLines]; u[idx].notes = e.target.value; setCsLines(u) }}
                />
              </div>
              <Button
                icon={<DeleteOutlined />}
                danger
                onClick={() => setCsLines(csLines.filter((_, i) => i !== idx))}
                disabled={csLines.length === 1}
              />
            </div>
          ))}

          <Button
            size="small"
            icon={<PlusOutlined />}
            onClick={() => setCsLines([...csLines, { product: undefined, quantity: 1, finish: 'mill', powder_color: '', position: '', notes: '' }])}
            style={{ marginBottom: 16 }}
          >
            Add Line
          </Button>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setCsModalOpen(false)}>Cancel</Button>
              <Button type="primary" htmlType="submit" loading={saveCSMutation.isPending}>
                {editingCS ? 'Update Sheet' : 'Create Sheet'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

// ─── ControlSheet view (within drawer tab) ───────────────────────────────────

function CSView({ cs, job, onEdit, onFinalize, onDelete }: {
  cs: any
  job: Job
  onEdit: () => void
  onFinalize: () => void
  onDelete: () => void
}) {
  return (
    <div>
      <Descriptions column={3} size="small" style={{ marginBottom: 12 }}>
        <Descriptions.Item label="Type">{OPENING_TYPES.find(o => o.value === cs.opening_type)?.label}</Descriptions.Item>
        <Descriptions.Item label="Dimensions">
          {cs.width_mm && cs.height_mm ? `${cs.width_mm} × ${cs.height_mm} mm` : '—'}
        </Descriptions.Item>
        <Descriptions.Item label="Lock">{LOCK_TYPES.find(l => l.value === cs.lock_type)?.label ?? '—'}</Descriptions.Item>
        <Descriptions.Item label="Colour">{cs.colour_name || '—'} {cs.colour_code && `(${cs.colour_code})`}</Descriptions.Item>
        <Descriptions.Item label="Powder Coat">{cs.powder_coat ? 'Yes' : 'No'}</Descriptions.Item>
        <Descriptions.Item label="Mesh">{MESH_TYPES.find(m => m.value === cs.mesh_type)?.label}</Descriptions.Item>
        <Descriptions.Item label="Top Rail">{cs.has_top_rail ? 'Yes' : 'No'}</Descriptions.Item>
        <Descriptions.Item label="Bottom Rail">{cs.has_bottom_rail ? 'Yes' : 'No'}</Descriptions.Item>
        {cs.rail_width_mm > 0 && <Descriptions.Item label="Rail Width">{cs.rail_width_mm}mm</Descriptions.Item>}
        {cs.signed_off_by && (
          <Descriptions.Item label="Signed Off">
            {cs.signed_off_by} at {new Date(cs.signed_off_at).toLocaleString()}
          </Descriptions.Item>
        )}
      </Descriptions>

      {cs.hardware_notes && (
        <Alert
          message={<span><strong>Hardware:</strong> {cs.hardware_notes}</span>}
          type="info" showIcon style={{ marginBottom: 12 }}
        />
      )}

      <Table
        rowKey="id"
        dataSource={cs.lines ?? []}
        columns={[
          { title: 'Product', dataIndex: 'product_name', key: 'product', ellipsis: true },
          { title: 'Length', dataIndex: 'length_mm', key: 'length', width: 80, align: 'right' as const,
            render: (v: number) => v ? `${v}mm` : '—' },
          { title: 'Qty', dataIndex: 'quantity', key: 'qty', width: 60, align: 'center' as const },
          { title: 'Finish', dataIndex: 'finish', key: 'finish', width: 130,
            render: (v: string) => FINISH_TYPES.find(f => f.value === v)?.label ?? v },
          { title: 'Position', dataIndex: 'position', key: 'position', width: 110,
            render: (v: string) => POSITION_TYPES.find(p => p.value === v)?.label ?? v },
          { title: 'Notes', dataIndex: 'notes', key: 'notes', ellipsis: true },
        ]}
        pagination={false}
        size="small"
        summary={() => (
          <Table.Summary fixed>
            <Table.Summary.Row>
              <Table.Summary.Cell index={0} colSpan={6} align="right">
                <strong>{cs.lines?.length ?? 0} line(s)</strong>
              </Table.Summary.Cell>
            </Table.Summary.Row>
          </Table.Summary>
        )}
      />

      <Space style={{ marginTop: 12 }}>
        {cs.status === 'draft' && (
          <>
            <Button size="small" icon={<EditOutlined />} onClick={onEdit}>Edit</Button>
            <Button size="small" type="primary" icon={<LockOutlined />} onClick={onFinalize}>Finalize</Button>
            <Button size="small" danger icon={<DeleteOutlined />} onClick={onDelete}>Delete</Button>
          </>
        )}
        {cs.status !== 'draft' && (
          <Tag color="green"><LockOutlined /> Finalized</Tag>
        )}
      </Space>
    </div>
  )
}