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
import type { WeddingPublic } from '@/lib/api-schemas'

type Props = {
  wedding: WeddingPublic | null
  onClose: () => void
}

export function DeleteWeddingDialog({ wedding, onClose }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => {
      if (!wedding) throw new Error('No wedding')
      return api.weddings.delete(wedding.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.weddings.all() })
      const activeStored = localStorage.getItem('active_wedding_id')
      if (activeStored && Number(activeStored) === wedding!.id) {
        localStorage.removeItem('active_wedding_id')
      }
      onClose()
    },
  })

  return (
    <AlertDialog open={!!wedding} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this wedding?</AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div>
              <strong>{wedding?.partner1_name} &amp; {wedding?.partner2_name}</strong>
              {' '}and ALL its data — guests, budget categories, expenses, vendors,
              checklist, tables — will be permanently deleted. This{" can't"} be undone.
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="bg-red-600 hover:bg-red-700 text-white"
          >
            {mutation.isPending ? 'Deleting…' : 'Delete wedding'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
