import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Pencil, Trash2, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AddGuestDialog } from '@/pages/guests/AddGuestDialog'
import { DeleteGuestDialog } from '@/pages/guests/DeleteGuestDialog'
import { EditGuestDialog } from '@/pages/guests/EditGuestDialog'
import { RSVPPill } from '@/pages/guests/RSVPPill'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { GuestPublic } from '@/lib/api-schemas'

export function GuestsPage() {
  const { activeId, isLoading: weddingsLoading } = useActiveWedding()
  const [editing, setEditing] = useState<GuestPublic | null>(null)
  const [deleting, setDeleting] = useState<GuestPublic | null>(null)

  const guestsQuery = useQuery({
    queryKey: queryKeys.guests.list(activeId ?? -1, { limit: 200 }),
    queryFn: () => api.guests.list(activeId!, { limit: 200 }),
    enabled: !!activeId,
  })

  if (weddingsLoading) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      </div>
    )
  }

  if (!activeId) {
    return (
      <div className="p-8">
        <p className="text-sm text-[var(--color-text-muted)]">
          Select a wedding from the dashboard first.
        </p>
      </div>
    )
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-serif text-3xl">Guests</h1>
        <AddGuestDialog weddingId={activeId} />
      </div>

      {guestsQuery.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-12" />
          ))}
        </div>
      ) : guestsQuery.isError ? (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-sm text-red-700 mb-4">Couldn't load guests.</p>
            <Button onClick={() => guestsQuery.refetch()}>Try again</Button>
          </CardContent>
        </Card>
      ) : guestsQuery.data && guestsQuery.data.items.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Users className="h-10 w-10 text-[var(--color-rose)] mx-auto mb-3" />
            <h2 className="font-serif text-xl mb-1">No guests yet</h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-4">
              Add your first guest to start tracking RSVPs.
            </p>
            <AddGuestDialog weddingId={activeId} />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[var(--color-border-default)] text-left text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3 hidden md:table-cell">Group</th>
                  <th className="px-4 py-3 hidden lg:table-cell">Email</th>
                  <th className="px-4 py-3">RSVP</th>
                  <th className="px-4 py-3 w-20"></th>
                </tr>
              </thead>
              <tbody>
                {guestsQuery.data?.items.map((guest) => (
                  <tr
                    key={guest.id}
                    className="border-b border-[var(--color-border-default)] last:border-0 hover:bg-[var(--color-cream)]"
                  >
                    <td className="px-4 py-3">
                      <div className="font-medium">{guest.full_name}</div>
                      {guest.meal_preference && (
                        <div className="text-xs text-[var(--color-text-muted)]">
                          {guest.meal_preference}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 hidden md:table-cell text-sm text-[var(--color-text-muted)]">
                      {guest.group_name || '—'}
                    </td>
                    <td className="px-4 py-3 hidden lg:table-cell text-sm text-[var(--color-text-muted)]">
                      {guest.email || '—'}
                    </td>
                    <td className="px-4 py-3">
                      <RSVPPill status={guest.rsvp_status} />
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex gap-1 justify-end">
                        <button
                          onClick={() => setEditing(guest)}
                          className="p-1.5 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)]"
                          aria-label="Edit"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => setDeleting(guest)}
                          className="p-1.5 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700"
                          aria-label="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      <EditGuestDialog
        weddingId={activeId}
        guest={editing}
        onClose={() => setEditing(null)}
      />
      <DeleteGuestDialog
        weddingId={activeId}
        guest={deleting}
        onClose={() => setDeleting(null)}
      />
    </div>
  )
}
