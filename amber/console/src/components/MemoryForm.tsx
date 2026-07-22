import { createContext, useCallback, useContext, useState, type ReactNode } from "react"
import { useCreateMemory, useUpdateMemory } from "../lib/queries"
import { useToast } from "./Toast"
import type { MemoryCreatePayload, MemoryDetail, MemoryUpdatePayload } from "../types"

interface MemoryFormCtx {
  openCreate: () => void
  openEdit: (m: MemoryDetail) => void
}
const Ctx = createContext<MemoryFormCtx | null>(null)
export function useMemoryForm(): MemoryFormCtx {
  const c = useContext(Ctx)
  if (!c) throw new Error("useMemoryForm 必须在 MemoryFormProvider 内使用")
  return c
}

export function MemoryFormProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<{ open: boolean; mode: "create" | "edit"; editing?: MemoryDetail }>({
    open: false,
    mode: "create",
  })
  const openCreate = useCallback(() => setState({ open: true, mode: "create" }), [])
  const openEdit = useCallback((m: MemoryDetail) => setState({ open: true, mode: "edit", editing: m }), [])
  return (
    <Ctx.Provider value={{ openCreate, openEdit }}>
      {children}
      {state.open && (
        <MemoryFormModal
          mode={state.mode}
          editing={state.editing}
          onClose={() => setState((s) => ({ ...s, open: false }))}
        />
      )}
    </Ctx.Provider>
  )
}

const TIERS = ["L1", "L2", "L3", "L4"]
const inputCls =
  "w-full h-9 rounded-lg bg-card border border-line text-sm text-ink placeholder:text-ink-4 outline-none focus:border-accent/60 px-3"
const labelCls = "text-xs font-medium text-ink-3 mb-1.5 block"

function MemoryFormModal({
  mode,
  editing,
  onClose,
}: {
  mode: "create" | "edit"
  editing?: MemoryDetail
  onClose: () => void
}) {
  const create = useCreateMemory()
  const update = useUpdateMemory()
  const toast = useToast()

  const [content, setContent] = useState(editing?.content ?? "")
  const [category, setCategory] = useState(editing?.category ?? "general")
  const [scope, setScope] = useState<"durable" | "general">(editing?.scope === "durable" ? "durable" : "general")
  const [tier, setTier] = useState(editing?.tier ?? "L1")
  const [importance, setImportance] = useState(editing ? String(editing.importance) : "")
  const [reliability, setReliability] = useState(editing ? String(editing.reliability) : "")
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    if (!content.trim()) {
      toast.push("warn", "请填写内容", "记忆内容不能为空")
      return
    }
    setBusy(true)
    try {
      const payload: MemoryCreatePayload & MemoryUpdatePayload = {
        content: content.trim(),
        category: category.trim() || "general",
        tier: tier || undefined,
        importance: importance ? Number(importance) : undefined,
        reliability: reliability ? Number(reliability) : undefined,
      }
      if (mode === "edit" && editing) {
        const body: MemoryUpdatePayload = { ...payload }
        if (body.tier === undefined) delete body.tier
        await update.mutateAsync({ id: editing.id, payload: body })
        toast.push("ok", "保存成功", `记忆 #${editing.id} 已更新`)
      } else {
        await create.mutateAsync({ ...payload, scope_target: scope })
        toast.push("ok", "创建成功", "新记忆已写入")
      }
      onClose()
    } catch (e) {
      toast.push("err", "操作失败", e instanceof Error ? e.message : "请稍后重试")
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[95] flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative w-[520px] max-w-full bg-card border border-line rounded-2xl p-6 flex flex-col gap-4 max-h-[90vh] overflow-y-auto no-scrollbar">
        <h3 className="text-lg font-bold text-ink">{mode === "edit" ? "编辑记忆" : "新建记忆"}</h3>

        <div>
          <label className={labelCls}>内容 *</label>
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={4}
            placeholder="输入记忆内容…"
            className="w-full rounded-lg bg-card border border-line text-sm text-ink placeholder:text-ink-4 outline-none focus:border-accent/60 p-3 resize-none"
          />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelCls}>分类</label>
            <input value={category} onChange={(e) => setCategory(e.target.value)} className={inputCls} placeholder="general" />
          </div>
          {mode === "create" ? (
            <div>
              <label className={labelCls}>作用域</label>
              <select value={scope} onChange={(e) => setScope(e.target.value as "durable" | "general")} className={inputCls}>
                <option value="general">general · 普通</option>
                <option value="durable">durable · 持久</option>
              </select>
            </div>
          ) : (
            <div>
              <label className={labelCls}>层级</label>
              <select value={tier} onChange={(e) => setTier(e.target.value)} className={inputCls}>
                {TIERS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="grid grid-cols-3 gap-3">
          {mode === "edit" && (
            <div>
              <label className={labelCls}>层级</label>
              <select value={tier} onChange={(e) => setTier(e.target.value)} className={inputCls}>
                {TIERS.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className={labelCls}>重要性 0–1</label>
            <input
              value={importance}
              onChange={(e) => setImportance(e.target.value)}
              type="number"
              min={0}
              max={1}
              step={0.05}
              className={inputCls}
              placeholder="0.5"
            />
          </div>
          <div>
            <label className={labelCls}>可靠性 0–1</label>
            <input
              value={reliability}
              onChange={(e) => setReliability(e.target.value)}
              type="number"
              min={0}
              max={1}
              step={0.05}
              className={inputCls}
              placeholder="0.5"
            />
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-1">
          <button
            onClick={onClose}
            disabled={busy}
            className="h-9 px-4 rounded-lg bg-line text-ink text-sm font-medium hover:bg-[#2f2f35] transition-colors disabled:opacity-50"
          >
            取消
          </button>
          <button
            onClick={submit}
            disabled={busy}
            className="h-9 px-5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-[#0f8fe0] transition-colors disabled:opacity-60"
          >
            {busy ? "处理中…" : mode === "edit" ? "保存" : "创建"}
          </button>
        </div>
      </div>
    </div>
  )
}
