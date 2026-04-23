import { useState, useCallback } from 'react'
import { useAuthStore } from '../context/AuthContext'

export const useAuth = () => {
  const { user, token, login, logout, isAuthenticated, isAdmin } = useAuthStore()
  const [loading, setLoading] = useState(false)

  const authenticate = useCallback(async (testToken: string) => {
    setLoading(true)
    // In production, this would validate the token with the backend
    const mockUser = {
      user_id: testToken.replace('user_', ''),
      email: 'user@example.com',
      roles: ['user'],
      authenticated: true,
    }
    login(mockUser, testToken)
    localStorage.setItem('auth_token', testToken)
    setLoading(false)
  }, [login])

  const logoutUser = useCallback(() => {
    logout()
    localStorage.removeItem('auth_token')
  }, [logout])

  return {
    user,
    token,
    isAuthenticated,
    isAdmin,
    loading,
    authenticate,
    logout: logoutUser,
  }
}
