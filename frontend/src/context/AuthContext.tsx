import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  getCurrentUser,
  login as apiLogin,
  register as apiRegister,
  setAuthToken,
} from '../services/api'
import type { User } from '../types'

interface AuthContextValue {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
    setAuthToken(null)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true)
    try {
      const auth = await apiLogin(email, password)
      setToken(auth.access_token)
      setAuthToken(auth.access_token)
      const currentUser = await getCurrentUser()
      setUser(currentUser)
    } finally {
      setLoading(false)
    }
  }, [])

  const register = useCallback(async (email: string, password: string) => {
    setLoading(true)
    try {
      await apiRegister(email, password)
      await login(email, password)
    } finally {
      setLoading(false)
    }
  }, [login])

  const value = useMemo(
    () => ({
      user,
      token,
      loading,
      login,
      register,
      logout,
      isAuthenticated: token !== null && user !== null,
    }),
    [user, token, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
