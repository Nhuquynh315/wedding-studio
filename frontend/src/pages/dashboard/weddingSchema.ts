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
  partner1_name: z.string().min(1, 'Required'),
  partner2_name: z.string().min(1, 'Required'),
  wedding_date: z.string().min(1, 'Required'),
  location: z.string().min(1, 'Required'),
  venue_name: z.string().min(1, 'Required'),
  style: z.enum(WEDDING_STYLES, { message: 'Select a style' }),
  total_budget: z.preprocess(
    (v) => (v === '' || v === undefined || v === null ? null : Number(v)),
    z.number().positive('Must be positive').nullable(),
  ),
})

export type WeddingFormValues = z.input<typeof weddingSchema>
export type WeddingFormOutput = z.output<typeof weddingSchema>
