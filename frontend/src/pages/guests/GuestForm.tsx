import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { guestSchema, formToPayload, type GuestFormValues } from '@/pages/guests/guestSchema'
import type { GuestPublic } from '@/lib/api-schemas'

type Props = {
  initial?: GuestPublic
  onSubmit: (payload: ReturnType<typeof formToPayload>) => Promise<void>
  onCancel: () => void
  submitLabel?: string
  isSubmitting?: boolean
}

export function GuestForm({
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
  } = useForm<GuestFormValues>({
    resolver: zodResolver(guestSchema),
    defaultValues: {
      full_name: initial?.full_name ?? '',
      email: initial?.email ?? '',
      phone: initial?.phone ?? '',
      group_name: initial?.group_name ?? '',
      meal_preference: initial?.meal_preference ?? '',
      rsvp_status: initial?.rsvp_status ?? 'pending',
    },
  })

  const onValidSubmit = async (values: GuestFormValues) => {
    await onSubmit(formToPayload(values))
  }

  return (
    <form onSubmit={handleSubmit(onValidSubmit)} className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="full_name">Name *</Label>
        <Input
          id="full_name"
          autoFocus
          {...register('full_name')}
          aria-invalid={!!errors.full_name}
        />
        {errors.full_name && (
          <p className="text-sm text-red-600">{errors.full_name.message}</p>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" type="email" {...register('email')} />
          {errors.email && (
            <p className="text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="phone">Phone</Label>
          <Input id="phone" {...register('phone')} />
          {errors.phone && (
            <p className="text-sm text-red-600">{errors.phone.message}</p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-2">
          <Label htmlFor="group_name">Group</Label>
          <Input
            id="group_name"
            placeholder="Smith Family"
            {...register('group_name')}
          />
          {errors.group_name && (
            <p className="text-sm text-red-600">{errors.group_name.message}</p>
          )}
        </div>
        <div className="space-y-2">
          <Label htmlFor="meal_preference">Meal</Label>
          <Input
            id="meal_preference"
            placeholder="Vegetarian"
            {...register('meal_preference')}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="rsvp_status">RSVP</Label>
        <select
          id="rsvp_status"
          {...register('rsvp_status')}
          className="w-full px-3 py-2 border border-[var(--color-border-default)] rounded-md focus:outline-none focus:border-[var(--color-rose)]"
        >
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="declined">Declined</option>
        </select>
      </div>

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
