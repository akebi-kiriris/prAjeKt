import { defineStore } from 'pinia';
import api from '../services/api';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('access_token') || null,
    refreshToken: localStorage.getItem('refresh_token') || null,
  }),
  
  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    currentUser: (state) => state.user,
  },
  
  actions: {
    async login(email, password) {
      try {
        const response = await api.post('/auth/login', { email, password });
        this.accessToken = response.data.access_token;
        this.refreshToken = response.data.refresh_token;
        this.user = response.data.user;
        localStorage.setItem('access_token', this.accessToken);
        localStorage.setItem('refresh_token', this.refreshToken);
        // 登入後立即刷新 user 狀態
        await this.fetchCurrentUser();
        return { success: true };
      } catch (error) {
        return { success: false, error: error.response?.data?.error || '登入失敗' };
      }
    },
    
    async register(userData) {
      try {
        await api.post('/auth/register', userData);
        return { success: true };
      } catch (error) {
        return { success: false, error: error.response?.data?.error || '註冊失敗' };
      }
    },
    
    async logout() {
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
    
    async fetchCurrentUser() {
      try {
        const response = await api.get('/auth/me');
        this.user = response.data;
        return { success: true };
      } catch (error) {
        return { success: false, error: error.response?.data?.error };
      }
    },
  },
});
