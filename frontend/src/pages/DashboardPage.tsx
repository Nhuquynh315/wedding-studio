import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Heart } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { RSVPBar } from '@/components/dashboard/RSVPBar'
import { StatCard } from '@/components/dashboard/StatCard'
import { WeddingSelector } from '@/components/dashboard/WeddingSelector'
import { CreateWeddingDialog } from '@/pages/dashboard/CreateWeddingDialog'
import { useActiveWedding } from '@/hooks/useActiveWedding'
import { api } from '@/lib/api'
import { queryKeys } from '@/lib/query-keys'

function daysUntil(dateString: string | null | undefined): number | null {
  if (!dateString) return null
  const target = new Date(dateString)
  if (isNaN(target.getTime())) return null
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  target.setHours(0, 0, 0, 0)
  return Math.round((target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24))
}

function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('en-AU', {
    style: 'currency',
    currency: 'AUD',
    maximumFractionDigits: 0,
  }).format(amount)
}

export function DashboardPage() {
  const [showCreate, setShowCreate] = useState(false)
  const {
    weddings,
    active,
    activeId,
    setActiveId,
    isLoading: weddingsLoading,
    isError: weddingsError,
    refetch: refetchWeddings,
  } = useActiveWedding()

  if (weddingsLoading) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-64 mb-8" />
        <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    )
  }

  if (weddingsError) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-sm text-red-700 mb-4">Couldn't load your weddings.</p>
            <Button onClick={() => refetchWeddings()}>Try again</Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (weddings.length === 0) {
    return (
      <div className="p-8">
        <Card>
          <CardContent className="p-12 text-center">
            <Heart className="h-12 w-12 text-[var(--color-rose)] mx-auto mb-4" />
            <h2 className="font-serif text-2xl mb-2">Welcome to Wedding Studio</h2>
            <p className="text-sm text-[var(--color-text-muted)] mb-6 max-w-sm mx-auto">
              Create your first wedding to start tracking guests, budget, vendors, and more.
            </p>
            <Button
              onClick={() => setShowCreate(true)}
              className="bg-[var(--color-rose)] hover:bg-[var(--color-rose-dark)] text-white"
            >
              Create your first wedding
            </Button>
          </CardContent>
        </Card>
        <CreateWeddingDialog
          open={showCreate}
          onClose={() => setShowCreate(false)}
          onCreated={(id) => {
            setShowCreate(false)
            setActiveId(id)
          }}
        />
      </div>
    )
  }

  if (!active || !activeId) return null

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <WeddingSelector weddings={weddings} activeId={activeId} onChange={setActiveId} />
        {active.wedding_date && (
          <p className="text-sm text-[var(--color-text-muted)] mt-1">
            {new Date(active.wedding_date).toLocaleDateString('en-AU', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        )}
      </div>

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        <GuestCountCard weddingId={activeId} />
        <ResponseRateCard weddingId={activeId} />
        <DaysUntilCard date={active.wedding_date} />
        <BudgetCard weddingId={activeId} />
      </div>
    </div>
  )
}

// ── Individual stat cards — each owns its query ────────────────────

function GuestCountCard({ weddingId }: { weddingId: number }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.guests.list(weddingId, { limit: 200 }),
    queryFn: () => api.guests.list(weddingId, { limit: 200 }),
  })

  if (isLoading) return <Skeleton className="h-32" />
  if (isError) return <StatCard label="Guests" value="—" sub="error" />

  const guests = data?.items ?? []
  const confirmed = guests.filter((g) => g.rsvp_status === 'confirmed').length
  const pending = guests.filter((g) => g.rsvp_status === 'pending').length
  const declined = guests.filter((g) => g.rsvp_status === 'declined').length

  return (
    <StatCard
      label="Guests"
      value={guests.length}
      sub={
        <div className="space-y-2 mt-2">
          <RSVPBar confirmed={confirmed} pending={pending} declined={declined} />
          <div className="flex items-center gap-3 text-xs">
            <span>
              <span className="inline-block w-2 h-2 rounded-full bg-[var(--color-rose)] mr-1" />
              {confirmed} yes
            </span>
            <span>
              <span className="inline-block w-2 h-2 rounded-full bg-amber-300 mr-1" />
              {pending} pending
            </span>
            <span>
              <span className="inline-block w-2 h-2 rounded-full bg-stone-400 mr-1" />
              {declined} no
            </span>
          </div>
        </div>
      }
    />
  )
}

function ResponseRateCard({ weddingId }: { weddingId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.guests.list(weddingId, { limit: 200 }),
    queryFn: () => api.guests.list(weddingId, { limit: 200 }),
  })

  if (isLoading) return <Skeleton className="h-32" />

  const guests = data?.items ?? []
  const total = guests.length
  const responded = guests.filter(
    (g) => g.rsvp_status === 'confirmed' || g.rsvp_status === 'declined',
  ).length
  const rate = total > 0 ? Math.round((responded / total) * 100) : 0

  return (
    <StatCard
      label="Response rate"
      value={`${rate}%`}
      sub={`${responded} of ${total} responded`}
    />
  )
}

function DaysUntilCard({ date }: { date: string | null | undefined }) {
  const days = daysUntil(date)
  if (days === null) return <StatCard label="Wedding date" value="—" sub="not set yet" />
  if (days < 0) return <StatCard label="Wedding day" value="🎉" sub={`${-days} days ago`} />
  if (days === 0) return <StatCard label="Wedding day" value="Today!" sub="🎊" />
  return (
    <StatCard
      label="Until the day"
      value={days}
      sub={days === 1 ? 'day to go' : 'days to go'}
    />
  )
}

function BudgetCard({ weddingId }: { weddingId: number }) {
  const { data, isLoading } = useQuery({
    queryKey: queryKeys.budget.summary(weddingId),
    queryFn: () => api.budget.summary(weddingId),
  })

  if (isLoading) return <Skeleton className="h-32" />

  const allocated = data?.total_allocated ?? 0
  const spent = data?.total_spent ?? 0
  const pct = allocated > 0 ? Math.min(100, (spent / allocated) * 100) : 0

  return (
    <StatCard
      label="Budget"
      value={formatCurrency(spent)}
      sub={
        <div className="space-y-2 mt-2">
          <div className="h-2 bg-[var(--color-cream)] rounded-full overflow-hidden">
            <div className="h-full bg-[var(--color-rose)]" style={{ width: `${pct}%` }} />
          </div>
          <div className="text-xs">of {formatCurrency(allocated)} allocated</div>
        </div>
      }
    />
  )
}
