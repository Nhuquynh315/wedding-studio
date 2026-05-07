import { cn } from '@/lib/utils'
import type { VendorStatus } from '@/lib/api-schemas'

const STYLES: Record<VendorStatus, string> = {
  considering: 'bg-amber-100 text-amber-800 border-amber-200',
  booked: 'bg-green-100 text-green-800 border-green-200',
  rejected: 'bg-stone-200 text-stone-700 border-stone-300',
  backup: 'bg-blue-100 text-blue-800 border-blue-200',
}

export function VendorStatusPill({ status }: { status: VendorStatus }) {
  return (
    <span
      className={cn(
        'inline-block px-2 py-0.5 rounded-full text-xs border capitalize',
        STYLES[status],
      )}
    >
      {status}
    </span>
  )
}
