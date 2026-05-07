import { cn } from '@/lib/utils'
import type { ChecklistPriority } from '@/lib/api-schemas'

const STYLES: Record<ChecklistPriority, string> = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-amber-100 text-amber-800 border-amber-200',
  low: 'bg-stone-100 text-stone-700 border-stone-200',
}

export function PriorityBadge({ priority }: { priority: ChecklistPriority }) {
  return (
    <span
      className={cn(
        'inline-block px-2 py-0.5 rounded-full text-xs border capitalize',
        STYLES[priority],
      )}
    >
      {priority}
    </span>
  )
}
