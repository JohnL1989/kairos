/** 展示层格式化工具 */

/** 将 ISO 时间（后端截断的 19 字符或完整）转为友好展示 */
export function formatDate(s: string | undefined): string {
  if (!s) return "—"
  // 后端常返回 "2026-07-09 12:34:56" 或带 T 的 ISO
  const d = new Date(s.includes("T") ? s : s.replace(" ", "T") + "Z")
  if (isNaN(d.getTime())) return s
  return d.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  })
}

/** 热力分 0–1 → 0–100 整数 */
export function heatPercent(heat: number | undefined): number {
  return Math.round((heat ?? 0) * 100)
}

/** 重要性 0–1 → 高/中/低 文案 */
export function importanceLabel(v: number | undefined): { text: string; tone: "ok" | "warn" | "err" | "muted" } {
  const n = v ?? 0
  if (n >= 0.66) return { text: "高", tone: "warn" }
  if (n >= 0.33) return { text: "中", tone: "muted" }
  return { text: "低", tone: "muted" }
}

/** 可靠性 0–1 → 0.92 形式 */
export function reliabilityText(v: number | undefined): string {
  return (v ?? 0).toFixed(2)
}

const TIER_LABELS: Record<string, string> = {
  L1: "L1 · 感知",
  L2: "L2 · 短期",
  L3: "L3 · 工作",
  L4: "L4 · 长期",
}

/** 层级代码 → 友好标签（未知则原样显示） */
export function tierLabel(tier: string | undefined): string {
  if (!tier) return "未知"
  return TIER_LABELS[tier] ?? tier
}

/** scope → 中文 */
export function scopeLabel(scope: string | undefined): string {
  if (scope === "durable") return "持久"
  if (scope === "general") return "普通"
  return scope ?? "—"
}
