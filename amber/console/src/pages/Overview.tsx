import { useNavigate } from "react-router-dom"
import { useStats } from "../lib/queries"
import { SkeletonList } from "../components/States"

function Bar({ label, value, total, color }: { label: string; value: number; total: number; color: string }) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 shrink-0 text-xs text-ink-3 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-line overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-10 text-right font-mono text-xs text-ink-2">{value}</span>
    </div>
  )
}

export default function Overview() {
  const { data, isLoading, isError } = useStats()
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
        <div className="w-20 h-20 rounded-2xl bg-errbg flex items-center justify-center mb-5">
          <span className="text-3xl font-bold text-err">!</span>
        </div>
        <h2 className="text-xl font-bold text-ink">统计加载失败</h2>
        <p className="text-sm text-ink-3 mt-2">请确认后端服务已启动且可访问 /api/v1/console/stats</p>
        <button
          onClick={() => navigate("/memories")}
          className="mt-5 h-9 px-5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-[#0f8fe0] transition-colors"
        >
          前往记忆浏览
        </button>
      </div>
    )
  }

  const m = data.memories
  const total = m.total || 1
  const tierColors: Record<string, string> = {
    L1: "#18a0fb",
    L2: "#14ae5c",
    L3: "#f2c94c",
    L4: "#a855f7",
  }
  const topCategories = Object.entries(data.by_category)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 8)

  return (
    <div className="p-8 max-w-[1100px] mx-auto flex flex-col gap-6">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">概览</h1>
          <p className="text-sm text-ink-3 mt-1">Hermes 记忆系统的整体态势</p>
        </div>
        <button
          onClick={() => navigate("/memories")}
          className="h-10 px-5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-[#0f8fe0] transition-colors"
        >
          进入记忆浏览 →
        </button>
      </div>

      {/* 指标卡 */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="记忆总量" value={m.total} accent />
        <StatCard label="今日新增" value={m.today_new} />
        <StatCard label="信念" value={data.beliefs.total} />
        <StatCard label="知识页" value={data.wiki_pages.total} />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* 层级分布 */}
        <div className="bg-card border border-line rounded-2xl p-5 flex flex-col gap-4">
          <h3 className="text-sm font-medium text-ink-3">层级分布</h3>
          <div className="flex flex-col gap-3">
            {Object.entries(m.tier).length === 0 && (
              <span className="text-sm text-ink-4">暂无数据</span>
            )}
            {Object.entries(m.tier).map(([k, v]) => (
              <Bar key={k} label={k} value={v} total={total} color={tierColors[k] ?? "#18a0fb"} />
            ))}
          </div>
        </div>

        {/* 分类分布 */}
        <div className="bg-card border border-line rounded-2xl p-5 flex flex-col gap-4">
          <h3 className="text-sm font-medium text-ink-3">分类分布（Top 8）</h3>
          <div className="flex flex-col gap-3">
            {topCategories.length === 0 && <span className="text-sm text-ink-4">暂无数据</span>}
            {topCategories.map(([k, v]) => (
              <Bar key={k} label={k} value={v} total={total} color="#18a0fb" />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  return (
    <div className="bg-card border border-line rounded-2xl p-5 flex flex-col gap-1">
      <span className="text-xs text-ink-3">{label}</span>
      <span className={`text-3xl font-bold font-mono ${accent ? "text-accent" : "text-ink"}`}>
        {value}
      </span>
    </div>
  )
}
