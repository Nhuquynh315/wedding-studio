import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { AUTH_EXPIRED_EVENT } from '@/lib/api'

/** Redirects to /login when auth:expired fires (e.g., refresh failed). */
export function AuthExpiredHandler() {
  const navigate = useNavigate()

  useEffect(() => {
    const handler = () => {
      navigate('/login', { replace: true })
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, handler)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handler)
  }, [navigate])

  return null
}
