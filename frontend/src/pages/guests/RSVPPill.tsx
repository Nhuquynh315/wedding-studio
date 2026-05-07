import { cn } from '@/lib/utils'
import type { RSVPStatus } from '@/lib/api-schemas'

const STYLES: Record<RSVPStatus, string> = {
  pending: 'bg-amber-100 text-amber-800 border-amber-200',
  confirmed: 'bg-green-100 text-green-800 border-green-200',
  declined: 'bg-stone-200 text-stone-700 border-stone-300',
}

export function RSVPPill({ status }: { status: RSVPStatus }) {
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
