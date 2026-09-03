import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client'
import type { User } from '../types'
import { AuthContext } from './auth-context-value'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(() => Boolean(localStorage.getItem('access_token')))

  useEffect(() => {
    const token = localStorage.getItem('access_token')
    if (!token) return
    api.get('/auth/profile/').then((r) => setUser(r.data)).catch(() => localStorage.clear()).finally(() => setLoading(false))
  }, [])

  const login = async (username: string, password: string) => {
    const { data } = await api.post('/auth/login/', { username, password })
    localStorage.setItem('access_token', data.access)
    localStorage.setItem('refresh_token', data.refresh)
    const profile = await api.get('/auth/profile/')
    setUser(profile.data)
  }

  const logout = async () => {
    const refresh = localStorage.getItem('refresh_token')
    try {
      if (refresh) await api.post('/auth/logout/', { refresh })
    } finally {
      localStorage.clear()
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, isAdmin: user?.role === 'administrator' }}>
      {children}
    </AuthContext.Provider>
  )
}
