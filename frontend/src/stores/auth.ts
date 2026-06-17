import { defineStore } from 'pinia';
import type { AuthLoginResponse, CurrentUserResponse, RegisterForm, User } from '../types';
import api from '../services/api';
import { getApiErrorCode, getApiErrorMessage, shouldRedirectToLogin } from '../utils/apiError';

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
}

interface AuthResult {
  success: boolean;
  error?: string;
}

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
        const response = await api.post<AuthLoginResponse>('/auth/login', { email, password });
        this.accessToken = response.data.access_token;
        this.refreshToken = response.data.refresh_token;
        localStorage.setItem('access_token', this.accessToken);
        localStorage.setItem('refresh_token', this.refreshToken);
        await this.fetchCurrentUser();
        return { success: true };
      } catch (error) {
        return { success: false, error: getApiErrorMessage(error, '登入失敗') };
      }
    },

    async register(userData: RegisterForm): Promise<AuthResult> {
      try {
        await api.post('/auth/register', userData);
        return { success: true };
      } catch (error) {
        return { success: false, error: getApiErrorMessage(error, '註冊失敗') };
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
        const response = await api.get<CurrentUserResponse>('/auth/me');
        this.user = {
          id: response.data.id,
          name: response.data.name,
          username: response.data.username,
          email: response.data.email,
          phone: response.data.phone,
        };
        return { success: true };
      } catch (error) {
        if (shouldRedirectToLogin(getApiErrorCode(error))) {
          this.user = null;
          this.accessToken = null;
          this.refreshToken = null;
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        }
        return { success: false, error: getApiErrorMessage(error, '取得使用者資料失敗') };
      }
    },
  },
});
