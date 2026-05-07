import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  CHECKLIST_CATEGORIES,
  CHECKLIST_PRIORITIES,
  checklistSchema,
  checklistToPayload,
  type ChecklistFormValues,
} from '@/pages/checklist/checklistSchema'
import type { ChecklistItemPublic } from '@/lib/api-schemas'

type Props = {
  initial?: ChecklistItemPublic
  onSubmit: (payload: ReturnType<typeof checklistToPayload>) => Promise<void>
  onCancel: () => void
  submitLabel?: string
  isSubmitting?: boolean
}

export function ChecklistForm({
  initial,
  onSubmit,
  onCancel,
  submitLabel = 'Save',
  isSubmitting = false,
}: Props) {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ChecklistFormValues>({
    resolver: zodResolver(checklistSchema),
    defaultValues: {
      title: initial?.title ?? '',
      category: initial?.category ?? 'Other',
      priority: initial?.priority ?? 'medium',
      due_date: initial?.due_date ?? '',
      notes: initial?.notes ?? '',
      is_completed: initial?.is_completed ?? false,
    },
  })

  return (
    <form
      onSubmit={handleSubmit((v) => onSubmit(checklistToPayload(v)))}
      className="space-y-4"
    >
      <div className="space-y-1.5">
        <Label htmlFor="cl-title">Title *</Label>
        <Input id="cl-title" autoFocus {...register('title')} />
        {errors.title && <p className="text-sm text-red-600">{errors.title.message}</p>}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="cl-category">Category</Label>
          <select
            id="cl-category"
            {...register('category')}
            className="w-full h-9 rounded-md border border-[var(--color-border-default)] bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)]"
          >
            {CHECKLIST_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="cl-priority">Priority</Label>
          <select
            id="cl-priority"
            {...register('priority')}
            className="w-full h-9 rounded-md border border-[var(--color-border-default)] bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] capitalize"
          >
            {CHECKLIST_PRIORITIES.map((p) => (
              <option key={p} value={p} className="capitalize">
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="cl-due_date">Due date</Label>
        <Input id="cl-due_date" type="date" {...register('due_date')} />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="cl-notes">Notes</Label>
        <textarea
          id="cl-notes"
          {...register('notes')}
          rows={3}
          className="w-full rounded-md border border-[var(--color-border-default)] bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] resize-none"
          placeholder="Optional notes…"
        />
      </div>

      <label className="flex items-center gap-2 text-sm cursor-pointer">
        <input
          type="checkbox"
          {...register('is_completed')}
          className="h-4 w-4 rounded accent-[var(--color-rose)]"
        />
        Mark as completed
      </label>

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isSubmitting}>
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting}
          className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
        >
          {isSubmitting ? 'Saving…' : submitLabel}
        </Button>
      </div>
    </form>
  )
}
