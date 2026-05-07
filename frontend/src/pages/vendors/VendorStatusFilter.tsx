import { cn } from '@/lib/utils'
import type { VendorStatus } from '@/lib/api-schemas'

type FilterValue = VendorStatus | 'all'

const OPTIONS: Array<{ value: FilterValue; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'considering', label: 'Considering' },
  { value: 'booked', label: 'Booked' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'backup', label: 'Backup' },
]

type Props = {
  value: FilterValue
  onChange: (value: FilterValue) => void
}

export function VendorStatusFilter({ value, onChange }: Props) {
  return (
    <div className="flex gap-1.5 flex-wrap">
      {OPTIONS.map((opt) => {
        const isActive = value === opt.value
        return (
          <button
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className={cn(
              'px-3 py-1.5 rounded-full text-sm border transition-colors',
              isActive
                ? 'bg-[var(--color-rose)] text-white border-[var(--color-rose)]'
                : 'bg-white text-[var(--color-text-dark)] border-[var(--color-border-default)] hover:border-[var(--color-rose)]',
            )}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}

export type { FilterValue }
