import { type ReactNode } from 'react'
import { useDroppable } from '@dnd-kit/core'
import { SortableContext, verticalListSortingStrategy } from '@dnd-kit/sortable'
import { cn } from '@/lib/utils'
import { DraggableGuestChip } from '@/pages/seating/DraggableGuestChip'
import type { GuestPublic } from '@/lib/api-schemas'

type Props = {
  id: string
  guests: GuestPublic[]
  emptyMessage?: string
  className?: string
  children?: ReactNode
}

export function DroppableZone({
  id,
  guests,
  emptyMessage = 'Drop guests here',
  className,
  children,
}: Props) {
  const { setNodeRef, isOver } = useDroppable({ id })

  return (
    <div
      ref={setNodeRef}
      className={cn(
        'border-2 border-dashed rounded-lg p-3 transition-colors',
        isOver
          ? 'border-[var(--color-rose)] bg-[var(--color-rose-bg)]'
          : 'border-[var(--color-border-default)]',
        className,
      )}
    >
      {children}
      <SortableContext
        items={guests.map((g) => `guest-${g.id}`)}
        strategy={verticalListSortingStrategy}
      >
        <div className="space-y-1.5 mt-2 min-h-[40px]">
          {guests.length === 0 ? (
            <p className="text-xs text-[var(--color-text-muted)] py-2 text-center">
              {emptyMessage}
            </p>
          ) : (
            guests.map((g) => <DraggableGuestChip key={g.id} guest={g} containerId={id} />)
          )}
        </div>
      </SortableContext>
    </div>
  )
}
