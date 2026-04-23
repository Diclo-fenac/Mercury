import { create } from 'zustand'

interface User {
  user_id: string
  email?: string
  roles: string[]
  authenticated: boolean
}

interface AuthState {
  user: User | null
  token: string | null
  login: (user: User, token: string) => void
  logout: () => void
  isAuthenticated: () => boolean
  isAdmin: () => boolean
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  login: (user, token) => set({ user, token }),
  logout: () => set({ user: null, token: null }),
  isAuthenticated: () => {
    const state = useAuthStore.getState()
    return state.user?.authenticated ?? false
  },
  isAdmin: () => {
    const state = useAuthStore.getState()
    return state.user?.roles.includes('admin') ?? false
  },
}))
