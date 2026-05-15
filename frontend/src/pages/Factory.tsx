import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Card, Row, Col, Progress, Badge, Typography, Space, Button, message, Alert, Statistic,
} from 'antd'
import {
  ReloadOutlined, ScissorOutlined,
} from '@ant-design/icons'
import { api } from '../api'

const { Text, Title } = Typography

// ─── Types (mirror backend structure) ─────────────────────────────────────

interface Cut {
  cut_id: string
  bar_id: string
  position_mm: number
  length_mm: number
  item_id: number
  is_cut: boolean
  style: string
  colour: string
  colour_code: string
}

interface Bar {
  bar_id: string
  bar_no: number
  stock_len: number
  offcut_mm: number
  offcut_keep: boolean
  offcut_bin: string
  is_flipped: boolean
  is_complete: boolean
  cuts: Cut[]
}

interface Section {
  heading: string
  extrusion: string
  colour: string
  colour_code: string
  stock_len: string
  bars: Bar[]
}

interface Offcut {
  id: string
  extrusion: string
  style: string
  colour: string
  colour_code: string
  length_mm: number
  bin_code: string
  stock_len: number
}

interface FactoryJob {
  job_id: string
  job_number: string
  description: string
  division: string
  priority: number
  total_bars: number
  done_bars: number
  total_cuts: number
  done_cuts: number
  progress_pct: number
  status: string
}

interface FactoryJobDetail {
  job_id: string
  job_number: string
  description: string
  division: string
  status: string
  offcut_keep_min_mm: number
  offcuts: Offcut[]
  sections: Section[]
}

// ─── API ─────────────────────────────────────────────────────────────────────

const factory = {
  queue: () => api.get<FactoryJob[]>('/manufacturing/factory/'),
  job: (id: string) => api.get<FactoryJobDetail>(`/manufacturing/factory/${id}/`),
  flipBar: (jobId: string, barId: string) =>
    api.post(`/manufacturing/factory/${jobId}/flip_bar/${barId}/`),
  markCut: (jobId: string, cutId: string) =>
    api.post(`/manufacturing/factory/${jobId}/mark_cut/${cutId}/`),
  resetBar: (jobId: string, barId: string) =>
    api.post(`/manufacturing/factory/${jobId}/reset_bar/${barId}/`),
}

// ─── Colour helpers ─────────────────────────────────────────────────────────

const ITEM_COLORS = [
  '#2563EB', '#DC2626', '#16A34A', '#D97706', '#7C3AED',
  '#0891B2', '#DB2777', '#EA580C', '#4F46E5', '#65A30D',
]
function itemColor(itemNo: number): string {
  return ITEM_COLORS[(itemNo - 1) % ITEM_COLORS.length]
}

// ─── Component ────────────────────────────────────────────────────────────

