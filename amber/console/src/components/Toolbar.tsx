interface ToolbarProps {
  searchInput: string
  onSearchInput: (v: string) => void
  onSearchSubmit: () => void
  onSearchClear: () => void
  searching: boolean
  tier: string
  category: string
  categories: string[]
  onTierChange: (v: string) => void
  onCategoryChange: (v: string) => void
}

const TIERS = ["", "L1", "L2", "L3", "L4"]

export default function Toolbar({
  searchInput,
  onSearchInput,
  onSearchSubmit,
  onSearchClear,
  searching,
  tier,
  category,
  categories,
  onTierChange,
  onCategoryChange,
}: ToolbarProps) {
  return (
    <div className="flex items-center gap-3 px-5 h-16 border-b border-line bg-panel shrink-0">
      {/* 搜索框 */}
      <div className="relative flex-1 max-w-md">
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-4 text-sm">⌕</span>
        <input
          value={searchInput}
          onChange={(e) => onSearchInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") onSearchSubmit()
          }}
          placeholder="搜索记忆内容、实体或关键词…"
          className="w-full h-9 pl-9 pr-9 rounded-lg bg-card border border-line text-sm text-ink placeholder:text-ink-4 outline-none focus:border-accent/60 transition-colors"
        />
        {searching && (
          <button
            onClick={onSearchClear}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-4 hover:text-ink text-xs"
            title="清除搜索"
          >
            ✕
          </button>
        )}
      </div>

      {/* 层级筛选 */}
      <select
        value={tier}
        onChange={(e) => onTierChange(e.target.value)}
        className="h-9 rounded-lg bg-card border border-line text-sm text-ink-2 px-3 outline-none focus:border-accent/60"
      >
        <option value="">全部层级</option>
        {TIERS.filter((t) => t).map((t) => (
          <option key={t} value={t}>
            {t}
          </option>
        ))}
      </select>

      {/* 分类筛选 */}
      <select
        value={category}
        onChange={(e) => onCategoryChange(e.target.value)}
        className="h-9 rounded-lg bg-card border border-line text-sm text-ink-2 px-3 outline-none focus:border-accent/60"
      >
        <option value="">全部分类</option>
        {categories.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
    </div>
  )
}
