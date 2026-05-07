import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CheckSquare } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { QueryErrorState } from '@/components/QueryErrorState'
import { AddItemDialog } from '@/pages/checklist/AddItemDialog'
import { BulkCompleteDialog } from '@/pages/checklist/BulkCompleteDialog'
import { ChecklistFilters } from '@/pages/checklist/ChecklistFilters'
import { ChecklistItemRow } from '@/pages/checklist/ChecklistItemRow'
import { DeleteItemDialog } from '@/pages/checklist/DeleteItemDialog'
import { EditItemDialog } from '@/pages/checklist/EditItemDialog'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { ChecklistCategory, ChecklistItemPublic, ChecklistPriority } from '@/lib/api-schemas'

export function ChecklistPage() {
  const { activeId, isLoading: weddingsLoading } = useActiveWedding()
  const [editing, setEditing] = useState<ChecklistItemPublic | null>(null)
  const [deleting, setDeleting] = useState<ChecklistItemPublic | null>(null)

  const [category, setCategory] = useState<ChecklistCategory | 'all'>('all')
  const [priority, setPriority] = useState<ChecklistPriority | 'all'>('all')
  const [completed, setCompleted] = useState<'all' | 'yes' | 'no'>('all')

  const params = {
    category: category !== 'all' ? category : undefined,
    priority: priority !== 'all' ? priority : undefined,
    completed: completed === 'all' ? undefined : completed === 'yes',
  }

  const itemsQuery = useQuery({
    queryKey: queryKeys.checklist.list(activeId ?? -1, params),
    queryFn: () => api.checklist.list(activeId!, params),
    enabled: !!activeId,
  })

  if (weddingsLoading || !activeId) {
    return (
      <div className="p-8">
        <Skeleton className="h-96" />
      </div>
    )
  }

  const items = itemsQuery.data ?? []
  const openCount = items.filter((i) => !i.is_completed).length

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-serif text-3xl">Checklist</h1>
        <AddItemDialog weddingId={activeId} />
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <ChecklistFilters
          category={category}
          priority={priority}
          completed={completed}
          onCategoryChange={setCategory}
          onPriorityChange={setPriority}
          onCompletedChange={setCompleted}
        />
        {category !== 'all' && (
          <BulkCompleteDialog
            weddingId={activeId}
            category={category}
            openItemCount={openCount}
          />
        )}
      </div>

      {itemsQuery.isLoading ? (
        <Card>
          <CardContent className="p-4 space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-12" />
            ))}
          </CardContent>
        </Card>
      ) : itemsQuery.isError ? (
        <QueryErrorState
          error={itemsQuery.error}
          onRetry={() => itemsQuery.refetch()}
          resourceName="checklist items"
        />
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <CheckSquare className="h-10 w-10 text-[var(--color-rose)] mx-auto mb-3" />
            <h2 className="font-serif text-xl mb-1">No items match</h2>
            <p className="text-sm text-[var(--color-text-muted)]">
              Adjust the filters or add a new item.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-2">
            {items.map((item) => (
              <ChecklistItemRow
                key={item.id}
                weddingId={activeId}
                item={item}
                onEdit={() => setEditing(item)}
                onDelete={() => setDeleting(item)}
              />
            ))}
          </CardContent>
        </Card>
      )}

      <EditItemDialog
        weddingId={activeId}
        item={editing}
        onClose={() => setEditing(null)}
      />
      <DeleteItemDialog
        weddingId={activeId}
        item={deleting}
        onClose={() => setDeleting(null)}
      />
    </div>
  )
}
