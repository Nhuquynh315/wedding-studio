import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="font-serif text-5xl mb-2">404</h1>
        <p className="text-sm tracking-widest uppercase text-[var(--color-rose)] mb-6">
          Page not found
        </p>
        <Link to="/" className="text-[var(--color-rose)] underline">
          Back to dashboard
        </Link>
      </div>
    </div>
  )
}
