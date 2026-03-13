import { defineStore } from 'pinia';
import axios from 'axios';
import type { User } from '../types';
import api from '../services/api';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
}

interface AuthResult {
  success: boolean;
  error?: string;
}

const getErrorMessage = (error: unknown, fallback: string): string => {
  if (axios.isAxiosError(error)) {
    return (error.response?.data as { error?: string } | undefined)?.error || fallback;
  }
  return fallback;
};

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.accessToken,
    currentUser: (state): User | null => state.user,
  },

  actions: {
    async login(email: string, password: string): Promise<AuthResult> {
      try {
        const response = await api.post('/auth/login', { email, password });
        this.accessToken = response.data.access_token as string;
        this.refreshToken = response.data.refresh_token as string;
        this.user = response.data.user as User;
        localStorage.setItem('access_token', this.accessToken);
        localStorage.setItem('refresh_token', this.refreshToken);
        await this.fetchCurrentUser();
        return { success: true };
      } catch (error) {
        return { success: false, error: getErrorMessage(error, '登入失敗') };
      }
    },

    async register(userData: Record<string, unknown>): Promise<AuthResult> {
      try {
        await api.post('/auth/register', userData);
        return { success: true };
      } catch (error) {
        return { success: false, error: getErrorMessage(error, '註冊失敗') };
      }
    },

    async logout(): Promise<void> {
      try {
        await api.post('/auth/logout');
      } catch (error) {
        console.error('登出時發生錯誤:', error);
      } finally {
        this.user = null;
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    },

    async fetchCurrentUser(): Promise<AuthResult> {
      try {
        const response = await api.get('/auth/me');
        this.user = response.data as User;
        return { success: true };
      } catch (error) {
        return { success: false, error: getErrorMessage(error, '取得使用者資料失敗') };
      }
    },
  },
});
