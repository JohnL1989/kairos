import { NavLink } from "react-router-dom"
import { useStats } from "../lib/queries"
import { useMemoryForm } from "./MemoryForm"

const NAV = [
  { to: "/", label: "概览", end: true, icon: "◎" },
  { to: "/memories", label: "记忆浏览", end: false, icon: "❒" },
  { to: "/timeline", label: "时间线", end: false, icon: "⟜" },
  { to: "/categories", label: "分类管理", end: false, icon: "▤" },
  { to: "/pipeline", label: "知识流转", end: false, icon: "⇄" },
  { to: "/maturity", label: "成熟度", end: false, icon: "◈" },
  { to: "/health", label: "系统健康", end: false, icon: "✓" },
]

export default function Sidebar() {
  const { data: stats } = useStats()
  const form = useMemoryForm()

  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 bg-panel border-r border-line flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center gap-2.5 px-5 border-b border-line">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent to-indigo-600 flex items-center justify-center text-white text-sm font-bold shadow-lg shadow-accent/30">
          H
        </div>
        <div className="leading-none">
          <div className="text-sm font-bold text-ink tracking-tight">Hermes 记忆</div>
          <div className="text-[10px] text-ink-4 tracking-[0.2em] mt-1">CONSOLE</div>
        </div>
      </div>

      {/* 导航 */}
      <nav className="flex-1 px-3 py-4 flex flex-col gap-1 overflow-y-auto no-scrollbar">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 h-9 rounded-lg text-sm transition-colors ${
                isActive
                  ? "bg-selected text-accent font-medium"
                  : "text-ink-3 hover:text-ink hover:bg-white/[0.03]"
              }`
            }
          >
            <span className="w-4 text-center text-base opacity-80">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* 底部统计 */}
      <div className="px-4 py-4 border-t border-line flex flex-col gap-3">
        <button
          onClick={() => form.openCreate()}
          className="h-9 rounded-lg bg-accent text-white text-sm font-medium hover:bg-[#0f8fe0] transition-colors"
        >
          + 新建记忆
        </button>
        <div className="rounded-lg bg-card border border-line px-3 py-2.5 flex items-center justify-between">
          <span className="text-xs text-ink-3">记忆总量</span>
          <span className="text-sm font-mono font-bold text-ink">
            {stats ? stats.memories.total : "—"}
          </span>
        </div>
      </div>
    </aside>
  )
}
