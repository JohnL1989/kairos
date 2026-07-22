import { useServices, useHealthHistory } from "../lib/queries"
import { ErrorState, SkeletonList } from "../components/States"
import { PageHeader, Card, Stat, StatusDot, statusTextClass } from "../components/ui"
import { formatDate } from "../lib/format"

export default function Health() {
  const svc = useServices()
  const hist = useHealthHistory(24)

  if (svc.isLoading || hist.isLoading) {
    return (
      <div className="p-8">
        <SkeletonList rows={4} />
      </div>
    )
  }
  if (svc.isError || !svc.data) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-8">
        <ErrorState
          message={svc.error instanceof Error ? svc.error.message : "服务状态加载失败"}
          onRetry={() => svc.refetch()}
        />
      </div>
    )
  }

  const overall = svc.data.overall
  const overallColor =
    overall === "up" ? "#14ae5c" : overall === "degraded" ? "#f2c94c" : "#f24822"
  const summary = hist.data?.summary
  const timeline = hist.data?.timeline ?? []

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <PageHeader title="系统健康" subtitle="依赖服务存活与 24h 可用性" />

      {/* 总体状态 */}
      <div
        className="rounded-2xl border p-6 flex items-center gap-4"
        style={{ borderColor: `${overallColor}55`, background: `${overallColor}12` }}
      >
        <StatusDot status={overall} />
        <div>
          <div className="text-xl font-bold capitalize" style={{ color: overallColor }}>
            {overall === "up" ? "运行正常" : overall === "degraded" ? "部分降级" : "服务异常"}
          </div>
          <div className="text-sm text-ink-3 mt-0.5">
            探测到 {svc.data.services.length} 个依赖服务
          </div>
        </div>
      </div>

      {/* 24h 摘要 */}
      <div className="grid grid-cols-3 gap-4">
        <Stat
          label="24h 可用性"
          value={summary ? `${summary.uptime_24h}%` : "—"}
          accent={summary ? summary.uptime_24h >= 99 : false}
        />
        <Stat label="中断次数" value={summary ? summary.outages : "—"} sub={summary && summary.outages > 0 ? "过去 24 小时" : "无中断"} />
        <Stat label="最长中断" value={summary ? `${summary.longest_outage_min}m` : "—"} />
      </div>

      {/* 服务卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {svc.data.services.map((s) => (
          <div key={s.name} className="bg-card border border-line rounded-2xl p-5 flex flex-col gap-3">
            <div className="flex items-center gap-2.5">
              <StatusDot status={s.status} />
              <span className="text-sm font-medium text-ink flex-1 truncate">{s.name}</span>
              <span className={`text-xs font-medium capitalize ${statusTextClass(s.status)}`}>{s.status}</span>
            </div>
            <div className="flex items-center justify-between text-xs text-ink-4">
              <span className="font-mono uppercase">{s.kind}</span>
              <span className="font-mono">
                {s.latency_ms != null ? `${Math.round(s.latency_ms)} ms` : "—"}
              </span>
            </div>
            {s.error && <p className="text-xs text-err/80 font-mono break-all">{s.error}</p>}
          </div>
        ))}
      </div>

      {/* 健康时间线 */}
      <Card title="24h 健康时间线">
        {timeline.length === 0 ? (
          <span className="text-sm text-ink-4">暂无健康检查记录</span>
        ) : (
          <div className="flex flex-col max-h-80 overflow-y-auto no-scrollbar">
            {timeline.map((p, i) => (
              <div key={i} className="flex items-center gap-3 py-2.5 border-b border-line/60 last:border-0">
                <StatusDot status={p.status} />
                <span className="w-32 shrink-0 text-sm text-ink-2 font-mono">{p.service}</span>
                <span className="flex-1 text-xs text-ink-4">
                  {p.time ? formatDate(p.time.replace("T", " ").slice(0, 19)) : "—"}
                </span>
                <span className="text-xs font-mono text-ink-3">
                  {p.avg_latency_ms != null ? `${Math.round(p.avg_latency_ms)}ms` : "—"}
                </span>
                <span className={`text-xs capitalize w-20 text-right ${statusTextClass(p.status)}`}>{p.status}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
