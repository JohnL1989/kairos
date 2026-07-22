import { createContext, useCallback, useContext, useRef, useState } from "react"
import type { ReactNode } from "react"

type ToastTone = "ok" | "warn" | "err"

interface ToastItem {
  id: number
  tone: ToastTone
  title: string
  message?: string
}

interface ToastApi {
  push: (tone: ToastTone, title: string, message?: string) => void
}

const ToastContext = createContext<ToastApi | null>(null)

export function useToast(): ToastApi {
  const ctx = useContext(ToastContext)
  if (!ctx) throw new Error("useToast 必须在 ToastProvider 内使用")
  return ctx
}

const TONE_BAR: Record<ToastTone, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  err: "bg-err",
}
const TONE_DOT: Record<ToastTone, string> = {
  ok: "bg-ok",
  warn: "bg-warn",
  err: "bg-err",
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const seq = useRef(0)

  const push = useCallback((tone: ToastTone, title: string, message?: string) => {
    const id = ++seq.current
    setItems((prev) => [...prev, { id, tone, title, message }])
    setTimeout(() => {
      setItems((prev) => prev.filter((t) => t.id !== id))
    }, 4200)
  }, [])

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-[360px] pointer-events-none">
        {items.map((t) => (
          <div
            key={t.id}
            className="flex items-center gap-3 bg-card border border-line rounded-lg pl-3 pr-4 py-3 shadow-2xl shadow-black/40 pointer-events-auto animate-[fadein_.18s_ease-out]"
          >
            <span className={`w-1 self-stretch rounded-full ${TONE_BAR[t.tone]}`} />
            <span className={`w-2.5 h-2.5 rounded-full ${TONE_DOT[t.tone]}`} />
            <div className="flex flex-col min-w-0">
              <span className="text-sm font-medium text-ink leading-tight">{t.title}</span>
              {t.message && (
                <span className="text-xs text-ink-3 mt-0.5 leading-snug">{t.message}</span>
              )}
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

// 内联 keyframes（避免额外 css 文件）
const styleId = "toast-keyframes"
if (typeof document !== "undefined" && !document.getElementById(styleId)) {
  const el = document.createElement("style")
  el.id = styleId
  el.textContent = "@keyframes fadein{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}"
  document.head.appendChild(el)
}
