import { useState } from "react"
import { useMemory, useDeleteMemory } from "../lib/queries"
import { useToast } from "./Toast"
import { useMemoryForm } from "./MemoryForm"
import ConfirmDialog from "./ConfirmDialog"
import { ErrorState } from "./States"
import {
  formatDate,
  heatPercent,
  importanceLabel,
  reliabilityText,
  scopeLabel,
  tierLabel,
} from "../lib/format"

const TONE_TEXT: Record<string, string> = {
  ok: "text-ok",
  warn: "text-warn",
  err: "text-err",
  muted: "text-ink-3",
}

export default function MemoryInspector({
  memoryId,
  onDeleted,
  onClose,
}: {
  memoryId: number | null
  onDeleted: () => void
  onClose: () => void
}) {
  const { data, isLoading, isError, error, refetch } = useMemory(memoryId)
  const del = useDeleteMemory()
  const toast = useToast()
  const form = useMemoryForm()
  const [confirmOpen, setConfirmOpen] = useState(false)

  if (!memoryId) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center px-8">
        <div className="w-16 h-16 rounded-2xl bg-panel flex items-center justify-center mb-4">
          <span className="text-2xl text-ink-4">❒</span>
        </div>
        <p className="text-sm text-ink-3">从左侧选择一条记忆查看详情</p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="p-5 flex flex-col gap-4">
        <div className="h-6 w-2/3 rounded bg-skeleton animate-pulse" />
        <div className="h-24 rounded-lg bg-skeleton animate-pulse" />
        <div className="grid grid-cols-2 gap-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-[58px] rounded-lg bg-skeleton animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <ErrorState
        message={error instanceof Error ? error.message : "记忆详情加载失败"}
        onRetry={() => refetch()}
      />
    )
  }

  const imp = importanceLabel(data.importance)

  const handleDelete = async () => {
    try {
      await del.mutateAsync(data.id)
      toast.push("ok", "删除成功", `记忆 #${data.id} 已软删除`)
      setConfirmOpen(false)
      onDeleted()
    } catch (e) {
      toast.push("err", "删除失败", e instanceof Error ? e.message : "请稍后重试")
      setConfirmOpen(false)
    }
  }

  return (
    <div className="h-full flex flex-col">
      {/* 顶栏操作 */}
      <div className="h-14 shrink-0 flex items-center justify-between px-5 border-b border-line">
        <span className="text-xs text-ink-3 font-mono">#{data.id}</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => data && form.openEdit(data)}
            className="h-8 px-3 rounded-lg bg-card border border-line text-sm text-ink hover:bg-[#17171b] transition-colors"
          >
            编辑
          </button>
          <button
            onClick={() => toast.push("warn", "功能建设中", "导出将在后续阶段开放")}
            className="h-8 px-3 rounded-lg bg-card border border-line text-sm text-ink hover:bg-[#17171b] transition-colors"
          >
            导出
          </button>
          <button
            onClick={() => setConfirmOpen(true)}
            className="h-8 px-3 rounded-lg bg-errbg text-err text-sm font-medium hover:bg-[#3a2222] transition-colors"
          >
            删除
          </button>
          <button
            onClick={onClose}
            className="h-8 w-8 rounded-lg bg-card border border-line text-ink-3 hover:text-ink transition-colors text-base"
            title="关闭"
          >
            ✕
          </button>
        </div>
      </div>

      {/* 内容区 */}
      <div className="flex-1 overflow-y-auto px-5 py-5 flex flex-col gap-6">
        {/* 标题 + 徽章 */}
        <div className="flex flex-col gap-3">
          <h2 className="text-xl font-bold text-ink leading-snug">
            {data.content.slice(0, 60)}
            {data.content.length > 60 ? "…" : ""}
          </h2>
          <div className="flex flex-wrap items-center gap-2">
            <span className="px-2.5 py-1 rounded-md bg-selected text-accent text-xs font-medium">
              {tierLabel(data.tier)}
            </span>
            <span className="px-2.5 py-1 rounded-md bg-line text-ink-3 text-xs">
              {data.category}
            </span>
            <span className="px-2.5 py-1 rounded-md bg-line text-ink-3 text-xs font-mono">
              {scopeLabel(data.scope)}
            </span>
          </div>
        </div>

        {/* 正文 */}
        <p className="text-sm text-ink-2 leading-relaxed whitespace-pre-wrap">{data.content}</p>

        {/* 指标卡 */}
        <div className="grid grid-cols-2 gap-3">
          <Metric label="热力分" value={`${heatPercent(data.heat)}`} accent />
          <Metric label="TMT 成熟度" value={`L${data.tmt_level}`} tone="ok" />
          <Metric label="可靠性" value={reliabilityText(data.reliability)} />
          <Metric label="重要性" value={imp.text} toneClass={TONE_TEXT[imp.tone]} />
        </div>

        {/* 实体 */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-ink-3">实体</span>
          {data.entities.length === 0 ? (
            <span className="text-sm text-ink-4">暂无标记实体</span>
          ) : (
            <div className="flex flex-wrap gap-2">
              {data.entities.map((e) => (
                <span
                  key={e}
                  className="px-2.5 py-1 rounded-full bg-panel border border-line text-xs text-ink-3 font-mono"
                >
                  {e}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* 时间 */}
        <div className="flex flex-col gap-2">
          <span className="text-xs font-medium text-ink-3">时间</span>
          <div className="flex gap-8 text-sm">
            <div className="flex flex-col">
              <span className="text-ink-4 text-xs">创建</span>
              <span className="font-mono text-ink">{formatDate(data.created)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-ink-4 text-xs">更新</span>
              <span className="font-mono text-ink">{formatDate(data.updated)}</span>
            </div>
            <div className="flex flex-col">
              <span className="text-ink-4 text-xs">访问次数</span>
              <span className="font-mono text-ink">{data.access_count}</span>
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="删除记忆"
        body={`该操作不可撤销。确认删除「${data.content.slice(0, 20)}…」？`}
        confirmText="确认删除"
        danger
        loading={del.isPending}
        onConfirm={handleDelete}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  )
}

function Metric({
  label,
  value,
  accent,
  tone,
  toneClass,
}: {
  label: string
  value: string
  accent?: boolean
  tone?: "ok" | "warn" | "err"
  toneClass?: string
}) {
  const color = accent
    ? "text-accent"
    : tone === "ok"
      ? "text-ok"
      : tone === "warn"
        ? "text-warn"
        : tone === "err"
          ? "text-err"
          : toneClass || "text-ink"
  return (
    <div className="bg-panel border border-line rounded-lg p-3 flex flex-col gap-1">
      <span className="text-[11px] text-ink-3">{label}</span>
      <span className={`text-xl font-bold font-mono ${color}`}>{value}</span>
    </div>
  )
}
