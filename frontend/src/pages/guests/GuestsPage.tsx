import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Users } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { QueryErrorState } from '@/components/QueryErrorState'
import { AddGuestDialog } from '@/pages/guests/AddGuestDialog'
import { ImportCsvDialog } from '@/pages/guests/ImportCsvDialog'
import { DeleteGuestDialog } from '@/pages/guests/DeleteGuestDialog'
import { EditGuestDialog } from '@/pages/guests/EditGuestDialog'
import { RSVPFilterChips, type FilterValue } from '@/pages/guests/RSVPFilterChips'
import { VirtualizedGuestRows } from '@/pages/guests/VirtualizedGuestRows'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { useDebounce } from '@/hooks/useDebounce'
import { useUrlState } from '@/hooks/useUrlState'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { GuestPublic, RSVPStatus } from '@/lib/api-schemas'

function isFilterValue(v: string | null): v is FilterValue {
  return v === 'pending' || v === 'confirmed' || v === 'declined' || v === 'all'
}

export function GuestsPage() {
  const { activeId, isLoading: weddingsLoading } = useActiveWedding()
  const [editing, setEditing] = useState<GuestPublic | null>(null)
  const [deleting, setDeleting] = useState<GuestPublic | null>(null)

  const [filterParam, setFilterParam] = useUrlState('rsvp')
  const filter: FilterValue = isFilterValue(filterParam) ? filterParam : 'all'

  const [search, setSearch] = useState('')
  const debouncedSearch = useDebounce(search, 350)

  const rsvpForApi: RSVPStatus | undefined = filter === 'all' ? undefined : filter

  const guestsQuery = useQuery({
    queryKey: queryKeys.guests.list(activeId ?? -1, { limit: 200, rsvp: rsvpForApi }),
    queryFn: () => api.guests.list(activeId!, { limit: 200, rsvp: rsvpForApi }),
    enabled: !!activeId,
  })

  const filteredGuests = useMemo(() => {
    const items = guestsQuery.data?.items ?? []
    if (!debouncedSearch.trim()) return items
    const q = debouncedSearch.trim().toLowerCase()
    return items.filter(
      (g) =>
        g.full_name.toLowerCase().includes(q) ||
        (g.email?.toLowerCase().includes(q) ?? false) ||
        (g.group_name?.toLowerCase().includes(q) ?? false),
    )
  }, [guestsQuery.data, debouncedSearch])

  if (weddingsLoading) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-48 mb-6" />
        <Skeleton className="h-10 mb-4" />
        <Skeleton className="h-96" />
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
        <div className="flex gap-2">
          <ImportCsvDialog weddingId={activeId} />
          <AddGuestDialog weddingId={activeId} />
        </div>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 mb-4">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--color-text-muted)]" />
          <Input
            type="search"
            placeholder="Search by name, email, or group…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <RSVPFilterChips
          value={filter}
          onChange={(v) => setFilterParam(v === 'all' ? null : v)}
        />
      </div>

      {(debouncedSearch || filter !== 'all') && !guestsQuery.isLoading && (
        <p className="text-sm text-[var(--color-text-muted)] mb-3">
          Showing {filteredGuests.length} of {guestsQuery.data?.items.length ?? 0}
          {filter !== 'all' && ` ${filter}`} guest
          {filteredGuests.length !== 1 && 's'}
        </p>
      )}

      {guestsQuery.isLoading ? (
        <Card>
          <CardContent className="p-0">
            <div className="space-y-1 p-4">
              {Array.from({ length: 8 }).map((_, i) => (
                <Skeleton key={i} className="h-12" />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : guestsQuery.isError ? (
        <QueryErrorState
          error={guestsQuery.error}
          onRetry={() => guestsQuery.refetch()}
          resourceName="guests"
        />
      ) : (guestsQuery.data?.items.length ?? 0) === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Users className="h-10 w-10 text-[var(--color-rose)] mx-auto mb-3" />
            <h2 className="font-serif text-xl mb-1">
              {filter !== 'all' ? `No ${filter} guests` : 'No guests yet'}
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-4">
              {filter !== 'all'
                ? 'Try a different filter, or add a new guest.'
                : 'Add your first guest to start tracking RSVPs.'}
            </p>
            <AddGuestDialog weddingId={activeId} />
          </CardContent>
        </Card>
      ) : filteredGuests.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-sm text-[var(--color-text-muted)]">
              No guests match your search.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="p-0">
            <VirtualizedGuestRows
              guests={filteredGuests}
              onEdit={setEditing}
              onDelete={setDeleting}
            />
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
