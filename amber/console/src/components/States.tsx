import type { ReactNode } from "react"

/** 列表骨架屏行 */
export function SkeletonList({ rows = 6 }: { rows?: number }) {
  return (
    <div className="flex flex-col gap-2 p-3">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-[88px] rounded-lg bg-skeleton animate-pulse" />
      ))}
    </div>
  )
}

/** 错误态 */
export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12">
      <div className="w-24 h-24 rounded-full bg-errbg flex items-center justify-center mb-5">
        <span className="text-3xl font-bold text-err">!</span>
      </div>
      <h3 className="text-lg font-bold text-ink">加载失败</h3>
      <p className="text-sm text-ink-3 mt-2 max-w-xs">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-5 h-9 px-5 rounded-lg bg-err text-white text-sm font-medium hover:bg-[#d63c1c] transition-colors"
        >
          重新加载
        </button>
      )}
    </div>
  )
}

/** 空态 */
export function EmptyState({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6 py-12">
      <div className="w-24 h-24 rounded-full bg-panel flex items-center justify-center mb-5">
        <span className="text-3xl text-ink-4">∅</span>
      </div>
      <h3 className="text-lg font-bold text-ink">{title}</h3>
      <p className="text-sm text-ink-3 mt-2 max-w-xs">{subtitle}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
