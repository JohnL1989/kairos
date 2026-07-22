import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { deleteJson, getJson, postJson, putJson } from "./api"
import type {
  EventsResponse,
  HealthHistoryResponse,
  MaturityResponse,
  MemoryCreatePayload,
  MemoryDetail,
  MemoryListResponse,
  MemoryQuery,
  MemoryUpdatePayload,
  PipelineResponse,
  SearchResponse,
  ServicesResponse,
  StatsResponse,
  TrendsResponse,
} from "../types"

/** 记忆列表（支持 tier / category / limit 过滤） */
export function useMemories(query: MemoryQuery) {
  return useQuery({
    queryKey: ["memories", query],
    queryFn: () =>
      getJson<MemoryListResponse>("/memories", {
        tier: query.tier,
        category: query.category,
        limit: query.limit ?? 20,
      }),
    staleTime: 15_000,
  })
}

/** 语义 / 全文搜索 */
export function useSearch(query: string, topK = 30) {
  return useQuery({
    queryKey: ["search", query],
    queryFn: () =>
      postJson<SearchResponse>("/memories/search", { query, top_k: topK }),
    enabled: query.trim().length > 2,
    staleTime: 15_000,
  })
}

/** 单条记忆详情 */
export function useMemory(id: number | null) {
  return useQuery({
    queryKey: ["memory", id],
    queryFn: () => getJson<MemoryDetail>(`/memories/${id}`),
    enabled: id != null,
    staleTime: 15_000,
  })
}

/** 概览统计 */
export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => getJson<StatsResponse>("/console/stats"),
    staleTime: 30_000,
  })
}

/** 趋势（时间线页） */
export function useTrends() {
  return useQuery({
    queryKey: ["trends"],
    queryFn: () => getJson<TrendsResponse>("/console/trends"),
    staleTime: 60_000,
  })
}

/** 事件流（时间线页） */
export function useEvents(limit = 30) {
  return useQuery({
    queryKey: ["events", limit],
    queryFn: () => getJson<EventsResponse>("/console/events", { limit }),
    staleTime: 15_000,
  })
}

/** 服务健康（系统健康页） */
export function useServices() {
  return useQuery({
    queryKey: ["services"],
    queryFn: () => getJson<ServicesResponse>("/console/services"),
    staleTime: 15_000,
    refetchInterval: 30_000,
  })
}

/** 健康时间线（系统健康页） */
export function useHealthHistory(hours = 24) {
  return useQuery({
    queryKey: ["health-history", hours],
    queryFn: () => getJson<HealthHistoryResponse>("/console/health-history", { hours }),
    staleTime: 60_000,
  })
}

/** 知识流转（知识流转页） */
export function usePipeline() {
  return useQuery({
    queryKey: ["pipeline"],
    queryFn: () => getJson<PipelineResponse>("/console/pipeline"),
    staleTime: 30_000,
  })
}

/** 成熟度（成熟度页） */
export function useMaturity() {
  return useQuery({
    queryKey: ["maturity"],
    queryFn: () => getJson<MaturityResponse>("/console/maturity"),
    staleTime: 30_000,
  })
}

/** 删除记忆（软删除） */
export function useDeleteMemory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => deleteJson<{ status: string; id: number }>(`/memories/${id}`),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memories"] })
      qc.invalidateQueries({ queryKey: ["stats"] })
    },
  })
}

/** 新建记忆 */
export function useCreateMemory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (payload: MemoryCreatePayload) =>
      postJson<{ id: number; created: string; scope: string }>("/memories", payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["memories"] })
      qc.invalidateQueries({ queryKey: ["stats"] })
    },
  })
}

/** 更新记忆（编辑） */
export function useUpdateMemory() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: MemoryUpdatePayload }) =>
      putJson<{ status: string; id: number }>(`/memories/${id}`, payload),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: ["memory", vars.id] })
      qc.invalidateQueries({ queryKey: ["memories"] })
      qc.invalidateQueries({ queryKey: ["stats"] })
    },
  })
}
