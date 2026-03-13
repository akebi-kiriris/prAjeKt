import api from './api';
import type { AxiosResponse } from 'axios';
import type { Notification } from '../types';

interface UnreadCountResponse {
  count: number;
}

export const notificationService = {
  getAll:         (): Promise<AxiosResponse<Notification[]>>          => api.get('/notifications'),
  getUnreadCount: (): Promise<AxiosResponse<UnreadCountResponse>>     => api.get('/notifications/unread-count'),
  markAsRead:     (id: number): Promise<AxiosResponse<Notification>>  => api.patch(`/notifications/${id}/read`),
  markAllAsRead:  (): Promise<AxiosResponse<void>>                    => api.patch('/notifications/read-all'),
  delete:         (id: number): Promise<AxiosResponse<void>>          => api.delete(`/notifications/${id}`),
};
