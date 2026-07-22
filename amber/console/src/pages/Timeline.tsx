import { useNavigate } from "react-router-dom"
import { useTrends, useEvents } from "../lib/queries"
import { ErrorState, EmptyState, SkeletonList } from "../components/States"
import { PageHeader, Card, Bar, Stat } from "../components/ui"
import { formatDate } from "../lib/format"

const ACTION_TONE: Record<string, string> = {
  create: "text-ok bg-ok/10",
  delete: "text-err bg-err/10",
  update: "text-warn bg-warn/10",
  search: "text-accent bg-accent/10",
}
function actionTone(a: string) {
  return ACTION_TONE[a] ?? "text-ink-3 bg-line"
}

export default function Timeline() {
  const { data: trends, isLoading: lt, isError: et, error: errT, refetch: rfT } = useTrends()
  const { data: events, isLoading: le, isError: ee, refetch: rfE } = useEvents(30)
  const navigate = useNavigate()

  const isLoading = lt || le
  const isError = et || ee
  const refetch = () => {
    rfT()
    rfE()
  }

  if (isLoading) {
    return (
      <div className="p-8">
        <SkeletonList rows={5} />
      </div>
    )
  }

  if (isError) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-8">
        <ErrorState
          message={errT instanceof Error ? errT.message : ee ? "事件流加载失败" : "加载失败"}
          onRetry={refetch}
        />
      </div>
    )
  }

  const daily = trends?.daily ?? []
  const hourly = trends?.hourly_today ?? []
  const maxDaily = Math.max(1, ...daily.map((d) => d.memories_created))
  const weekTotal = daily.reduce((s, d) => s + d.memories_created, 0)
  const todayTotal = hourly.reduce((s, h) => s + h.count, 0)
  const maxHourly = Math.max(1, ...hourly.map((h) => h.count))
  const evs = events?.events ?? []

  if (daily.length === 0 && evs.length === 0) {
    return (
      <div className="p-8">
        <PageHeader title="时间线" subtitle="记忆写入活跃度与最近操作" />
        <EmptyState title="暂无时间线数据" subtitle="还没有记忆写入记录或操作事件" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <PageHeader title="时间线" subtitle="记忆写入活跃度与最近操作" />

      <div className="grid grid-cols-3 gap-4">
        <Stat label="近 7 天新增" value={weekTotal} accent />
        <Stat label="今日新增" value={todayTotal} sub={`${hourly.length} 个活跃小时`} />
        <Stat label="最近操作" value={evs.length} sub="操作事件" />
      </div>

      {/* 每日新增柱状 */}
      <Card title="近 7 天每日新增">
        <div className="flex items-end justify-between gap-3 h-44">
          {daily.map((d) => (
            <div key={d.date} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
              <span className="font-mono text-xs text-ink-3">{d.memories_created}</span>
              <div
                className="w-full rounded-t-md bg-gradient-to-t from-accent/30 to-accent"
                style={{ height: `${(d.memories_created / maxDaily) * 100}%` }}
                title={`${d.date}: ${d.memories_created}`}
              />
              <span className="text-[10px] text-ink-4 font-mono">
                {d.date.slice(5)}
              </span>
            </div>
          ))}
        </div>
      </Card>

      {/* 今日按小时 */}
      <Card title="今日按小时活跃">
        {hourly.length === 0 ? (
          <span className="text-sm text-ink-4">今日暂无写入</span>
        ) : (
          <div className="flex items-end gap-1.5 h-32">
            {hourly.map((h) => (
              <div key={h.hour} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                <div
                  className="w-full rounded-t bg-accent/50 hover:bg-accent transition-colors"
                  style={{ height: `${(h.count / maxHourly) * 100}%` }}
                  title={`${h.hour}:00 — ${h.count}`}
                />
                <span className="text-[9px] text-ink-4 font-mono">{h.hour}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* 最近操作事件流 */}
      <Card title="最近操作" action={<span className="text-xs text-ink-4">来自 memory_traces</span>}>
        {evs.length === 0 ? (
          <span className="text-sm text-ink-4">暂无操作事件</span>
        ) : (
          <div className="flex flex-col">
            {evs.map((e) => (
              <button
                key={e.id}
                onClick={() => e.memory_id && navigate("/memories")}
                className="flex items-center gap-3 py-3 px-2 -mx-2 rounded-lg hover:bg-white/[0.03] transition-colors text-left"
              >
                <span
                  className={`px-2 py-0.5 rounded text-[11px] font-medium font-mono uppercase ${actionTone(e.action)}`}
                >
                  {e.action}
                </span>
                <span className="flex-1 min-w-0 text-sm text-ink-2 truncate">
                  {e.preview || "（无预览）"}
                </span>
                <span className="text-xs text-ink-4 font-mono shrink-0">
                  {e.executed_at ? formatDate(e.executed_at.replace("T", " ").slice(0, 19)) : "—"}
                </span>
              </button>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
