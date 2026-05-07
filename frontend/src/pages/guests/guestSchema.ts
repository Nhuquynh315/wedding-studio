import { z } from 'zod'

export const guestSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(200, 'Name is too long'),
  email: z.string().email('Please enter a valid email').optional().or(z.literal('')),
  phone: z.string().max(50, 'Phone is too long').optional().or(z.literal('')),
  group_name: z.string().max(100, 'Group name is too long').optional().or(z.literal('')),
  meal_preference: z.string().max(100, 'Too long').optional().or(z.literal('')),
  rsvp_status: z.enum(['pending', 'confirmed', 'declined']),
})

export type GuestFormValues = z.infer<typeof guestSchema>

export function formToPayload(values: GuestFormValues) {
  const blank = (s: string | undefined) => (s && s.trim() ? s.trim() : null)
  return {
    full_name: values.full_name.trim(),
    email: blank(values.email),
    phone: blank(values.phone),
    group_name: blank(values.group_name),
    meal_preference: blank(values.meal_preference),
    rsvp_status: values.rsvp_status,
  }
}
