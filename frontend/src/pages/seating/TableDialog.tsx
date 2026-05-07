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
import { TABLE_SHAPES, tableSchema, tableToPayload, type TableFormValues } from '@/pages/seating/tableSchema'
import type { WeddingTablePublic } from '@/lib/api-schemas'

type Props = {
  weddingId: number
  trigger?: ReactNode
  table?: WeddingTablePublic | null
  onClose?: () => void
}

export function TableDialog({ weddingId, trigger, table, onClose }: Props) {
  const isEditing = !!table && !!onClose
  const [internalOpen, setInternalOpen] = useState(false)
  const open = isEditing ? !!table : internalOpen

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
  } = useForm<TableFormValues>({
    resolver: zodResolver(tableSchema),
    defaultValues: {
      table_number: table?.table_number ?? '',
      table_name: table?.table_name ?? '',
      capacity: table?.capacity ?? 8,
      shape: (table?.shape as TableFormValues['shape']) ?? 'round',
      notes: table?.notes ?? '',
    },
  })

  const mutation = useMutation({
    mutationFn: (values: TableFormValues) => {
      const payload = tableToPayload(values)
      if (table) return api.tables.update(weddingId, table.id, payload)
      return api.tables.create(weddingId, payload)
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.tables.all(weddingId) })
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
            {table ? 'Edit table' : 'Add table'}
          </DialogTitle>
        </DialogHeader>

        {submitError && (
          <div role="alert" className="text-sm text-red-700 bg-red-50 border border-red-200 rounded p-2">
            {submitError}
          </div>
        )}

        <form onSubmit={handleSubmit((v) => mutation.mutate(v))} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="tbl-number">Table number *</Label>
              <Input id="tbl-number" type="number" min="1" autoFocus {...register('table_number')} />
              {errors.table_number && (
                <p className="text-sm text-red-600">{errors.table_number.message as string}</p>
              )}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="tbl-capacity">Capacity *</Label>
              <Input id="tbl-capacity" type="number" min="1" max="100" {...register('capacity')} />
              {errors.capacity && (
                <p className="text-sm text-red-600">{errors.capacity.message as string}</p>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tbl-name">Table name (optional)</Label>
            <Input id="tbl-name" placeholder="Head Table" {...register('table_name')} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tbl-shape">Shape</Label>
            <select
              id="tbl-shape"
              {...register('shape')}
              className="w-full h-9 rounded-md border border-[var(--color-border-default)] bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] capitalize"
            >
              {TABLE_SHAPES.map((s) => (
                <option key={s} value={s} className="capitalize">
                  {s.charAt(0).toUpperCase() + s.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="tbl-notes">Notes</Label>
            <textarea
              id="tbl-notes"
              {...register('notes')}
              rows={2}
              className="w-full rounded-md border border-[var(--color-border-default)] bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] resize-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => setOpen(false)} disabled={mutation.isPending}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={mutation.isPending}
              className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
            >
              {mutation.isPending ? 'Saving…' : table ? 'Save changes' : 'Add table'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
