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
import type { ExpensePublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  expense: ExpensePublic | null
  onClose: () => void
}

export function DeleteExpenseDialog({ weddingId, expense, onClose }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => {
      if (!expense) throw new Error('No expense')
      return api.budget.deleteExpense(weddingId, expense.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.budget.all(weddingId) })
      onClose()
    },
  })

  return (
    <AlertDialog open={!!expense} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this expense?</AlertDialogTitle>
          <AlertDialogDescription>
            <strong>{expense?.title}</strong> will be permanently deleted. This can't be undone.
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
