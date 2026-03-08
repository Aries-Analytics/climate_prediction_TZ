import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import axiosInstance from '../config/axiosInstance'

interface User {
  id: number
  username: string
  email: string
  role: string
  isActive: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    if (storedToken) {
      setToken(storedToken)
      fetchCurrentUser()
    } else {
      setIsLoading(false)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      const response = await axiosInstance.get('/auth/me')
      setUser(response.data)
    } catch (error) {
      // Interceptor already handled token refresh or redirect to /login
      setToken(null)
      setUser(null)
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const response = await axiosInstance.post('/auth/login', { username, password })
    const { access_token, refresh_token } = response.data
    setToken(access_token)
    localStorage.setItem('token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    await fetchCurrentUser()
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        login,
        logout,
        isAuthenticated: !!token && !!user,
        isLoading
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
