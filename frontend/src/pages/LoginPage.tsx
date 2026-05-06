import { useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/lib/auth-context'

export function LoginPage() {
  const { user, isLoading } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  if (!isLoading && user) {
    const from = (location.state as { from?: string })?.from || '/'
    navigate(from, { replace: true })
    return null
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="font-serif text-5xl mb-2">Wedding Studio</h1>
        <p className="text-sm tracking-widest uppercase text-[var(--color-rose)] mb-8">
          Login Page
        </p>
        <p className="text-sm text-[var(--color-text-muted)]">Form coming in Prompt 5.</p>
      </div>
    </div>
  )
}
