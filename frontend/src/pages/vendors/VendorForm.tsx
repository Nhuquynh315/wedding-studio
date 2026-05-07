import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  VENDOR_STATUSES,
  vendorSchema,
  vendorToPayload,
  type VendorFormValues,
} from '@/pages/vendors/vendorSchema'
import type { VendorPublic } from '@/lib/api-schemas'

type Props = {
  initial?: VendorPublic
  onSubmit: (payload: ReturnType<typeof vendorToPayload>) => Promise<void>
  onCancel: () => void
  submitLabel?: string
  isSubmitting?: boolean
}

export function VendorForm({
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
  } = useForm<VendorFormValues>({
    resolver: zodResolver(vendorSchema),
    defaultValues: {
      business_name: initial?.business_name ?? '',
      category: initial?.category ?? 'Other',
      status: initial?.status ?? 'considering',
      contact_name: initial?.contact_name ?? '',
      email: initial?.email ?? '',
      phone: initial?.phone ?? '',
      website: initial?.website ?? '',
      quoted_price: initial?.quoted_price ?? '',
      notes: initial?.notes ?? '',
      rating: initial?.rating ?? '',
      deposit_amount: initial?.deposit_amount ?? '',
      deposit_paid: initial?.deposit_paid ?? false,
      deposit_due_date: initial?.deposit_due_date ?? '',
      contracted: initial?.contracted ?? false,
      contract_signed_date: initial?.contract_signed_date ?? '',
      contract_url: initial?.contract_url ?? '',
      final_payment_amount: initial?.final_payment_amount ?? '',
      final_payment_paid: initial?.final_payment_paid ?? false,
      final_payment_due_date: initial?.final_payment_due_date ?? '',
    },
  })

  const onValidSubmit = async (values: VendorFormValues) => {
    await onSubmit(vendorToPayload(values))
  }

  const sectionTitle = (text: string) => (
    <h3 className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2 mt-1">
      {text}
    </h3>
  )

  return (
    <form
      onSubmit={handleSubmit(onValidSubmit)}
      className="space-y-5 max-h-[70vh] overflow-y-auto pr-2"
    >
      {/* ── Basic ───────────────────────────────────────────── */}
      <div>
        {sectionTitle('Basic')}
        <div className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="vf-business_name">Business name *</Label>
            <Input id="vf-business_name" autoFocus {...register('business_name')} />
            {errors.business_name && (
              <p className="text-sm text-red-600">{errors.business_name.message}</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="vf-category">Category</Label>
              <Input id="vf-category" {...register('category')} placeholder="Photography" />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="vf-status">Status</Label>
              <select
                id="vf-status"
                {...register('status')}
                className="w-full h-9 rounded-md border border-[var(--color-border-default)] bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] capitalize"
              >
                {VENDOR_STATUSES.map((s) => (
                  <option key={s} value={s} className="capitalize">
                    {s.charAt(0).toUpperCase() + s.slice(1)}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* ── Contact ─────────────────────────────────────────── */}
      <div>
        {sectionTitle('Contact')}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="vf-contact_name">Contact name</Label>
            <Input id="vf-contact_name" {...register('contact_name')} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-phone">Phone</Label>
            <Input id="vf-phone" {...register('phone')} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-email">Email</Label>
            <Input id="vf-email" type="email" {...register('email')} />
            {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-website">Website</Label>
            <Input id="vf-website" {...register('website')} placeholder="https://…" />
          </div>
        </div>
      </div>

      {/* ── Cost & rating ───────────────────────────────────── */}
      <div>
        {sectionTitle('Cost')}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="vf-quoted_price">Quoted price (AUD)</Label>
            <Input
              id="vf-quoted_price"
              type="number"
              min="0"
              step="100"
              {...register('quoted_price')}
            />
            {errors.quoted_price && (
              <p className="text-sm text-red-600">{errors.quoted_price.message as string}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-rating">Rating (0–5)</Label>
            <Input
              id="vf-rating"
              type="number"
              min="0"
              max="5"
              step="1"
              {...register('rating')}
            />
            {errors.rating && (
              <p className="text-sm text-red-600">{errors.rating.message as string}</p>
            )}
          </div>
        </div>
        <div className="space-y-1.5 mt-3">
          <Label htmlFor="vf-notes">Notes</Label>
          <textarea
            id="vf-notes"
            {...register('notes')}
            rows={3}
            className="w-full rounded-md border border-[var(--color-border-default)] bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-rose)] resize-none"
          />
        </div>
      </div>

      {/* ── Deposit ─────────────────────────────────────────── */}
      <div>
        {sectionTitle('Deposit')}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="vf-deposit_amount">Amount (AUD)</Label>
            <Input
              id="vf-deposit_amount"
              type="number"
              min="0"
              step="50"
              {...register('deposit_amount')}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-deposit_due_date">Due date</Label>
            <Input id="vf-deposit_due_date" type="date" {...register('deposit_due_date')} />
          </div>
        </div>
        <label className="flex items-center gap-2 mt-3 text-sm cursor-pointer">
          <input
            type="checkbox"
            {...register('deposit_paid')}
            className="h-4 w-4 rounded accent-[var(--color-rose)]"
          />
          Deposit paid
        </label>
      </div>

      {/* ── Contract ────────────────────────────────────────── */}
      <div>
        {sectionTitle('Contract')}
        <label className="flex items-center gap-2 text-sm mb-3 cursor-pointer">
          <input
            type="checkbox"
            {...register('contracted')}
            className="h-4 w-4 rounded accent-[var(--color-rose)]"
          />
          Contract signed
        </label>
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="vf-contract_signed_date">Signed date</Label>
            <Input
              id="vf-contract_signed_date"
              type="date"
              {...register('contract_signed_date')}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-contract_url">Contract URL</Label>
            <Input
              id="vf-contract_url"
              {...register('contract_url')}
              placeholder="Drive/Dropbox link"
            />
          </div>
        </div>
      </div>

      {/* ── Final payment ───────────────────────────────────── */}
      <div>
        {sectionTitle('Final payment')}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1.5">
            <Label htmlFor="vf-final_payment_amount">Amount (AUD)</Label>
            <Input
              id="vf-final_payment_amount"
              type="number"
              min="0"
              step="50"
              {...register('final_payment_amount')}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="vf-final_payment_due_date">Due date</Label>
            <Input
              id="vf-final_payment_due_date"
              type="date"
              {...register('final_payment_due_date')}
            />
          </div>
        </div>
        <label className="flex items-center gap-2 mt-3 text-sm cursor-pointer">
          <input
            type="checkbox"
            {...register('final_payment_paid')}
            className="h-4 w-4 rounded accent-[var(--color-rose)]"
          />
          Final payment paid
        </label>
      </div>

      {/* ── Footer ──────────────────────────────────────────── */}
      <div className="flex justify-end gap-2 pt-2 sticky bottom-0 bg-white pb-2">
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
