import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Pencil, Trash2 } from 'lucide-react'

import { PriorityBadge } from '@/pages/checklist/PriorityBadge'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import { cn } from '@/lib/utils'
import type { ChecklistItemPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  item: ChecklistItemPublic
  onEdit: () => void
  onDelete: () => void
}

export function ChecklistItemRow({ weddingId, item, onEdit, onDelete }: Props) {
  const qc = useQueryClient()

  const toggle = useMutation({
    mutationFn: (completed: boolean) =>
      api.checklist.update(weddingId, item.id, { is_completed: completed }),
    onMutate: async (completed) => {
      await qc.cancelQueries({ queryKey: queryKeys.checklist.all(weddingId) })
      const previous = qc.getQueriesData<ChecklistItemPublic[]>({
        queryKey: queryKeys.checklist.all(weddingId),
      })
      qc.setQueriesData<ChecklistItemPublic[]>(
        { queryKey: queryKeys.checklist.all(weddingId) },
        (old) => {
          if (!old) return old
          return old.map((i) => (i.id === item.id ? { ...i, is_completed: completed } : i))
        },
      )
      return { previous }
    },
    onError: (_err, _completed, context) => {
      if (context?.previous) {
        context.previous.forEach(([key, data]) => qc.setQueryData(key, data))
      }
    },
    onSettled: () => {
      qc.invalidateQueries({ queryKey: queryKeys.checklist.all(weddingId) })
    },
  })

  const isOverdue =
    item.due_date && !item.is_completed && new Date(item.due_date) < new Date()

  return (
    <div className="flex items-center gap-3 py-2.5 px-3 group hover:bg-[var(--color-cream)] rounded">
      <input
        type="checkbox"
        checked={item.is_completed}
        onChange={(e) => toggle.mutate(e.target.checked)}
        className="h-4 w-4 rounded cursor-pointer accent-[var(--color-rose)]"
        aria-label={`Mark ${item.title} as ${item.is_completed ? 'incomplete' : 'complete'}`}
      />
      <div className="flex-1 min-w-0">
        <div
          className={cn(
            'truncate',
            item.is_completed && 'line-through text-[var(--color-text-muted)]',
          )}
        >
          {item.title}
        </div>
        <div className="flex items-center gap-2 text-xs text-[var(--color-text-muted)] mt-0.5">
          <span>{item.category}</span>
          {item.due_date && (
            <>
              <span>·</span>
              <span className={cn(isOverdue && 'text-red-600 font-medium')}>
                {isOverdue ? 'Overdue: ' : 'Due: '}
                {new Date(item.due_date).toLocaleDateString('en-AU')}
              </span>
            </>
          )}
        </div>
      </div>
      <PriorityBadge priority={item.priority} />
      <div className="flex gap-1">
        <button
          onClick={onEdit}
          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)] transition-opacity"
          aria-label="Edit"
        >
          <Pencil className="h-4 w-4" />
        </button>
        <button
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700 transition-opacity"
          aria-label="Delete"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  )
}
