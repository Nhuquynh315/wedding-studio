import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { GripVertical } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { GuestPublic } from '@/lib/api-schemas'

type Props = {
  guest: GuestPublic
  containerId: string
}

export function DraggableGuestChip({ guest, containerId }: Props) {
  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `guest-${guest.id}`,
    data: { type: 'guest', guest, containerId },
  })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.4 : 1,
  }

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      className={cn(
        'flex items-center gap-2 px-2.5 py-1.5 bg-white border border-[var(--color-border-default)] rounded-md text-sm cursor-grab active:cursor-grabbing hover:border-[var(--color-rose)] transition-colors',
        isDragging && 'shadow-lg',
      )}
    >
      <GripVertical className="h-3.5 w-3.5 text-[var(--color-text-muted)] flex-shrink-0" />
      <span className="truncate">{guest.full_name}</span>
    </div>
  )
}
