import { Pencil, Trash2 } from 'lucide-react'
import type { BudgetCategoryPublic, BudgetSummary } from '@/lib/api-schemas'
import { formatAUD } from '@/lib/format'

const FALLBACK_COLORS = [
  '#c9687a',
  '#e8a87c',
  '#7cb8e8',
  '#a8d8a8',
  '#d4a8d8',
  '#f0d4a8',
  '#a8c8d8',
  '#d8c8a8',
]

type Props = {
  categories: BudgetCategoryPublic[]
  summary: BudgetSummary | undefined
  onEdit: (cat: BudgetCategoryPublic) => void
  onDelete: (cat: BudgetCategoryPublic) => void
}

export function CategoryList({ categories, summary, onEdit, onDelete }: Props) {
  const spentByCat = new Map(
    (summary?.categories ?? []).map((c) => [c.category_id, c.spent_amount]),
  )

  return (
    <div className="space-y-3">
      {categories.map((cat, i) => {
        const allocated = cat.allocated_amount ?? 0
        const spent = spentByCat.get(cat.id) ?? 0
        const pct = allocated > 0 ? Math.min(100, (spent / allocated) * 100) : 0
        const color = cat.color || FALLBACK_COLORS[i % FALLBACK_COLORS.length]
        const isOver = spent > allocated && allocated > 0

        return (
          <div key={cat.id} className="group">
            <div className="flex items-center justify-between mb-1.5">
              <div className="flex items-center gap-2">
                <span
                  className="inline-block w-3 h-3 rounded-full flex-shrink-0"
                  style={{ backgroundColor: color }}
                />
                <span className="font-medium text-sm">{cat.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--color-text-muted)]">
                  {formatAUD(spent)} / {formatAUD(allocated)}
                </span>
                <button
                  onClick={() => onEdit(cat)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)] transition-opacity"
                  aria-label="Edit"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => onDelete(cat)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700 transition-opacity"
                  aria-label="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
            <div className="h-2 bg-[var(--color-cream)] rounded-full overflow-hidden">
              <div
                className="h-full transition-all"
                style={{
                  width: `${pct}%`,
                  backgroundColor: isOver ? '#dc2626' : color,
                }}
              />
            </div>
            {isOver && (
              <p className="text-xs text-red-600 mt-1">
                Over budget by {formatAUD(spent - allocated)}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
