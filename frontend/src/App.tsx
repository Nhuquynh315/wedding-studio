import { useAuth } from '@/lib/auth-context'

export default function App() {
  const { user, isLoading } = useAuth()

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="font-serif text-5xl mb-2 text-[var(--color-text-dark)]">
          Wedding Studio
        </h1>
        <p className="text-sm tracking-widest uppercase text-[var(--color-rose)]">
          {isLoading
            ? 'Loading…'
            : user
              ? `Logged in as ${user.email}`
              : 'Not logged in'}
        </p>
      </div>
    </div>
  )
}
