import { useRef } from 'react'
import { useVirtualizer } from '@tanstack/react-virtual'
import { Pencil, Trash2 } from 'lucide-react'

import { RSVPPill } from '@/pages/guests/RSVPPill'
import type { GuestPublic } from '@/lib/api-schemas'

const ROW_HEIGHT = 64

type Props = {
  guests: GuestPublic[]
  onEdit: (guest: GuestPublic) => void
  onDelete: (guest: GuestPublic) => void
}

export function VirtualizedGuestRows({ guests, onEdit, onDelete }: Props) {
  const scrollRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: guests.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => ROW_HEIGHT,
    overscan: 5,
  })

  return (
    <div
      ref={scrollRef}
      className="overflow-y-auto"
      style={{ height: 'calc(100vh - 280px)' }}
    >
      {/* Sticky header */}
      <table className="w-full">
        <thead className="sticky top-0 z-10 bg-white">
          <tr className="border-b border-[var(--color-border-default)] text-left text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
            <th className="px-4 py-3">Name</th>
            <th className="px-4 py-3 hidden md:table-cell">Group</th>
            <th className="px-4 py-3 hidden lg:table-cell">Email</th>
            <th className="px-4 py-3">RSVP</th>
            <th className="px-4 py-3 w-20"></th>
          </tr>
        </thead>
      </table>

      {/* Virtualized body — absolute-positioned divs; tables resist this */}
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((virtualRow) => {
          const guest = guests[virtualRow.index]
          return (
            <div
              key={guest.id}
              className="absolute top-0 left-0 w-full border-b border-[var(--color-border-default)] hover:bg-[var(--color-cream)] flex items-center"
              style={{
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div className="flex-1 grid grid-cols-[2fr_auto_auto_auto] md:grid-cols-[2fr_1fr_auto_auto] lg:grid-cols-[2fr_1fr_2fr_auto_auto] gap-4 px-4 items-center">
                <div>
                  <div className="font-medium">{guest.full_name}</div>
                  {guest.meal_preference && (
                    <div className="text-xs text-[var(--color-text-muted)]">
                      {guest.meal_preference}
                    </div>
                  )}
                </div>
                <div className="hidden md:block text-sm text-[var(--color-text-muted)]">
                  {guest.group_name || '—'}
                </div>
                <div className="hidden lg:block text-sm text-[var(--color-text-muted)] truncate">
                  {guest.email || '—'}
                </div>
                <div>
                  <RSVPPill status={guest.rsvp_status} />
                </div>
                <div className="flex gap-1 justify-end">
                  <button
                    onClick={() => onEdit(guest)}
                    className="p-1.5 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)]"
                    aria-label="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onDelete(guest)}
                    className="p-1.5 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700"
                    aria-label="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
