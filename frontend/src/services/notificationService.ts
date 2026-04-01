import api from './api';
import type { AxiosResponse } from 'axios';
import type { Notification } from '../types';

interface UnreadCountResponse {
  count: number;
}

export const notificationService = {
  getAll:         (): Promise<AxiosResponse<Notification[]>>          => api.get('/notifications'),
  getUnreadCount: (): Promise<AxiosResponse<UnreadCountResponse>>     => {
    console.log('📤 [Frontend] 發送 GET /notifications/unread-count...');
    return api.get('/notifications/unread-count').then(res => {
      console.log('📥 [Frontend] 收到回應:', res.data);
      return res;
    }).catch(err => {
      console.error('❌ [Frontend] 請求失敗:', err.message);
      throw err;
    });
  },
  markAsRead:     (id: number): Promise<AxiosResponse<Notification>>  => api.patch(`/notifications/${id}/read`),
  markAllAsRead:  (): Promise<AxiosResponse<void>>                    => api.patch('/notifications/read-all'),
  delete:         (id: number): Promise<AxiosResponse<void>>          => api.delete(`/notifications/${id}`),
};
