import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Briefcase } from 'lucide-react'

import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { AddVendorDialog } from '@/pages/vendors/AddVendorDialog'
import { DeleteVendorDialog } from '@/pages/vendors/DeleteVendorDialog'
import { EditVendorDialog } from '@/pages/vendors/EditVendorDialog'
import { VendorCard } from '@/pages/vendors/VendorCard'
import { VendorStatusFilter } from '@/pages/vendors/VendorStatusFilter'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { useUrlState } from '@/hooks/useUrlState'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { VendorPublic, VendorStatus } from '@/lib/api-schemas'

type FilterValue = VendorStatus | 'all'
const VALID_STATUSES: VendorStatus[] = ['considering', 'booked', 'rejected', 'backup']

function isFilterValue(v: string | null): v is FilterValue {
  return v === 'all' || (v !== null && VALID_STATUSES.includes(v as VendorStatus))
}

export function VendorsPage() {
  const { activeId, isLoading: weddingsLoading } = useActiveWedding()
  const [editing, setEditing] = useState<VendorPublic | null>(null)
  const [deleting, setDeleting] = useState<VendorPublic | null>(null)

  const [filterParam, setFilterParam] = useUrlState('status')
  const filter: FilterValue = isFilterValue(filterParam) ? filterParam : 'all'

  const statusForApi: VendorStatus | undefined = filter === 'all' ? undefined : filter

  const vendorsQuery = useQuery({
    queryKey: queryKeys.vendors.list(activeId ?? -1, statusForApi),
    queryFn: () => api.vendors.list(activeId!, statusForApi),
    enabled: !!activeId,
  })

  if (weddingsLoading || !activeId) {
    return (
      <div className="p-8">
        <Skeleton className="h-96" />
      </div>
    )
  }

  const vendors = vendorsQuery.data ?? []

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="font-serif text-3xl">Vendors</h1>
        <AddVendorDialog weddingId={activeId} />
      </div>

      <div className="mb-6">
        <VendorStatusFilter
          value={filter}
          onChange={(v) => setFilterParam(v === 'all' ? null : v)}
        />
      </div>

      {vendorsQuery.isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      ) : vendors.length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Briefcase className="h-10 w-10 text-[var(--color-rose)] mx-auto mb-3" />
            <h2 className="font-serif text-xl mb-1">
              {filter !== 'all' ? `No ${filter} vendors` : 'No vendors yet'}
            </h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-4">
              {filter !== 'all'
                ? 'Try a different filter, or add a new vendor.'
                : 'Add your first vendor to start tracking quotes, contracts, and payments.'}
            </p>
            <AddVendorDialog weddingId={activeId} />
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vendors.map((v) => (
            <VendorCard
              key={v.id}
              vendor={v}
              onEdit={() => setEditing(v)}
              onDelete={() => setDeleting(v)}
            />
          ))}
        </div>
      )}

      <EditVendorDialog
        weddingId={activeId}
        vendor={editing}
        onClose={() => setEditing(null)}
      />
      <DeleteVendorDialog
        weddingId={activeId}
        vendor={deleting}
        onClose={() => setDeleting(null)}
      />
    </div>
  )
}
