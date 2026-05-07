import { cn } from '@/lib/utils'
import type { RSVPStatus } from '@/lib/api-schemas'

type FilterValue = RSVPStatus | 'all'

const OPTIONS: Array<{ value: FilterValue; label: string }> = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Pending' },
  { value: 'confirmed', label: 'Confirmed' },
  { value: 'declined', label: 'Declined' },
]

type Props = {
  value: FilterValue
  onChange: (value: FilterValue) => void
}

export function RSVPFilterChips({ value, onChange }: Props) {
  return (
    <div className="flex gap-1.5">
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
