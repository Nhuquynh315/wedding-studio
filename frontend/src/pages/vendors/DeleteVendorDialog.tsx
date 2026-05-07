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
import type { VendorPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  vendor: VendorPublic | null
  onClose: () => void
}

export function DeleteVendorDialog({ weddingId, vendor, onClose }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => {
      if (!vendor) throw new Error('No vendor')
      return api.vendors.delete(weddingId, vendor.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.vendors.all(weddingId) })
      onClose()
    },
  })

  return (
    <AlertDialog open={!!vendor} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this vendor?</AlertDialogTitle>
          <AlertDialogDescription>
            <strong>{vendor?.business_name}</strong> will be permanently deleted. Any expenses
            linked to this vendor will have their vendor reference cleared. This can't be undone.
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
