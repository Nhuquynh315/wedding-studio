import { useState, type ReactNode } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { ApiError, api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import {
  categorySchema,
  categoryToPayload,
  type CategoryFormValues,
} from '@/pages/budget/budgetSchema'
import type { BudgetCategoryPublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  trigger?: ReactNode
  category?: BudgetCategoryPublic | null
  onClose?: () => void
}

export function CategoryDialog({ weddingId, trigger, category, onClose }: Props) {
  const isEditing = !!category && !!onClose
  const [internalOpen, setInternalOpen] = useState(false)
  const open = isEditing ? !!category : internalOpen

  const setOpen = (v: boolean) => {
    if (isEditing) {
      if (!v) onClose?.()
    } else {
      setInternalOpen(v)
    }
  }

  const [submitError, setSubmitError] = useState<string | null>(null)
  const qc = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CategoryFormValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: {
      name: category?.name ?? '',
      allocated_amount: category?.allocated_amount ?? '',
      color: category?.color ?? '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: CategoryFormValues) => {
      const payload = categoryToPayload(values)
      if (category) {
        return api.budget.updateCategory(weddingId, category.id, payload)
      }
      return api.budget.createCategory(weddingId, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.budget.all(weddingId) })
      setOpen(false)
      setSubmitError(null)
      reset()
    },
    onError: (err) => {
      setSubmitError(
        err instanceof ApiError
          ? err.problem.detail || err.problem.title
          : 'Something went wrong',
      )
    },
  })

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      {trigger && <DialogTrigger asChild>{trigger}</DialogTrigger>}
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">
            {category ? 'Edit category' : 'Add category'}
          </DialogTitle>
        </DialogHeader>

        {submitError && (
          <div
            role="alert"
            className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2 mb-2"
          >
            {submitError}
          </div>
        )}

        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="cat-name">Name *</Label>
            <Input id="cat-name" autoFocus {...register('name')} />
            {errors.name && <p className="text-sm text-red-600">{errors.name.message}</p>}
          </div>

          <div className="space-y-2">
            <Label htmlFor="cat-allocated">Allocated amount (AUD) *</Label>
            <Input
              id="cat-allocated"
              type="number"
              min="0"
              step="100"
              {...register('allocated_amount')}
            />
            {errors.allocated_amount && (
              <p className="text-sm text-red-600">
                {errors.allocated_amount.message as string}
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="cat-color">Color (hex, optional)</Label>
            <Input id="cat-color" placeholder="#c9687a" {...register('color')} />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={mutation.isPending}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={mutation.isPending}
              className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
            >
              {mutation.isPending ? 'Saving…' : category ? 'Save changes' : 'Add category'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
