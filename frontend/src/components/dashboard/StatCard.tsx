import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import type { ReactNode } from 'react'

type Props = {
  label: string
  value: ReactNode
  sub?: ReactNode
  className?: string
}

export function StatCard({ label, value, sub, className }: Props) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardContent className="p-5">
        <div className="text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
          {label}
        </div>
        <div className="text-3xl font-serif text-[var(--color-text-dark)] mb-1">{value}</div>
        {sub && <div className="text-xs text-[var(--color-text-muted)]">{sub}</div>}
      </CardContent>
    </Card>
  )
}
