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
} from './weddingSchema'

const DEFAULT_PRIMARY = '#c9687a'
const DEFAULT_SECONDARY = '#a8566a'

type Props = {
  open: boolean
  onClose: () => void
  onCreated: (id: number) => void
}

export function CreateWeddingDialog({ open, onClose, onCreated }: Props) {
  const queryClient = useQueryClient()
  const [serverError, setServerError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<WeddingFormValues>({
    resolver: zodResolver(weddingSchema),
    defaultValues: { style: 'rustic' },
  })

  const mutation = useMutation({
    mutationFn: (values: WeddingFormOutput) =>
      api.weddings.create({
        partner1_name: values.partner1_name,
        partner2_name: values.partner2_name,
        wedding_date: values.wedding_date,
        location: values.location,
        venue_name: values.venue_name,
        style: values.style,
        primary_color: DEFAULT_PRIMARY,
        secondary_color: DEFAULT_SECONDARY,
        total_budget: values.total_budget,
      }),
    onSuccess: (wedding) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.weddings.all() })
      reset()
      setServerError(null)
      onCreated(wedding.id)
    },
    onError: (err: unknown) => {
      const msg =
        err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      setServerError(msg)
    },
  })

  function handleClose() {
    reset()
    setServerError(null)
    onClose()
  }

  return (
    <Dialog open={open} onOpenChange={(o) => !o && handleClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="font-serif text-2xl">Create your wedding</DialogTitle>
        </DialogHeader>

        <form
          onSubmit={handleSubmit((v) => mutation.mutate(v as unknown as WeddingFormOutput))}
          className="space-y-4 mt-2"
        >
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="partner1_name">Partner 1</Label>
              <Input
                id="partner1_name"
                placeholder="Alex"
                {...register('partner1_name')}
                aria-invalid={!!errors.partner1_name}
              />
              {errors.partner1_name && (
                <p className="text-xs text-red-600">{errors.partner1_name.message}</p>
              )}
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="partner2_name">Partner 2</Label>
              <Input
                id="partner2_name"
                placeholder="Jordan"
                {...register('partner2_name')}
                aria-invalid={!!errors.partner2_name}
              />
              {errors.partner2_name && (
                <p className="text-xs text-red-600">{errors.partner2_name.message}</p>
              )}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="wedding_date">Wedding date</Label>
            <Input
              id="wedding_date"
              type="date"
              {...register('wedding_date')}
              aria-invalid={!!errors.wedding_date}
            />
            {errors.wedding_date && (
              <p className="text-xs text-red-600">{errors.wedding_date.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="location">Location</Label>
            <Input
              id="location"
              placeholder="Melbourne, VIC"
              {...register('location')}
              aria-invalid={!!errors.location}
            />
            {errors.location && (
              <p className="text-xs text-red-600">{errors.location.message}</p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="venue_name">Venue</Label>
            <Input
              id="venue_name"
              placeholder="The Grand Ballroom"
              {...register('venue_name')}
              aria-invalid={!!errors.venue_name}
            />
            {errors.venue_name && (
              <p className="text-xs text-red-600">{errors.venue_name.message}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="style">Style</Label>
              <select
                id="style"
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
              <Label htmlFor="total_budget">Total budget (optional)</Label>
              <Input
                id="total_budget"
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
              {mutation.isPending ? 'Creating…' : 'Create wedding'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
