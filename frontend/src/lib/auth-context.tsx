import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import { api, ApiError, AUTH_EXPIRED_EVENT } from '@/lib/api'
import { tokens } from '@/lib/tokens'
import type { UserPublic } from '@/lib/api-schemas'

type AuthContextValue = {
  user: UserPublic | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  updateUser: (user: UserPublic) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserPublic | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let cancelled = false

    const init = async () => {
      if (!tokens.getAccess()) {
        setIsLoading(false)
        return
      }
      try {
        const me = await api.auth.me()
        if (!cancelled) setUser(me)
      } catch (err) {
        // Token invalid/expired and refresh failed; tokens cleared by api.ts
        if (!cancelled) setUser(null)
        void err
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    init()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    const handler = () => setUser(null)
    window.addEventListener(AUTH_EXPIRED_EVENT, handler)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handler)
  }, [])

  const login = async (email: string, password: string) => {
    const tokenResp = await api.auth.login({ email, password })
    tokens.set(tokenResp.access_token, tokenResp.refresh_token)
    const me = await api.auth.me()
    setUser(me)
  }

  const logout = async () => {
    const refreshToken = tokens.getRefresh()
    if (refreshToken) {
      await api.auth.logout(refreshToken)
    } else {
      tokens.clear()
    }
    setUser(null)
  }

  const updateUser = (updated: UserPublic) => {
    setUser(updated)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

// Re-export ApiError so pages can import it from here alongside useAuth
export { ApiError }
