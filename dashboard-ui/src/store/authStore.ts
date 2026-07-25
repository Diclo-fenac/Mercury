import { create } from 'zustand';

interface AuthState {
  isAuthenticated: boolean;
  setAuth: () => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: false,
  setAuth: () => set({ isAuthenticated: true }),
  logout: () => {
    set({ isAuthenticated: false });
    window.location.href = '/dashboard/login';
  },
}));
