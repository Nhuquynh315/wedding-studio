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
  expenseSchema,
  expenseToPayload,
  type ExpenseFormValues,
} from '@/pages/budget/budgetSchema'
import type { BudgetCategoryPublic, ExpensePublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  categories: BudgetCategoryPublic[]
  trigger?: ReactNode
  expense?: ExpensePublic | null
  onClose?: () => void
}

export function ExpenseDialog({ weddingId, categories, trigger, expense, onClose }: Props) {
  const isEditing = !!expense && !!onClose
  const [internalOpen, setInternalOpen] = useState(false)
  const open = isEditing ? !!expense : internalOpen

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
    watch,
  } = useForm<ExpenseFormValues>({
    resolver: zodResolver(expenseSchema),
    defaultValues: {
      category_id: expense?.category_id ?? '',
      title: expense?.title ?? '',
      estimated_cost: expense?.estimated_cost ?? '',
      actual_cost: expense?.actual_cost ?? '',
      is_paid: expense?.is_paid ?? false,
      paid_date: expense?.paid_date ?? '',
      due_date: expense?.due_date ?? '',
      notes: expense?.notes ?? '',
    },
  })

  const isPaid = watch('is_paid')

  const mutation = useMutation({
    mutationFn: (values: ExpenseFormValues) => {
      const payload = expenseToPayload(values)
      if (expense) {
        return api.budget.updateExpense(weddingId, expense.id, payload)
      }
      return api.budget.createExpense(weddingId, payload)
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
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle className="font-serif text-xl">
            {expense ? 'Edit expense' : 'Add expense'}
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
            <Label htmlFor="exp-category">Category *</Label>
            <select
              id="exp-category"
              {...register('category_id')}
              className="w-full h-9 rounded-md border border-[var(--color-border-default)] bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)]"
              aria-invalid={!!errors.category_id}
            >
              <option value="">Select a category</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
            {errors.category_id && (
              <p className="text-sm text-red-600">{errors.category_id.message as string}</p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="exp-title">Title *</Label>
            <Input id="exp-title" autoFocus {...register('title')} />
            {errors.title && <p className="text-sm text-red-600">{errors.title.message}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="exp-estimated">Estimated (AUD)</Label>
              <Input id="exp-estimated" type="number" min="0" step="0.01" {...register('estimated_cost')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="exp-actual">Actual (AUD)</Label>
              <Input id="exp-actual" type="number" min="0" step="0.01" {...register('actual_cost')} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="exp-due">Due date</Label>
              <Input id="exp-due" type="date" {...register('due_date')} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="exp-paid-date">Paid date</Label>
              <Input id="exp-paid-date" type="date" {...register('paid_date')} disabled={!isPaid} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input
              id="exp-is-paid"
              type="checkbox"
              {...register('is_paid')}
              className="h-4 w-4 rounded border-[var(--color-border-default)] accent-[var(--color-rose)]"
            />
            <Label htmlFor="exp-is-paid" className="cursor-pointer">
              Mark as paid
            </Label>
          </div>

          <div className="space-y-2">
            <Label htmlFor="exp-notes">Notes</Label>
            <textarea
              id="exp-notes"
              {...register('notes')}
              rows={2}
              className="w-full rounded-md border border-[var(--color-border-default)] bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] resize-none"
              placeholder="Optional notes…"
            />
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
              {mutation.isPending ? 'Saving…' : expense ? 'Save changes' : 'Add expense'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
