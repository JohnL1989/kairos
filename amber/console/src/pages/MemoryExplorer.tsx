import { useState } from "react"
import { useSearchParams } from "react-router-dom"
import Toolbar from "../components/Toolbar"
import MemoryList from "../components/MemoryList"
import MemoryInspector from "../components/MemoryInspector"
import { EmptyState, ErrorState, SkeletonList } from "../components/States"
import { useMemories, useSearch, useStats } from "../lib/queries"

export default function MemoryExplorer() {
  const [searchParams] = useSearchParams()
  const [searchInput, setSearchInput] = useState("")
  const [activeQuery, setActiveQuery] = useState<string | null>(null)
  const [tier, setTier] = useState("")
  const [category, setCategory] = useState(searchParams.get("category") ?? "")
  const [listLimit, setListLimit] = useState(20)
  const [selectedId, setSelectedId] = useState<number | null>(null)

  const { data: stats } = useStats()
  const categories = stats ? Object.keys(stats.by_category) : []

  const searching = activeQuery != null
  const list = useMemories({ tier, category, limit: listLimit })
  const search = useSearch(activeQuery ?? "", 30)

  const query = searching ? search : list
  const memories = query.data?.memories ?? []
  const isLoading = query.isLoading
  const isError = query.isError
  const error = query.error

  const handleSearchSubmit = () => {
    const q = searchInput.trim()
    if (q.length > 2) setActiveQuery(q)
    else setActiveQuery(null)
  }
  const handleSearchClear = () => {
    setSearchInput("")
    setActiveQuery(null)
  }
  const handleTierChange = (v: string) => {
    setTier(v)
    setActiveQuery(null)
  }
  const handleCategoryChange = (v: string) => {
    setCategory(v)
    setActiveQuery(null)
  }
  const clearFilters = () => {
    setTier("")
    setCategory("")
    setActiveQuery(null)
    setSearchInput("")
  }

  const showLoadMore = !searching && !isLoading && memories.length > 0 && memories.length >= listLimit

  return (
    <div className="flex flex-col h-full">
      <Toolbar
        searchInput={searchInput}
        onSearchInput={setSearchInput}
        onSearchSubmit={handleSearchSubmit}
        onSearchClear={handleSearchClear}
        searching={searching}
        tier={tier}
        category={category}
        categories={categories}
        onTierChange={handleTierChange}
        onCategoryChange={handleCategoryChange}
      />

      <div className="flex flex-1 min-h-0">
        {/* 列表区 */}
        <section className="flex-1 min-w-0 flex flex-col border-r border-line">
          <div className="flex-1 overflow-y-auto">
            {isLoading ? (
              <SkeletonList />
            ) : isError ? (
              <ErrorState
                message={error instanceof Error ? error.message : "加载失败"}
                onRetry={() => query.refetch()}
              />
            ) : memories.length === 0 ? (
              <EmptyState
                title={searching ? "未找到匹配记忆" : "暂无记忆"}
                subtitle={
                  searching
                    ? "尝试更换关键词或缩短查询"
                    : "当前筛选条件下没有记忆，试试清除筛选"
                }
                action={
                  <button
                    onClick={clearFilters}
                    className="h-9 px-5 rounded-lg bg-accent text-white text-sm font-medium hover:bg-[#0f8fe0] transition-colors"
                  >
                    清除筛选
                  </button>
                }
              />
            ) : (
              <MemoryList
                memories={memories}
                selectedId={selectedId}
                onSelect={setSelectedId}
              />
            )}
          </div>

          {showLoadMore && (
            <div className="shrink-0 px-3 py-3 border-t border-line flex justify-center">
              <button
                onClick={() => setListLimit((l) => l + 20)}
                className="h-9 px-6 rounded-lg bg-card border border-line text-sm text-ink-2 hover:bg-[#17171b] transition-colors"
              >
                加载更多
              </button>
            </div>
          )}
        </section>

        {/* Inspector */}
        <aside className="w-[380px] shrink-0 bg-card/40">
          <MemoryInspector
            memoryId={selectedId}
            onDeleted={() => setSelectedId(null)}
            onClose={() => setSelectedId(null)}
          />
        </aside>
      </div>
    </div>
  )
}
