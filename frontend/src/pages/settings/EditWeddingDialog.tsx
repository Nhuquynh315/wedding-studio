import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQueryClient } from '@tanstack/react-query'

import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'
import {
  WEDDING_STYLES,
  weddingSchema,
  type WeddingFormValues,
  type WeddingFormOutput,
} from '@/pages/dashboard/weddingSchema'
import type { WeddingPublic } from '@/lib/api-schemas'

type Props = {
  wedding: WeddingPublic | null
  onClose: () => void
}

export function EditWeddingDialog({ wedding, onClose }: Props) {
  const qc = useQueryClient()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WeddingFormValues>({
    resolver: zodResolver(weddingSchema),
    values: wedding
      ? {
          partner1_name: wedding.partner1_name,
          partner2_name: wedding.partner2_name,
          wedding_date: wedding.wedding_date ?? '',
          location: wedding.location ?? '',
          venue_name: wedding.venue_name ?? '',
          style: (wedding.style as WeddingFormValues['style']) ?? 'rustic',
          total_budget: wedding.total_budget != null ? String(wedding.total_budget) : '',
        }
      : undefined,
  })

  const mutation = useMutation({
    mutationFn: (values: WeddingFormOutput) =>
      api.weddings.update(wedding!.id, {
        partner1_name: values.partner1_name,
        partner2_name: values.partner2_name,
        wedding_date: values.wedding_date,
        location: values.location,
        venue_name: values.venue_name,
        style: values.style,
        total_budget: values.total_budget,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.weddings.all() })
      reset()
      setServerError(null)
      onClose()
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      setServerError(msg)
    },
  })

  function handleClose() {
    reset()
    setServerError(null)
    onClose()
  }

  return (
    <Dialog open={!!wedding} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">Edit wedding</DialogTitle>
        </DialogHeader>

        <form
          onSubmit={handleSubmit((v) => mutation.mutate(v as unknown as WeddingFormOutput))}
          className="space-y-4 mt-2"
        >
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="edit-partner1_name">Partner 1</Label>
              <Input
                id="edit-partner1_name"
                {...register('partner1_name')}
                aria-invalid={!!errors.partner1_name}
              />
              {errors.partner1_name && (
                <p className="text-xs text-red-600">{errors.partner1_name.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="edit-partner2_name">Partner 2</Label>
              <Input
                id="edit-partner2_name"
                {...register('partner2_name')}
                aria-invalid={!!errors.partner2_name}
              />
              {errors.partner2_name && (
                <p className="text-xs text-red-600">{errors.partner2_name.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-wedding_date">Wedding date</Label>
            <Input
              id="edit-wedding_date"
              type="date"
              {...register('wedding_date')}
              aria-invalid={!!errors.wedding_date}
            />
            {errors.wedding_date && (
              <p className="text-xs text-red-600">{errors.wedding_date.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-location">Location</Label>
            <Input
              id="edit-location"
              {...register('location')}
              aria-invalid={!!errors.location}
            />
            {errors.location && (
              <p className="text-xs text-red-600">{errors.location.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-venue_name">Venue</Label>
            <Input
              id="edit-venue_name"
              {...register('venue_name')}
              aria-invalid={!!errors.venue_name}
            />
            {errors.venue_name && (
              <p className="text-xs text-red-600">{errors.venue_name.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="edit-style">Style</Label>
              <select
                id="edit-style"
                {...register('style')}
                className="w-full h-9 rounded-md border border-[var(--color-border-default)] bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] capitalize"
                aria-invalid={!!errors.style}
              >
                {WEDDING_STYLES.map((s) => (
                  <option key={s} value={s} className="capitalize">
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
              {errors.style && (
                <p className="text-xs text-red-600">{errors.style.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="edit-total_budget">Total budget (optional)</Label>
              <Input
                id="edit-total_budget"
                type="number"
                min="0"
                step="1000"
                placeholder="30000"
                {...register('total_budget')}
                aria-invalid={!!errors.total_budget}
              />
              {errors.total_budget && (
                <p className="text-xs text-red-600">{errors.total_budget.message}</p>
              )}
            </div>
          </div>

          {serverError && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
              {serverError}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={isSubmitting || mutation.isPending}
              className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
            >
              {mutation.isPending ? 'Saving…' : 'Save changes'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
