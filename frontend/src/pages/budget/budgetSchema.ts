import { z } from 'zod'

export const categorySchema = z.object({
  name: z.string().min(1, 'Required').max(100, 'Too long'),
  allocated_amount: z
    .union([z.string(), z.number()])
    .refine((v) => v !== '' && !isNaN(Number(v)) && Number(v) >= 0, {
      message: 'Must be 0 or greater',
    }),
  color: z.string().max(20).optional().or(z.literal('')),
})

export type CategoryFormValues = z.infer<typeof categorySchema>

export function categoryToPayload(values: CategoryFormValues) {
  return {
    name: values.name.trim(),
    allocated_amount: Number(values.allocated_amount),
    color: values.color && values.color.trim() ? values.color.trim() : null,
  }
}

// ── Expense ──────────────────────────────────────────────────────────────────

export const expenseSchema = z.object({
  category_id: z
    .union([z.string(), z.number()])
    .refine((v) => v !== '' && !isNaN(Number(v)) && Number(v) > 0, {
      message: 'Pick a category',
    }),
  vendor_id: z.union([z.string(), z.number()]).optional().or(z.literal('')),
  title: z.string().min(1, 'Required').max(200),
  estimated_cost: z.union([z.string(), z.number()]).optional().or(z.literal('')),
  actual_cost: z.union([z.string(), z.number()]).optional().or(z.literal('')),
  is_paid: z.boolean(),
  paid_date: z.string().optional().or(z.literal('')),
  due_date: z.string().optional().or(z.literal('')),
  notes: z.string().optional().or(z.literal('')),
})

export type ExpenseFormValues = z.infer<typeof expenseSchema>

export function expenseToPayload(values: ExpenseFormValues) {
  const numeric = (v: string | number | undefined) => {
    if (v === undefined || v === '' || v === null) return null
    const n = typeof v === 'number' ? v : Number(v)
    return isNaN(n) ? null : n
  }
  const blank = (s: string | undefined) => (s && s.trim() ? s.trim() : null)
  return {
    category_id: Number(values.category_id),
    vendor_id: values.vendor_id ? Number(values.vendor_id) : null,
    title: values.title.trim(),
    estimated_cost: numeric(values.estimated_cost) ?? 0,
    actual_cost: numeric(values.actual_cost),
    is_paid: values.is_paid,
    paid_date: blank(values.paid_date),
    due_date: blank(values.due_date),
    notes: blank(values.notes),
  }
}
