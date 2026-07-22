interface ConfirmDialogProps {
  open: boolean
  title: string
  body: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
  loading?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmDialog({
  open,
  title,
  body,
  confirmText = "确认",
  cancelText = "取消",
  danger = false,
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  if (!open) return null
  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60" onClick={onCancel} />
      <div className="relative w-[400px] bg-card border border-line rounded-2xl p-6 flex flex-col gap-4">
        <h3 className="text-lg font-bold text-ink">{title}</h3>
        <p className="text-sm text-ink-3 leading-relaxed">{body}</p>
        <div className="flex justify-end gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="h-9 px-4 rounded-lg bg-line text-ink text-sm font-medium hover:bg-[#2f2f35] transition-colors disabled:opacity-50"
          >
            {cancelText}
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={`h-9 px-4 rounded-lg text-sm font-medium text-white transition-colors disabled:opacity-60 ${
              danger ? "bg-err hover:bg-[#d63c1c]" : "bg-accent hover:bg-[#0f8fe0]"
            }`}
          >
            {loading ? "处理中…" : confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
