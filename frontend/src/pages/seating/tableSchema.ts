import { z } from 'zod'

// Backend stores shape as a free string — these are the documented valid values.
export const TABLE_SHAPES = ['round', 'rectangle', 'square', 'long'] as const

export const tableSchema = z.object({
  table_number: z
    .union([z.string(), z.number()])
    .refine((v) => v !== '' && !isNaN(Number(v)) && Number(v) > 0, {
      message: 'Table number must be a positive integer',
    }),
  table_name: z.string().max(100).optional().or(z.literal('')),
  capacity: z
    .union([z.string(), z.number()])
    .refine((v) => v !== '' && !isNaN(Number(v)) && Number(v) >= 1 && Number(v) <= 100, {
      message: 'Capacity must be 1–100',
    }),
  shape: z.enum(TABLE_SHAPES),
  notes: z.string().optional().or(z.literal('')),
})

export type TableFormValues = z.infer<typeof tableSchema>

export function tableToPayload(values: TableFormValues) {
  const blank = (s: string | undefined) => (s && s.trim() ? s.trim() : null)
  return {
    table_number: Number(values.table_number),
    table_name: blank(values.table_name),
    capacity: Number(values.capacity),
    shape: values.shape,
    notes: blank(values.notes),
  }
}
