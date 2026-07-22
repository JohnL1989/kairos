import { useNavigate } from "react-router-dom"
import { useStats } from "../lib/queries"
import { ErrorState, EmptyState, SkeletonList } from "../components/States"
import { PageHeader, Card, Bar, Stat } from "../components/ui"

export default function Categories() {
  const { data, isLoading, isError, error, refetch } = useStats()
  const navigate = useNavigate()

  if (isLoading) {
    return (
      <div className="p-8">
        <SkeletonList rows={4} />
      </div>
    )
  }
  if (isError || !data) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-8">
        <ErrorState message={error instanceof Error ? error.message : "分类加载失败"} onRetry={() => refetch()} />
      </div>
    )
  }

  const cats = Object.entries(data.by_category).sort((a, b) => b[1] - a[1])
  const total = data.memories.total || 1
  const top = cats[0]

  if (cats.length === 0) {
    return (
      <div className="p-8">
        <PageHeader title="分类管理" subtitle="记忆按业务分类的分布与占比" />
        <EmptyState title="暂无分类" subtitle="还没有任何带分类的记忆" />
      </div>
    )
  }

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <PageHeader title="分类管理" subtitle="记忆按业务分类的分布与占比" />

      <div className="grid grid-cols-3 gap-4">
        <Stat label="分类总数" value={cats.length} accent />
        <Stat label="记忆总量" value={data.memories.total} />
        <Stat label="最大分类" value={top[0]} sub={`${top[1]} 条 · ${Math.round((top[1] / total) * 100)}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="分类占比">
          <div className="flex flex-col gap-3">
            {cats.map(([name, count]) => (
              <Bar key={name} label={name} value={count} total={total} color="#18a0fb" />
            ))}
          </div>
        </Card>

        <Card title="分类卡片">
          <div className="grid grid-cols-2 gap-3">
            {cats.map(([name, count]) => {
              const pct = Math.round((count / total) * 100)
              return (
                <button
                  key={name}
                  onClick={() => navigate(`/memories?category=${encodeURIComponent(name)}`)}
                  className="text-left bg-panel border border-line rounded-xl p-4 flex flex-col gap-2 hover:border-accent/50 transition-colors"
                >
                  <span className="text-sm font-medium text-ink truncate">{name}</span>
                  <span className="text-2xl font-bold font-mono text-accent">{count}</span>
                  <span className="text-xs text-ink-4">占比 {pct}%</span>
                </button>
              )
            })}
          </div>
        </Card>
      </div>
    </div>
  )
}
