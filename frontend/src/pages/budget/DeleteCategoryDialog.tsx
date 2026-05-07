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
import type { BudgetCategoryPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  category: BudgetCategoryPublic | null
  onClose: () => void
}

export function DeleteCategoryDialog({ weddingId, category, onClose }: Props) {
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => {
      if (!category) throw new Error('No category')
      return api.budget.deleteCategory(weddingId, category.id)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.budget.all(weddingId) })
      onClose()
    },
  })

  return (
    <AlertDialog open={!!category} onOpenChange={(o) => !o && onClose()}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Delete this category?</AlertDialogTitle>
          <AlertDialogDescription>
            <strong>{category?.name}</strong> will be deleted along with all its expenses. This
            can't be undone.
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
