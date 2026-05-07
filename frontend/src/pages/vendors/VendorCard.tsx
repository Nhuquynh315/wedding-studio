import { CheckCircle2, FileText, Pencil, Star, Trash2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { VendorStatusPill } from '@/pages/vendors/VendorStatusPill'
import { formatAUD } from '@/lib/format'
import type { VendorPublic } from '@/lib/api-schemas'

type Props = {
  vendor: VendorPublic
  onEdit: () => void
  onDelete: () => void
}

export function VendorCard({ vendor, onEdit, onDelete }: Props) {
  return (
    <Card className="group">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 min-w-0">
            <h3 className="font-medium truncate">{vendor.business_name}</h3>
            <p className="text-xs text-[var(--color-text-muted)] mt-0.5">{vendor.category}</p>
          </div>
          <VendorStatusPill status={vendor.status} />
        </div>

        {(vendor.contact_name || vendor.email || vendor.phone) && (
          <div className="text-xs text-[var(--color-text-muted)] space-y-0.5">
            {vendor.contact_name && <p>{vendor.contact_name}</p>}
            {vendor.email && <p className="truncate">{vendor.email}</p>}
            {vendor.phone && <p>{vendor.phone}</p>}
          </div>
        )}

        {vendor.quoted_price != null && (
          <p className="text-sm font-medium">{formatAUD(vendor.quoted_price)}</p>
        )}

        <div className="flex items-center gap-3 text-xs text-[var(--color-text-muted)]">
          {vendor.contracted && (
            <span className="flex items-center gap-1">
              <FileText className="h-3 w-3" /> Contract
            </span>
          )}
          {vendor.deposit_paid && (
            <span className="flex items-center gap-1">
              <CheckCircle2 className="h-3 w-3 text-green-600" /> Deposit paid
            </span>
          )}
          {vendor.rating != null && (
            <span className="flex items-center gap-1">
              <Star className="h-3 w-3 fill-amber-400 text-amber-400" />
              {vendor.rating}
            </span>
          )}
        </div>

        <div className="flex justify-end gap-1 -mb-1">
          <button
            onClick={onEdit}
            className="opacity-0 group-hover:opacity-100 p-1.5 rounded hover:bg-[var(--color-rose-bg)] text-[var(--color-text-muted)] hover:text-[var(--color-rose-dark)] transition-opacity"
            aria-label="Edit"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            onClick={onDelete}
            className="opacity-0 group-hover:opacity-100 p-1.5 rounded hover:bg-red-50 text-[var(--color-text-muted)] hover:text-red-700 transition-opacity"
            aria-label="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </CardContent>
    </Card>
  )
}