export default function Factory() {
  const qc = useQueryClient()
  const [messageApi, contextHolder] = message.useMessage()
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  const queueQuery = useQuery({
    queryKey: ['factory-queue'],
    queryFn: () => factory.queue().then(r => r.data),
    refetchInterval: 15000,
  })

  const detailQuery = useQuery({
    queryKey: ['factory-job', selectedJobId],
    queryFn: () => factory.job(selectedJobId!).then(r => r.data),
    enabled: !!selectedJobId,
  })

  const flipBarMutation = useMutation({
    mutationFn: ({ jobId, barId }: { jobId: string; barId: string }) =>
      factory.flipBar(jobId, barId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['factory-job', selectedJobId] })
      qc.invalidateQueries({ queryKey: ['factory-queue'] })
    },
    onError: (err: any) => messageApi.error(err?.message ?? 'Flip failed'),
  })

  const markCutMutation = useMutation({
    mutationFn: ({ jobId, cutId }: { jobId: string; cutId: string }) =>
      factory.markCut(jobId, cutId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['factory-job', selectedJobId] })
      qc.invalidateQueries({ queryKey: ['factory-queue'] })
    },
    onError: (err: any) => messageApi.error(err?.message ?? 'Mark cut failed'),
  })

  const resetBarMutation = useMutation({
    mutationFn: ({ jobId, barId }: { jobId: string; barId: string }) =>
      factory.resetBar(jobId, barId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['factory-job', selectedJobId] })
      qc.invalidateQueries({ queryKey: ['factory-queue'] })
    },
    onError: (err: any) => messageApi.error(err?.message ?? 'Reset failed'),
  })

  // Auto-select first job
  useEffect(() => {
    if (!selectedJobId && queueQuery.data?.length) {
      setSelectedJobId(queueQuery.data[0].job_id)
    }
  }, [queueQuery.data])

  const detail = detailQuery.data

  return (
    <>
      {contextHolder}
      <div style={{ padding: 16 }}>
        <Space style={{ marginBottom: 16 }}>
          <Title level={4} style={{ margin: 0 }}>
            <ScissorOutlined /> Factory Cutting Queue
          </Title>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              qc.invalidateQueries({ queryKey: ['factory-queue'] })
              if (selectedJobId) qc.invalidateQueries({ queryKey: ['factory-job', selectedJobId] })
            }}
          >
            Refresh
          </Button>
        </Space>

        <Row gutter={16}>
          {/* ── Left: job queue sidebar ── */}
          <Col span={8}>
            {queueQuery.isLoading ? (
              <Card loading />
            ) : !queueQuery.data?.length ? (
              <Card>
                <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>
                  No jobs in cutting queue.
                  <br />
                  Jobs appear here when status is "Ready" or "In Cutting".
                </div>
              </Card>
            ) : (
              queueQuery.data.map((job) => (
                <Card
                  key={job.job_id}
                  size="small"
                  hoverable
                  style={{
                    marginBottom: 8,
                    border: selectedJobId === job.job_id ? '2px solid #1677ff' : undefined,
                    cursor: 'pointer',
                  }}
                  onClick={() => setSelectedJobId(job.job_id)}
                >
                  <Row justify="space-between" align="middle">
                    <Col>
                      <Space direction="vertical" size={2}>
                        <Text strong>{job.job_number}</Text>
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          {job.description || '—'}
                        </Text>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {job.division} · {job.total_bars} bars · {job.total_cuts} cuts
                        </Text>
                      </Space>
                    </Col>
                    <Col>
                      <Progress
                        type="circle"
                        percent={job.progress_pct}
                        size={48}
                        strokeColor={job.progress_pct === 100 ? '#52c41a' : '#1677ff'}
                      />
                    </Col>
                  </Row>
                  {job.priority > 0 && (
                    <Badge
                      count={`Priority ${job.priority}`}
                      style={{ marginTop: 4, backgroundColor: '#fa8c16' }}
                    />
                  )}
                </Card>
              ))
            )}
          </Col>

          {/* ── Right: per-job cutting detail ── */}
          <Col span={16}>
            {!selectedJobId ? (
              <Card>
                <div style={{ textAlign: 'center', color: '#999', padding: 40 }}>
                  <ScissorOutlined style={{ fontSize: 32 }} />
                  <p style={{ marginTop: 8 }}>Select a job from the queue to see the cutting plan.</p>
                </div>
              </Card>
            ) : detailQuery.isLoading ? (
              <Card loading />
            ) : !detail ? (
              <Card>
                <Alert type="error" message="Failed to load job details." />
              </Card>
            ) : (
              <>
                {/* Job header */}
                <Card size="small" style={{ marginBottom: 12 }}>
                  <Row justify="space-between">
                    <Col>
                      <Space direction="vertical" size={4}>
                        <Title level={5} style={{ margin: 0 }}>{detail.job_number}</Title>
                        <Text>{detail.description || '—'}</Text>
                      </Space>
                    </Col>
                    <Col>
                      <Space size="large">
                        <Statistic
                          title="Bars"
                          value={detail.sections.reduce((s: number, sec: Section) => s + sec.bars.length, 0)}
                          valueStyle={{ fontSize: 18 }}
                        />
                        <Statistic
                          title="Keep Offcuts"
                          value={detail.offcuts.length}
                          valueStyle={{ fontSize: 18, color: '#52c41a' }}
                        />
                      </Space>
                    </Col>
                  </Row>
                </Card>

                {/* Keepable offcuts */}
                {detail.offcuts.length > 0 && (
                  <Card
                    size="small"
                    style={{ marginBottom: 12, background: '#f6ffed', border: '1px solid #b7eb8f' }}
                  >
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      ♻️ Keepable Offcuts ({detail.offcut_keep_min_mm}mm min)
                    </Text>
                    <Space wrap>
                      {detail.offcuts.map((o: Offcut) => (
                        <Card
                          key={o.id}
                          size="small"
                          style={{ background: '#ffffff', border: '1px solid #b7eb8f' }}
                        >
                          <Space direction="vertical" size={1}>
                            <Text strong style={{ color: '#52c41a' }}>{o.length_mm}mm</Text>
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              {o.extrusion} · {o.colour} · {o.colour_code}
                            </Text>
                            <Text type="secondary" style={{ fontSize: 11 }}>
                              Bin: {o.bin_code}
                            </Text>
                          </Space>
                        </Card>
                      ))}
                    </Space>
                  </Card>
                )}

                {/* Per-section bars */}
                {detail.sections.map((section: Section) => (
                  <Card key={section.heading} size="small" style={{ marginBottom: 12 }}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>
                      {section.heading}
                    </Text>
                    {section.bars.map((bar: Bar) => (
                      <Card
                        key={bar.bar_id}
                        size="small"
                        style={{
                          marginBottom: 8,
                          background: bar.is_complete
                            ? '#f6ffed'
                            : bar.is_flipped
                            ? '#e6f4ff'
                            : '#fff',
                          border: '1px solid #d9d9d9',
                        }}
                        bodyStyle={{ padding: '8px 12px' }}
                      >
                        <Row justify="space-between" align="middle" style={{ marginBottom: 6 }}>
                          <Col>
                            <Space>
                              <Text strong>Bar {bar.bar_no}</Text>
                              <Text type="secondary">{bar.stock_len}mm stock</Text>
                              {bar.is_complete ? (
                                <Badge status="success" text="Complete" />
                              ) : bar.is_flipped ? (
                                <Badge status="processing" text="On Machine" />
                              ) : (
                                <Badge status="default" text="Waiting" />
                              )}
                            </Space>
                          </Col>
                          <Col>
                            <Space>
                              {bar.offcut_keep ? (
                                <Text style={{ color: '#52c41a', fontSize: 12 }}>
                                  Offcut: {bar.offcut_mm}mm → Bin {bar.offcut_bin || '—'}
                                </Text>
                              ) : (
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  Offcut: {bar.offcut_mm}mm (discard)
                                </Text>
                              )}
                              {!bar.is_complete && (
                                <>
                                  <Button
                                    size="small"
                                    onClick={() => flipBarMutation.mutate({ jobId: detail.job_id, barId: bar.bar_id })}
                                    loading={flipBarMutation.isPending}
                                  >
                                    {bar.is_flipped ? 'Flip Off' : 'Flip On'}
                                  </Button>
                                  <Button
                                    size="small"
                                    onClick={() => resetBarMutation.mutate({ jobId: detail.job_id, barId: bar.bar_id })}
                                    loading={resetBarMutation.isPending}
                                  >
                                    Reset
                                  </Button>
                                </>
                              )}
                            </Space>
                          </Col>
                        </Row>

                        {/* Cut chips */}
                        <Space wrap>
                          {bar.cuts.map((cut: Cut) => (
                            <Button
                              key={cut.cut_id}
                              size="small"
                              onClick={() => markCutMutation.mutate({ jobId: detail.job_id, cutId: cut.cut_id })}
                              style={{
                                background: cut.is_cut ? '#52c41a' : itemColor(cut.item_id),
                                color: '#fff',
                                border: 'none',
                                height: 'auto',
                                padding: '4px 8px',
                                marginBottom: 4,
                                fontWeight: cut.is_cut ? 'bold' : 'normal',
                                textDecoration: cut.is_cut ? 'line-through' : 'none',
                              }}
                            >
                              <div style={{ fontSize: 11, opacity: 0.9 }}>
                                #{cut.item_id} · {cut.length_mm}mm
                              </div>
                              <div style={{ fontSize: 10 }}>
                                {cut.style} {cut.colour}
                              </div>
                            </Button>
                          ))}
                        </Space>
                      </Card>
                    ))}
                  </Card>
                ))}
              </>
            )}
          </Col>
        </Row>
      </div>
    </>
  )
}