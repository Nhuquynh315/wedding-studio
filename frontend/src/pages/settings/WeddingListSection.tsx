import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Pencil, Plus, Trash2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { CreateWeddingDialog } from '@/pages/dashboard/CreateWeddingDialog'
import { EditWeddingDialog } from '@/pages/settings/EditWeddingDialog'
import { DeleteWeddingDialog } from '@/pages/settings/DeleteWeddingDialog'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { WeddingPublic } from '@/lib/api-schemas'

export function WeddingListSection() {
  const [editing, setEditing] = useState<WeddingPublic | null>(null)
  const [deleting, setDeleting] = useState<WeddingPublic | null>(null)

  const weddingsQuery = useQuery({
    queryKey: queryKeys.weddings.list(),
    queryFn: api.weddings.list,
  })

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="font-serif text-xl">Your weddings</h2>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">
              Manage the weddings you own
            </p>
          </div>
          <CreateWeddingDialog
            trigger={
              <Button variant="outline" size="sm">
                <Plus className="h-4 w-4 mr-1" />
                New wedding
              </Button>
            }
          />
        </div>

        {weddingsQuery.isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 2 }).map((_, i) => (
              <Skeleton key={i} className="h-14" />
            ))}
          </div>
        ) : (weddingsQuery.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-[var(--color-text-muted)] py-4">
            No weddings yet. Create one to get started.
          </p>
        ) : (
          <div className="divide-y divide-[var(--color-border-default)]">
            {weddingsQuery.data?.map((w) => (
              <div key={w.id} className="flex items-center justify-between py-3 group">
                <div className="flex-1 min-w-0">
                  <div className="font-medium">
                    {w.partner1_name} &amp; {w.partner2_name}
                  </div>
                  <div className="text-xs text-[var(--color-text-muted)] mt-0.5">
                    {w.wedding_date
                      ? new Date(w.wedding_date).toLocaleDateString('en-AU', {
                          year: 'numeric',
                          month: 'long',
                          day: 'numeric',
                        })
                      : 'No date set'}
                    {w.location && ` · ${w.location}`}
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => setEditing(w)}
                    className="p-1.5 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)]"
                    aria-label="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setDeleting(w)}
                    className="p-1.5 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700"
                    aria-label="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      <EditWeddingDialog wedding={editing} onClose={() => setEditing(null)} />
      <DeleteWeddingDialog wedding={deleting} onClose={() => setDeleting(null)} />
    </Card>
  )
}
