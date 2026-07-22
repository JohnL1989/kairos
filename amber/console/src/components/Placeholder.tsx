import { useLocation, useNavigate } from "react-router-dom"

export default function Placeholder() {
  const { pathname } = useLocation()
  const navigate = useNavigate()
  const name = pathname.replace("/", "") || "页面"

  return (
    <div className="h-full flex flex-col items-center justify-center text-center px-8">
      <div className="w-20 h-20 rounded-2xl bg-card border border-line flex items-center justify-center mb-5">
        <span className="text-3xl text-ink-4">⚙</span>
      </div>
      <h2 className="text-xl font-bold text-ink capitalize">{name} · 建设中</h2>
      <p className="text-sm text-ink-3 mt-2 max-w-sm">
        该模块属于后续阶段。当前 Phase 1 已交付「记忆浏览 + Inspector」，可前往体验。
      </p>
      <button
        onClick={() => navigate("/memories")}
        className="mt-5 h-9 px-5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-[#0f8fe0] transition-colors"
      >
        前往记忆浏览
      </button>
    </div>
  )
}
