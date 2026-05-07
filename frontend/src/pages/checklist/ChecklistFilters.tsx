import { CHECKLIST_CATEGORIES, CHECKLIST_PRIORITIES } from '@/pages/checklist/checklistSchema'
import type { ChecklistCategory, ChecklistPriority } from '@/lib/api-schemas'

type Props = {
  category: ChecklistCategory | 'all'
  priority: ChecklistPriority | 'all'
  completed: 'all' | 'yes' | 'no'
  onCategoryChange: (v: ChecklistCategory | 'all') => void
  onPriorityChange: (v: ChecklistPriority | 'all') => void
  onCompletedChange: (v: 'all' | 'yes' | 'no') => void
}

const selectClass =
  'px-3 py-2 border border-[var(--color-border-default)] rounded-md text-sm bg-white focus:outline-none focus:border-[var(--color-rose)]'

export function ChecklistFilters({
  category,
  priority,
  completed,
  onCategoryChange,
  onPriorityChange,
  onCompletedChange,
}: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      <select
        value={category}
        onChange={(e) => onCategoryChange(e.target.value as ChecklistCategory | 'all')}
        className={selectClass}
        aria-label="Filter by category"
      >
        <option value="all">All categories</option>
        {CHECKLIST_CATEGORIES.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>

      <select
        value={priority}
        onChange={(e) => onPriorityChange(e.target.value as ChecklistPriority | 'all')}
        className={selectClass}
        aria-label="Filter by priority"
      >
        <option value="all">All priorities</option>
        {CHECKLIST_PRIORITIES.map((p) => (
          <option key={p} value={p} className="capitalize">
            {p.charAt(0).toUpperCase() + p.slice(1)}
          </option>
        ))}
      </select>

      <select
        value={completed}
        onChange={(e) => onCompletedChange(e.target.value as 'all' | 'yes' | 'no')}
        className={selectClass}
        aria-label="Filter by completion"
      >
        <option value="all">All items</option>
        <option value="no">Open</option>
        <option value="yes">Completed</option>
      </select>
    </div>
  )
}
