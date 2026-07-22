import type { MemorySummary } from "../types"
import { formatDate, heatPercent, tierLabel } from "../lib/format"

interface MemoryListProps {
  memories: MemorySummary[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export default function MemoryList({ memories, selectedId, onSelect }: MemoryListProps) {
  return (
    <div className="flex flex-col gap-2 p-3">
      {memories.map((m) => {
        const active = m.id === selectedId
        return (
          <button
            key={m.id}
            onClick={() => onSelect(m.id)}
            className={`text-left rounded-lg border px-4 py-3 transition-colors ${
              active
                ? "bg-selected border-accent/60"
                : "bg-card border-line hover:border-[#33333a] hover:bg-[#17171b]"
            }`}
          >
            <div className="flex items-start justify-between gap-3">
              <p className="text-sm text-ink font-medium leading-snug line-clamp-2">
                {m.content}
              </p>
              <span
                className="shrink-0 mt-0.5 font-mono text-xs font-bold"
                style={{ color: heatColor(heatPercent(m.heat)) }}
                title={`热力分 ${heatPercent(m.heat)}`}
              >
                {heatPercent(m.heat)}
              </span>
            </div>
            <div className="flex items-center gap-2 mt-2.5 text-xs text-ink-3">
              <span className="px-2 py-0.5 rounded bg-selected text-accent font-medium">
                {tierLabel(m.tier)}
              </span>
              <span className="px-2 py-0.5 rounded bg-line text-ink-3">{m.category}</span>
              <span className="ml-auto font-mono">{formatDate(m.created)}</span>
            </div>
          </button>
        )
      })}
    </div>
  )
}

function heatColor(h: number): string {
  if (h >= 70) return "#18a0fb"
  if (h >= 40) return "#14ae5c"
  if (h >= 20) return "#f2c94c"
  return "#9ca3af"
}
