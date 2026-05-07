import { z } from 'zod'

export const VENDOR_STATUSES = ['considering', 'booked', 'rejected', 'backup'] as const

const optionalNum = z
  .union([z.string(), z.number()])
  .optional()
  .or(z.literal(''))
  .refine((v) => v === '' || v === undefined || (!isNaN(Number(v)) && Number(v) >= 0), {
    message: 'Must be 0 or greater',
  })

export const vendorSchema = z.object({
  business_name: z.string().min(1, 'Required').max(200),
  category: z.string().max(50).default('Other'),
  status: z.enum(VENDOR_STATUSES),

  contact_name: z.string().max(200).optional().or(z.literal('')),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  phone: z.string().max(50).optional().or(z.literal('')),
  website: z.string().max(300).optional().or(z.literal('')),

  quoted_price: optionalNum,
  notes: z.string().optional().or(z.literal('')),
  rating: z
    .union([z.string(), z.number()])
    .optional()
    .or(z.literal(''))
    .refine((v) => v === '' || v === undefined || (Number(v) >= 0 && Number(v) <= 5), {
      message: 'Rating must be 0–5',
    }),

  deposit_amount: optionalNum,
  deposit_paid: z.boolean().default(false),
  deposit_due_date: z.string().optional().or(z.literal('')),

  contracted: z.boolean().default(false),
  contract_signed_date: z.string().optional().or(z.literal('')),
  contract_url: z.string().max(500).optional().or(z.literal('')),

  final_payment_amount: optionalNum,
  final_payment_paid: z.boolean().default(false),
  final_payment_due_date: z.string().optional().or(z.literal('')),
})

export type VendorFormValues = z.infer<typeof vendorSchema>

export function vendorToPayload(values: VendorFormValues) {
  const numeric = (v: string | number | undefined) => {
    if (v === undefined || v === '' || v === null) return null
    const n = typeof v === 'number' ? v : Number(v)
    return isNaN(n) ? null : n
  }
  const blank = (s: string | undefined) => (s && s.trim() ? s.trim() : null)

  return {
    business_name: values.business_name.trim(),
    category: values.category?.trim() || 'Other',
    status: values.status,
    contact_name: blank(values.contact_name),
    email: blank(values.email),
    phone: blank(values.phone),
    website: blank(values.website),
    quoted_price: numeric(values.quoted_price),
    notes: blank(values.notes),
    rating: numeric(values.rating),
    deposit_amount: numeric(values.deposit_amount),
    deposit_paid: values.deposit_paid,
    deposit_due_date: blank(values.deposit_due_date),
    contracted: values.contracted,
    contract_signed_date: blank(values.contract_signed_date),
    contract_url: blank(values.contract_url),
    final_payment_amount: numeric(values.final_payment_amount),
    final_payment_paid: values.final_payment_paid,
    final_payment_due_date: blank(values.final_payment_due_date),
  }
}
