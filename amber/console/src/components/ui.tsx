import type { ReactNode } from "react"

/** 页面统一标题区 */
export function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: ReactNode
}) {
  return (
    <div className="flex items-end justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-ink tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-ink-3 mt-1">{subtitle}</p>}
      </div>
      {action}
    </div>
  )
}

/** 卡片容器 */
export function Card({
  title,
  action,
  children,
  className = "",
}: {
  title?: string
  action?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <div className={`bg-card border border-line rounded-2xl p-5 flex flex-col gap-4 ${className}`}>
      {(title || action) && (
        <div className="flex items-center justify-between">
          {title && <h3 className="text-sm font-medium text-ink-3">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  )
}

/** 横向比例条 */
export function Bar({
  label,
  value,
  total,
  color = "#18a0fb",
}: {
  label: string
  value: number
  total: number
  color?: string
}) {
  const pct = total > 0 ? Math.round((value / total) * 100) : 0
  return (
    <div className="flex items-center gap-3">
      <span className="w-28 shrink-0 text-xs text-ink-3 truncate">{label}</span>
      <div className="flex-1 h-2 rounded-full bg-line overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, background: color }} />
      </div>
      <span className="w-12 text-right font-mono text-xs text-ink-2">{value}</span>
    </div>
  )
}

/** 指标卡 */
export function Stat({
  label,
  value,
  accent,
  sub,
}: {
  label: string
  value: ReactNode
  accent?: boolean
  sub?: string
}) {
  return (
    <div className="bg-card border border-line rounded-2xl p-5 flex flex-col gap-1">
      <span className="text-xs text-ink-3">{label}</span>
      <span className={`text-3xl font-bold font-mono ${accent ? "text-accent" : "text-ink"}`}>
        {value}
      </span>
      {sub && <span className="text-xs text-ink-4">{sub}</span>}
    </div>
  )
}

/** 状态色点 */
const STATUS_COLOR: Record<string, string> = {
  up: "#14ae5c",
  healthy: "#14ae5c",
  degraded: "#f2c94c",
  down: "#f24822",
  unreachable: "#f24822",
}
export function StatusDot({ status }: { status: string }) {
  const c = STATUS_COLOR[status] ?? "#6b7280"
  return (
    <span
      className="inline-block w-2.5 h-2.5 rounded-full shrink-0"
      style={{ background: c, boxShadow: `0 0 0 3px ${c}22` }}
    />
  )
}

/** 状态徽章文字色 */
export function statusTextClass(status: string): string {
  if (status === "up" || status === "healthy") return "text-ok"
  if (status === "degraded") return "text-warn"
  if (status === "down" || status === "unreachable") return "text-err"
  return "text-ink-3"
}

/** 进度环（用于成熟度评分等 0–100 指标） */
export function Ring({
  value,
  max = 100,
  size = 132,
  stroke = 12,
  color = "#18a0fb",
  label,
  sub,
}: {
  value: number
  max?: number
  size?: number
  stroke?: number
  color?: string
  label?: string
  sub?: string
}) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const pct = max > 0 ? Math.max(0, Math.min(1, value / max)) : 0
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#232327" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-3xl font-bold font-mono text-ink">{label ?? Math.round(value)}</span>
        {sub && <span className="text-xs text-ink-4 mt-0.5">{sub}</span>}
      </div>
    </div>
  )
}
