import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { User, AuthState, LoginRequest, RegisterRequest } from '@/types';
import { login, register } from '@/lib/api';

interface AuthStore extends AuthState {
  loginAction: (params: LoginRequest) => Promise<void>;
  registerAction: (params: RegisterRequest) => Promise<void>;
  logout: () => void;
  clearError: () => void;
  setUser: (user: User) => void;
  setToken: (token: string) => void;
  hydrate: () => void;
}

const TOKEN_KEY = 'auth_token';
const USER_KEY = 'auth_user';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      loginAction: async (params: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await login(params);
          localStorage.setItem(TOKEN_KEY, response.token);
          localStorage.setItem(USER_KEY, JSON.stringify(response.user));
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '登录失败',
            isLoading: false,
          });
          throw error;
        }
      },

      registerAction: async (params: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await register(params);
          localStorage.setItem(TOKEN_KEY, response.token);
          localStorage.setItem(USER_KEY, JSON.stringify(response.user));
          set({
            user: response.user,
            token: response.token,
            isAuthenticated: true,
            isLoading: false,
          });
        } catch (error) {
          set({
            error: error instanceof Error ? error.message : '注册失败',
            isLoading: false,
          });
          throw error;
        }
      },

      logout: () => {
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      clearError: () => set({ error: null }),

      setUser: (user: User) => {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
        set({ user });
      },

      setToken: (token: string) => {
        localStorage.setItem(TOKEN_KEY, token);
        set({ token });
      },

      hydrate: () => {
        const token = localStorage.getItem(TOKEN_KEY);
        const userStr = localStorage.getItem(USER_KEY);
        if (token && userStr) {
          try {
            const user = JSON.parse(userStr) as User;
            set({
              user,
              token,
              isAuthenticated: true,
            });
          } catch {
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
          }
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);