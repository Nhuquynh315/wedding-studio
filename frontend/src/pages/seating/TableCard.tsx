import { Pencil, Trash2, Users } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Card, CardContent } from '@/components/ui/card'
import { DroppableZone } from '@/pages/seating/DroppableZone'
import type { WeddingTableWithGuests } from '@/lib/api-schemas'

type Props = {
  table: WeddingTableWithGuests
  onEdit: () => void
  onDelete: () => void
}

export function TableCard({ table, onEdit, onDelete }: Props) {
  const assigned = table.guests?.length ?? 0
  const isOver = assigned > table.capacity

  return (
    <Card className="group">
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div>
            <h3 className="font-medium">
              Table {table.table_number}
              {table.table_name && (
                <span className="text-[var(--color-text-muted)] font-normal">
                  {' · '}
                  {table.table_name}
                </span>
              )}
            </h3>
            <div
              className={cn(
                'flex items-center gap-1 text-xs mt-0.5',
                isOver ? 'text-red-600 font-medium' : 'text-[var(--color-text-muted)]',
              )}
            >
              <Users className="h-3 w-3" />
              <span>
                {assigned} / {table.capacity}
              </span>
              {isOver && <span> — over capacity</span>}
            </div>
          </div>
          <div className="flex gap-1">
            <button
              onClick={onEdit}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)] transition-opacity"
              aria-label="Edit"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={onDelete}
              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700 transition-opacity"
              aria-label="Delete"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        <DroppableZone
          id={`table-${table.id}`}
          guests={table.guests ?? []}
          emptyMessage="Drop guests here"
        />
      </CardContent>
    </Card>
  )
}
