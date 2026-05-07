import { useAuth } from '@/lib/auth-context'

export function DashboardPage() {
  const { user } = useAuth()
  return (
    <div className="p-8">
      <h1 className="font-serif text-3xl mb-2">Dashboard</h1>
      <p className="text-sm text-[var(--color-text-muted)]">
        Hello, {user?.full_name ?? user?.email}
      </p>
      <p className="mt-6 text-sm">Real dashboard content arrives in Prompt 7.</p>
    </div>
  )
}
