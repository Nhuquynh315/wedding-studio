import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  DndContext,
  KeyboardSensor,
  PointerSensor,
  closestCenter,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import { Plus, Users } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { QueryErrorState } from '@/components/QueryErrorState'
import { DeleteTableDialog } from '@/pages/seating/DeleteTableDialog'
import { DroppableZone } from '@/pages/seating/DroppableZone'
import { TableCard } from '@/pages/seating/TableCard'
import { TableDialog } from '@/pages/seating/TableDialog'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { GuestPublic, WeddingTablePublic, WeddingTableWithGuests } from '@/lib/api-schemas'

export function SeatingPage() {
  const { activeId, isLoading: weddingsLoading } = useActiveWedding()
  const [editingTable, setEditingTable] = useState<WeddingTablePublic | null>(null)
  const [deletingTable, setDeletingTable] = useState<WeddingTableWithGuests | null>(null)
  const qc = useQueryClient()

  const tablesQuery = useQuery({
    queryKey: queryKeys.tables.withGuests(activeId ?? -1),
    queryFn: () => api.tables.listWithGuests(activeId!),
    enabled: !!activeId,
  })

  const allGuestsQuery = useQuery({
    queryKey: queryKeys.guests.list(activeId ?? -1, { limit: 200 }),
    queryFn: () => api.guests.list(activeId!, { limit: 200 }),
    enabled: !!activeId,
  })

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 8 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  )

  const assignMutation = useMutation({
    mutationFn: ({ guestId, tableId }: { guestId: number; tableId: number | null }) =>
      api.guests.update(activeId!, guestId, { table_id: tableId }),

    onMutate: async ({ guestId, tableId }) => {
      await qc.cancelQueries({ queryKey: queryKeys.tables.all(activeId!) })
      await qc.cancelQueries({ queryKey: queryKeys.guests.all(activeId!) })

      const prevTables = qc.getQueryData<WeddingTableWithGuests[]>(
        queryKeys.tables.withGuests(activeId!),
      )
      const prevGuests = qc.getQueriesData<{ items: GuestPublic[] }>({
        queryKey: queryKeys.guests.all(activeId!),
      })

      // Optimistic update for tables-with-guests
      qc.setQueryData<WeddingTableWithGuests[]>(
        queryKeys.tables.withGuests(activeId!),
        (old) => {
          if (!old) return old
          let movingGuest: GuestPublic | null = null
          const cleared = old.map((t) => {
            const found = t.guests?.find((g) => g.id === guestId)
            if (found) movingGuest = found
            return { ...t, guests: t.guests?.filter((g) => g.id !== guestId) ?? [] }
          })
          // Fallback: find guest in the all-guests cache
          if (!movingGuest) {
            const allGuests = qc.getQueryData<{ items: GuestPublic[] }>(
              queryKeys.guests.list(activeId!, { limit: 200 }),
            )
            movingGuest = allGuests?.items.find((g) => g.id === guestId) ?? null
          }
          if (!movingGuest) return cleared
          if (tableId !== null) {
            return cleared.map((t) =>
              t.id === tableId
                ? { ...t, guests: [...(t.guests ?? []), { ...movingGuest!, table_id: tableId }] }
                : t,
            )
          }
          return cleared
        },
      )

      // Optimistic update for all-guests (unassigned pool)
      qc.setQueriesData<{ items: GuestPublic[] }>(
        { queryKey: queryKeys.guests.all(activeId!) },
        (old) => {
          if (!old?.items) return old
          return {
            ...old,
            items: old.items.map((g) => (g.id === guestId ? { ...g, table_id: tableId } : g)),
          }
        },
      )

      return { prevTables, prevGuests }
    },

    onError: (_err, _vars, context) => {
      if (context?.prevTables) {
        qc.setQueryData(queryKeys.tables.withGuests(activeId!), context.prevTables)
      }
      if (context?.prevGuests) {
        context.prevGuests.forEach(([key, data]) => qc.setQueryData(key, data))
      }
    },

    onSettled: () => {
      qc.invalidateQueries({ queryKey: queryKeys.tables.all(activeId!) })
      qc.invalidateQueries({ queryKey: queryKeys.guests.all(activeId!) })
    },
  })

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event
    if (!over) return

    const guestData = active.data.current as
      | { type: string; guest: GuestPublic; containerId: string }
      | undefined
    if (!guestData || guestData.type !== 'guest') return

    const sourceContainer = guestData.containerId
    const overData = over.data.current as { type?: string; containerId?: string } | undefined
    const targetContainer =
      overData?.type === 'guest' ? overData.containerId : (over.id as string)

    if (!targetContainer || targetContainer === sourceContainer) return

    const newTableId =
      targetContainer === 'unassigned' ? null : Number(targetContainer.replace('table-', ''))

    assignMutation.mutate({ guestId: guestData.guest.id, tableId: newTableId })
  }

  if (weddingsLoading || !activeId) {
    return (
      <div className="p-8">
        <Skeleton className="h-96" />
      </div>
    )
  }

  if (tablesQuery.isError || allGuestsQuery.isError) {
    const err = tablesQuery.error ?? allGuestsQuery.error
    const retry = () => {
      tablesQuery.refetch()
      allGuestsQuery.refetch()
    }
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <QueryErrorState error={err} onRetry={retry} resourceName="seating data" />
      </div>
    )
  }

  if (tablesQuery.isLoading || allGuestsQuery.isLoading) {
    return (
      <div className="p-8 max-w-7xl mx-auto">
        <Skeleton className="h-8 w-32 mb-6" />
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <Skeleton className="h-96 lg:col-span-1" />
          <Skeleton className="h-96 lg:col-span-3" />
        </div>
      </div>
    )
  }

  const tables = tablesQuery.data ?? []
  const allGuests = allGuestsQuery.data?.items ?? []
  const unassignedGuests = allGuests.filter((g) => g.table_id == null)
  const totalAssigned = allGuests.length - unassignedGuests.length

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="font-serif text-3xl">Seating</h1>
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            {totalAssigned} of {allGuests.length} guests seated · {tables.length} table
            {tables.length !== 1 ? 's' : ''}
          </p>
        </div>
        <TableDialog
          weddingId={activeId}
          trigger={
            <Button className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white">
              <Plus className="h-4 w-4 mr-1" />
              Table
            </Button>
          }
        />
      </div>

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          {/* Unassigned pool */}
          <div className="lg:col-span-1">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Users className="h-4 w-4 text-[var(--color-text-muted)]" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-[var(--color-text-muted)]">
                    Unassigned ({unassignedGuests.length})
                  </h2>
                </div>
                <DroppableZone
                  id="unassigned"
                  guests={unassignedGuests}
                  emptyMessage="All guests seated"
                />
              </CardContent>
            </Card>
          </div>

          {/* Tables grid */}
          <div className="lg:col-span-3">
            {tables.length === 0 ? (
              <Card>
                <CardContent className="p-12 text-center">
                  <h2 className="font-serif text-xl mb-1">No tables yet</h2>
                  <p className="text-sm text-[var(--color-text-muted)] mb-4">
                    Create your first table to start arranging seating.
                  </p>
                  <TableDialog
                    weddingId={activeId}
                    trigger={
                      <Button className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white">
                        Create first table
                      </Button>
                    }
                  />
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {tables.map((t) => (
                  <TableCard
                    key={t.id}
                    table={t}
                    onEdit={() => setEditingTable(t)}
                    onDelete={() => setDeletingTable(t)}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </DndContext>

      <TableDialog
        weddingId={activeId}
        table={editingTable}
        onClose={() => setEditingTable(null)}
      />
      <DeleteTableDialog
        weddingId={activeId}
        table={deletingTable}
        onClose={() => setDeletingTable(null)}
      />
    </div>
  )
}
