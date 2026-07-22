import { useMaturity } from "../lib/queries"
import { ErrorState, EmptyState, SkeletonList } from "../components/States"
import { PageHeader, Card, Bar, Stat, Ring } from "../components/ui"
import { heatPercent } from "../lib/format"

function scoreColor(v: number): string {
  if (v >= 80) return "#14ae5c"
  if (v >= 60) return "#18a0fb"
  if (v >= 40) return "#f2c94c"
  return "#f24822"
}

export default function Maturity() {
  const { data, isLoading, isError, error, refetch } = useMaturity()

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
        <ErrorState message={error instanceof Error ? error.message : "成熟度数据加载失败"} onRetry={() => refetch()} />
      </div>
    )
  }

  if (data.total_memories === 0) {
    return (
      <div className="p-8">
        <PageHeader title="成熟度" subtitle="记忆系统的自我审视与质量评分" />
        <EmptyState title="暂无记忆" subtitle="无法评估空库的成熟度" />
      </div>
    )
  }

  const color = scoreColor(data.maturity_score)
  const tmtTotal = data.tmt_levels.reduce((s, x) => s + x.count, 0) || 1
  const tierTotal = data.tier_distribution.reduce((s, x) => s + x.count, 0) || 1
  const catTotal = data.top_categories.reduce((s, x) => s + x.count, 0) || 1

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <PageHeader title="成熟度" subtitle="记忆系统的自我审视与质量评分" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="items-center justify-center lg:col-span-1">
          <Ring value={data.maturity_score} max={100} color={color} sub="成熟度评分" />
          <p className="text-xs text-ink-4 text-center mt-1">
            向量覆盖 · 持久占比 · 活跃度 · 层级丰富度 综合评分
          </p>
        </Card>

        <div className="lg:col-span-2 grid grid-cols-2 gap-4">
          <Stat label="向量覆盖率" value={`${data.embedding_rate}%`} accent sub={`${data.with_embedding} / ${data.total_memories} 条已向量化`} />
          <Stat label="持久占比" value={`${data.durable_rate}%`} sub={`${data.durable_count} 条 durable`} />
          <Stat label="30 天活跃" value={data.active_30d} sub="近 30 天新写入" />
          <Stat label="平均热值" value={heatPercent(data.avg_heat)} sub="0–100" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="TMT 层级分布">
          <div className="flex flex-col gap-3">
            {data.tmt_levels.map((t) => (
              <Bar key={t.level} label={`L${t.level}`} value={t.count} total={tmtTotal} color="#a855f7" />
            ))}
          </div>
        </Card>

        <Card title="层级（Tier）分布">
          <div className="flex flex-col gap-3">
            {data.tier_distribution.map((t) => (
              <Bar key={t.tier} label={t.tier} value={t.count} total={tierTotal} color="#18a0fb" />
            ))}
          </div>
        </Card>

        <Card title="Top 分类">
          <div className="flex flex-col gap-3">
            {data.top_categories.map((c) => (
              <Bar key={c.category} label={c.category} value={c.count} total={catTotal} color="#14ae5c" />
            ))}
          </div>
        </Card>
      </div>
    </div>
  )
}
