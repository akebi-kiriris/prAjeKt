import axios from 'axios';
import router from '../router';

// 統一管理 baseURL
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
  withCredentials: true,
});

// Token 刷新相關變數
let isRefreshing = false;  // 是否正在刷新 token
let failedQueue = [];      // 等待刷新完成的請求佇列

// 處理佇列中的請求
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Request 攔截器：自動加上 JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response 攔截器：處理 401 錯誤並自動刷新 token
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 如果是 401 錯誤且還沒重試過
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 避免 refresh endpoint 本身失敗時無限循環
      if (originalRequest.url.includes('/auth/refresh')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/login');
        return Promise.reject(error);
      }

      // 如果正在刷新中，將此請求加入佇列等待
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch(err => {
            return Promise.reject(err);
          });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');

      // 沒有 refresh_token，直接跳轉登入
      if (!refreshToken) {
        localStorage.removeItem('access_token');
        router.push('/login');
        return Promise.reject(error);
      }

      try {
        // 使用 refresh_token 取得新的 access_token
        const response = await axios.post(
          `${BASE_URL}/auth/refresh`,
          {},
          {
            headers: {
              Authorization: `Bearer ${refreshToken}`
            }
          }
        );

        const newAccessToken = response.data.access_token;
        localStorage.setItem('access_token', newAccessToken);

        // 更新原本失敗請求的 header
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;

        // 處理佇列中所有等待的請求
        processQueue(null, newAccessToken);

        // 重試原本的請求
        return api(originalRequest);
      } catch (refreshError) {
        // refresh_token 也過期了，清除所有 token 並跳轉登入
        processQueue(refreshError, null);
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        router.push('/login');
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export default api;
