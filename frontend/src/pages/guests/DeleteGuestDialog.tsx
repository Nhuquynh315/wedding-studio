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
import type { GuestPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  guest: GuestPublic | null
  onClose: () => void
}

export function DeleteGuestDialog({ weddingId, guest, onClose }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => {
      if (!guest) throw new Error('No guest to delete')
      return api.guests.delete(weddingId, guest.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.guests.all(weddingId) })
      onClose()
    },
  })

  return (
    <AlertDialog open={!!guest} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this guest?</AlertDialogTitle>
          <AlertDialogDescription>
            {guest?.full_name} will be permanently removed. This can't be undone.
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
