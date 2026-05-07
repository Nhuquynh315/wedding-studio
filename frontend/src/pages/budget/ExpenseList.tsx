import { Pencil, Trash2 } from 'lucide-react'
import type { BudgetCategoryPublic, ExpensePublic } from '@/lib/api-schemas'
import { formatAUD } from '@/lib/format'

type Props = {
  expenses: ExpensePublic[]
  categories: BudgetCategoryPublic[]
  onEdit: (e: ExpensePublic) => void
  onDelete: (e: ExpensePublic) => void
}

export function ExpenseList({ expenses, categories, onEdit, onDelete }: Props) {
  const catById = new Map(categories.map((c) => [c.id, c]))

  if (expenses.length === 0) {
    return (
      <p className="text-sm text-[var(--color-text-muted)] py-4">
        No expenses yet. Add one to start tracking spending.
      </p>
    )
  }

  return (
    <div className="divide-y divide-[var(--color-border-default)]">
      {expenses.map((exp) => {
        const cat = catById.get(exp.category_id ?? -1)
        const amount = exp.actual_cost ?? exp.estimated_cost ?? 0
        const date = exp.paid_date || exp.due_date

        return (
          <div key={exp.id} className="flex items-center justify-between py-3 group">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium">{exp.title}</span>
                {exp.is_paid ? (
                  <span className="text-xs px-1.5 py-0.5 bg-green-100 text-green-800 rounded-full">
                    Paid
                  </span>
                ) : (
                  <span className="text-xs px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded-full">
                    Unpaid
                  </span>
                )}
              </div>
              <div className="text-xs text-[var(--color-text-muted)] mt-0.5">
                {cat?.name ?? '—'}
                {date &&
                  ` · ${new Date(date).toLocaleDateString('en-AU', { day: 'numeric', month: 'short', year: 'numeric' })}`}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="font-mono text-sm">{formatAUD(amount)}</span>
              <div className="flex gap-1">
                <button
                  onClick={() => onEdit(exp)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)] transition-opacity"
                  aria-label="Edit"
                >
                  <Pencil className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => onDelete(exp)}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700 transition-opacity"
                  aria-label="Delete"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
