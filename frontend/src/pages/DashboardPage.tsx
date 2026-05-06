import { useAuth } from '@/lib/auth-context'

export function DashboardPage() {
  const { user, logout } = useAuth()
  return (
    <div className="min-h-screen p-8">
      <h1 className="font-serif text-4xl mb-2">Dashboard</h1>
      <p className="text-sm text-[var(--color-text-muted)] mb-6">
        Hello, {user?.full_name ?? user?.email}
      </p>
      <button
        onClick={logout}
        className="px-4 py-2 bg-[var(--color-rose)] text-white rounded"
      >
        Log out
      </button>
    </div>
  )
}
