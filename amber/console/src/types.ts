/** 记忆系统前端类型定义（对齐后端真实响应） */

/** 列表/搜索返回的精简记忆对象 */
export interface MemorySummary {
  id: number
  /** 内容，后端已截断（列表 200 字 / 搜索 300 字） */
  content: string
  category: string
  /** 层级代码，如 L1 / L2 … */
  tier: string
  /** 热力分 0–1 */
  heat: number
  /** 创建时间（已截断为 19 字符） */
  created: string
  /** durable | general */
  scope: string
}

/** 单条记忆完整详情 */
export interface MemoryDetail {
  id: number
  content: string
  category: string
  tier: string
  /** 热力分 0–1 */
  heat: number
  /** 可靠性 0–1 */
  reliability: number
  /** TMT 成熟度等级（整数） */
  tmt_level: number
  /** 重要性 0–1 */
  importance: number
  /** 实体标签列表 */
  entities: string[]
  access_count: number
  scope: string
  created: string
  updated: string
}

export interface MemoryListResponse {
  memories: MemorySummary[]
}

export interface SearchResponse {
  memories: MemorySummary[]
}

/** 概览统计（/api/v1/console/stats — 当前后端嵌套结构） */
export interface StatsResponse {
  memories: {
    total: number
    today_new: number
    scope: Record<string, number>
    tier: Record<string, number>
  }
  beliefs: { total: number; today_new: number }
  wiki_pages: { total: number; today_new: number }
  total_traces: number
  by_category: Record<string, number>
}

/** 列表筛选参数 */
export interface MemoryQuery {
  tier?: string
  category?: string
  limit?: number
}

/* ── 时间线 / 趋势（/api/v1/console/trends） ── */
export interface TrendPoint {
  date: string
  memories_created: number
}
export interface TrendsResponse {
  daily: TrendPoint[]
  hourly_today: { hour: number; count: number }[]
  labels: string[]
  values: number[]
  window_days: number
}

/* ── 事件流（/api/v1/console/events） ── */
export interface TraceEvent {
  id: number
  action: string
  memory_id: number | null
  preview: string
  executed_at: string | null
}
export interface EventsResponse {
  events: TraceEvent[]
  count: number
}

/* ── 服务健康（/api/v1/console/services） ── */
export type ServiceStatus = "up" | "degraded" | "down"
export interface ServiceInfo {
  name: string
  kind: string
  status: ServiceStatus
  latency_ms: number | null
  last_check: string
  error?: string
}
export interface ServicesResponse {
  services: ServiceInfo[]
  overall: ServiceStatus
}

/* ── 知识流转（/api/v1/console/pipeline） ── */
export interface PipelineScope {
  scope_target: string
  count: number
  deleted: number
  avg_heat: number
}
export interface PipelineTmtLevel {
  level: number
  count: number
  avg_heat: number
  tiers: Record<string, number>
}
export interface PipelineResponse {
  scope: PipelineScope[]
  tmt_levels: PipelineTmtLevel[]
  categories: { category: string; count: number }[]
  trend: Record<string, number | string>[]
  window_days: number
  generated_at: string
}

/* ── 成熟度（/api/v1/console/maturity） ── */
export interface MaturityResponse {
  maturity_score: number
  total_memories: number
  with_embedding: number
  embedding_rate: number
  durable_count: number
  durable_rate: number
  general_count: number
  active_30d: number
  avg_heat: number
  tmt_levels: { level: number; count: number }[]
  tier_distribution: { tier: string; count: number }[]
  top_categories: { category: string; count: number }[]
  generated_at: string
}

/* ── 健康时间线（/api/v1/console/health-history） ── */
export interface HealthTimelinePoint {
  time: string | null
  service: string
  status: ServiceStatus
  avg_latency_ms: number | null
  checks: number
}
export interface HealthHistoryResponse {
  timeline: HealthTimelinePoint[]
  summary: {
    uptime_24h: number
    outages: number
    longest_outage_min: number
  }
}

/* ── 新建 / 编辑记忆 ── */
export interface MemoryCreatePayload {
  content: string
  category?: string
  scope_target?: "durable" | "general"
  tier?: string
  importance?: number
  reliability?: number
}
export interface MemoryUpdatePayload {
  content?: string
  category?: string
  tier?: string
  importance?: number
  reliability?: number
}
