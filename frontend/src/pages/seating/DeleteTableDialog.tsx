import { useMutation, useQueryClient } from '@tanstack/react-query'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { WeddingTableWithGuests } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  table: WeddingTableWithGuests | null
  onClose: () => void
}

export function DeleteTableDialog({ weddingId, table, onClose }: Props) {
  const qc = useQueryClient()
  const guestCount = table?.guests?.length ?? 0

  const mutation = useMutation({
    mutationFn: () => {
      if (!table) throw new Error('No table')
      return api.tables.delete(weddingId, table.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.tables.all(weddingId) })
      qc.invalidateQueries({ queryKey: queryKeys.guests.all(weddingId) })
      onClose()
    },
  })

  return (
    <AlertDialog open={!!table} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete Table {table?.table_number}?</AlertDialogTitle>
          <AlertDialogDescription>
            {guestCount > 0 ? (
              <>
                Table {table?.table_number} has <strong>{guestCount} guest{guestCount !== 1 ? 's' : ''}</strong> assigned.
                They'll be moved to unassigned. This can't be undone.
              </>
            ) : (
              "This table will be permanently deleted. This can't be undone."
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {mutation.isPending ? 'Deleting…' : 'Delete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
