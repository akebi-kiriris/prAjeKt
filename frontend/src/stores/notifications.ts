import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Notification } from '../types';
import { notificationService } from '../services/notificationService';

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref<Notification[]>([]);
  const unreadCount = ref(0);

  const hasUnread = computed(() => unreadCount.value > 0);

  async function fetchNotifications(): Promise<void> {
    const res = await notificationService.getAll();
    notifications.value = res.data;
  }

  async function fetchUnreadCount(): Promise<void> {
    const res = await notificationService.getUnreadCount();
    unreadCount.value = res.data.count;
  }

  async function markAsRead(id: number): Promise<void> {
    await notificationService.markAsRead(id);
    const n = notifications.value.find(item => item.id === id);
    if (n) n.is_read = true;
    if (unreadCount.value > 0) unreadCount.value--;
  }

  async function markAllAsRead(): Promise<void> {
    await notificationService.markAllAsRead();
    notifications.value.forEach(n => {
      n.is_read = true;
    });
    unreadCount.value = 0;
  }

  async function deleteNotification(id: number): Promise<void> {
    await notificationService.delete(id);
    const n = notifications.value.find(item => item.id === id);
    if (n && !n.is_read && unreadCount.value > 0) unreadCount.value--;
    notifications.value = notifications.value.filter(item => item.id !== id);
  }

  return {
    notifications,
    unreadCount,
    hasUnread,
    fetchNotifications,
    fetchUnreadCount,
    markAsRead,
    markAllAsRead,
    deleteNotification,
  };
});
