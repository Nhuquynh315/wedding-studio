import { useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckCircle2 } from 'lucide-react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import type { ChecklistCategory } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  category: ChecklistCategory
  openItemCount: number
}

export function BulkCompleteDialog({ weddingId, category, openItemCount }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () =>
      api.checklist.bulkComplete(weddingId, { category, completed: true }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.checklist.all(weddingId) })
    },
  })

  if (openItemCount === 0) return null

  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="outline" size="sm">
          <CheckCircle2 className="h-4 w-4 mr-1" />
          Mark all {category} as done
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Mark all {category} items complete?</AlertDialogTitle>
          <AlertDialogDescription>
            {openItemCount} open item{openItemCount !== 1 ? 's' : ''} in{' '}
            <strong>{category}</strong> will be marked as done.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={mutation.isPending}>Cancel</AlertDialogCancel>
          <AlertDialogAction
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
          >
            {mutation.isPending ? 'Updating…' : 'Mark complete'}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
