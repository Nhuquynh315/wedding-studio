import { z } from 'zod'

export const WEDDING_STYLES = [
  'rustic',
  'modern',
  'luxury',
  'beach',
  'vintage',
  'minimalist',
] as const

export const weddingSchema = z.object({
  partner1_name: z.string().min(1, 'Required').max(120, 'Max 120 characters'),
  partner2_name: z.string().min(1, 'Required').max(120, 'Max 120 characters'),
  wedding_date: z.string().min(1, 'Required'),
  location: z.string().min(1, 'Required').max(255, 'Max 255 characters'),
  venue_name: z.string().min(1, 'Required').max(255, 'Max 255 characters'),
  style: z.enum(WEDDING_STYLES, { message: 'Select a style' }),
  total_budget: z.preprocess(
    (v) => (v === '' || v === undefined || v === null ? null : Number(v)),
    z.number().min(0, 'Must be 0 or greater').nullable(),
  ),
})

export type WeddingFormValues = z.input<typeof weddingSchema>
export type WeddingFormOutput = z.output<typeof weddingSchema>
