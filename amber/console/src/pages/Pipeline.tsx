import { usePipeline } from "../lib/queries"
import { ErrorState, EmptyState, SkeletonList } from "../components/States"
import { PageHeader, Card, Bar, Stat } from "../components/ui"
import { heatPercent } from "../lib/format"

export default function Pipeline() {
  const { data, isLoading, isError, error, refetch } = usePipeline()

  if (isLoading) {
    return (
      <div className="p-8">
        <SkeletonList rows={5} />
      </div>
    )
  }
  if (isError || !data) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-8">
        <ErrorState message={error instanceof Error ? error.message : "知识流转数据加载失败"} onRetry={() => refetch()} />
      </div>
    )
  }

  const durable = data.scope.find((s) => s.scope_target === "durable")
  const general = data.scope.find((s) => s.scope_target === "general")
  const totalScope = data.scope.reduce((s, x) => s + x.count, 0) || 1
  const totalCat = data.categories.reduce((s, x) => s + x.count, 0) || 1

  if (data.scope.length === 0) {
    return (
      <div className="p-8">
        <PageHeader title="知识流转" subtitle="记忆在作用域与 TMT 层级间的流转" />
        <EmptyState title="暂无流转数据" subtitle="还没有可供分析的记忆" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <PageHeader title="知识流转" subtitle="记忆在作用域与 TMT 层级间的流转" />

      {/* 作用域流转 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-stretch">
        <ScopeNode
          label="普通作用域"
          hint="general · 会话级"
          count={general?.count ?? 0}
          deleted={general?.deleted ?? 0}
          heat={general?.avg_heat ?? 0}
        />
        <div className="hidden lg:flex items-center justify-center text-ink-4 text-2xl">⇄</div>
        <ScopeNode
          label="持久作用域"
          hint="durable · 长期"
          count={durable?.count ?? 0}
          deleted={durable?.deleted ?? 0}
          heat={durable?.avg_heat ?? 0}
          accent
        />
      </div>

      {/* TMT 层级阶梯 */}
      <Card title="TMT 蒸馏层级">
        <div className="flex flex-col gap-4">
          {data.tmt_levels.map((lv) => (
            <div key={lv.level} className="flex flex-col gap-2">
              <div className="flex items-center gap-3">
                <span className="px-2.5 py-1 rounded-md bg-selected text-accent text-xs font-mono font-bold">
                  L{lv.level}
                </span>
                <span className="font-mono text-sm text-ink-2">{lv.count} 条</span>
                <span className="text-xs text-ink-4">均热 {heatPercent(lv.avg_heat)}</span>
              </div>
              {Object.keys(lv.tiers).length > 0 && (
                <div className="flex flex-col gap-1.5 pl-1">
                  {Object.entries(lv.tiers).map(([t, c]) => (
                    <Bar key={t} label={t} value={c} total={lv.count} color="#a855f7" />
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 分类 Top */}
        <Card title="分类分布（Top 10）">
          <div className="flex flex-col gap-3">
            {data.categories.map((c) => (
              <Bar key={c.category} label={c.category} value={c.count} total={totalCat} color="#18a0fb" />
            ))}
          </div>
        </Card>

        {/* 近 7 天趋势 */}
        <Card title={`近 ${data.window_days} 天写入趋势`}>
          {data.trend.length === 0 ? (
            <span className="text-sm text-ink-4">近 7 天无新写入</span>
          ) : (
            <div className="flex items-end gap-2 h-40">
              {data.trend.map((t, i) => {
                const day = t as Record<string, number | string>
                const durable = Number(day.durable ?? 0)
                const general = Number(day.general ?? 0)
                const total = durable + general || 1
                return (
                  <div key={i} className="flex-1 flex flex-col items-center gap-1 h-full justify-end">
                    <div className="w-full flex flex-col-reverse rounded-t overflow-hidden" style={{ height: `${(total / 200) * 100}%` }} title={`${day.day} · 持久 ${durable} / 普通 ${general}`}>
                      <div className="bg-accent" style={{ height: `${(general / total) * 100}%` }} />
                      <div className="bg-ok" style={{ height: `${(durable / total) * 100}%` }} />
                    </div>
                    <span className="text-[9px] text-ink-4 font-mono">{(day.day as string).slice(5)}</span>
                  </div>
                )
              })}
            </div>
          )}
          <div className="flex items-center gap-4 mt-2 text-xs text-ink-4">
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-ok" />持久</span>
            <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-sm bg-accent" />普通</span>
          </div>
        </Card>
      </div>
    </div>
  )
}

function ScopeNode({
  label,
  hint,
  count,
  deleted,
  heat,
  accent,
}: {
  label: string
  hint: string
  count: number
  deleted: number
  heat: number
  accent?: boolean
}) {
  return (
    <div className={`rounded-2xl border p-5 flex flex-col gap-3 ${accent ? "border-accent/40 bg-selected/30" : "border-line bg-card"}`}>
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-ink">{label}</span>
        <span className="text-[10px] text-ink-4 font-mono uppercase">{hint}</span>
      </div>
      <span className="text-4xl font-bold font-mono text-ink">{count}</span>
      <div className="flex gap-6 text-sm">
        <div className="flex flex-col">
          <span className="text-ink-4 text-xs">已删除</span>
          <span className="font-mono text-ink-2">{deleted}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-ink-4 text-xs">均热</span>
          <span className="font-mono text-ink-2">{heatPercent(heat)}</span>
        </div>
      </div>
    </div>
  )
}
