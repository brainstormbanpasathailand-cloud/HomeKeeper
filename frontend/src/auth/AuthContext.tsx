import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, clearTokens, getAccess, setTokens } from '@/lib/api'
import type { User } from '@/lib/types'

interface AuthState {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, fullName: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setSession: (access: string, refresh: string) => Promise<void>
}

const AuthContext = createContext<AuthState>(null as unknown as AuthState)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = useCallback(async () => {
    if (!getAccess()) {
      setUser(null)
      setLoading(false)
      return
    }
    try {
      const resp = await api.get<User>('/auth/me')
      setUser(resp.data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refreshUser()
  }, [refreshUser])

  const login = async (email: string, password: string) => {
    const resp = await api.post('/auth/login', { email, password })
    setTokens(resp.data.access_token, resp.data.refresh_token)
    await refreshUser()
  }

  const register = async (email: string, password: string, fullName: string) => {
    const resp = await api.post('/auth/register', { email, password, full_name: fullName })
    setTokens(resp.data.access_token, resp.data.refresh_token)
    await refreshUser()
  }

  const setSession = async (access: string, refresh: string) => {
    setTokens(access, refresh)
    await refreshUser()
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch {
      /* ignore */
    }
    clearTokens()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, setSession }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
