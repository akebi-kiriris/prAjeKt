import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { notificationService } from '../services/notificationService';

export const useNotificationStore = defineStore('notifications', () => {
  const notifications = ref([]);
  const unreadCount = ref(0);

  const hasUnread = computed(() => unreadCount.value > 0);

  async function fetchNotifications() {
    const res = await notificationService.getAll();
    notifications.value = res.data;
  }

  async function fetchUnreadCount() {
    const res = await notificationService.getUnreadCount();
    unreadCount.value = res.data.count;
  }

  async function markAsRead(id) {
    await notificationService.markAsRead(id);
    const n = notifications.value.find(n => n.id === id);
    if (n) n.is_read = true;
    if (unreadCount.value > 0) unreadCount.value--;
  }

  async function markAllAsRead() {
    await notificationService.markAllAsRead();
    notifications.value.forEach(n => n.is_read = true);
    unreadCount.value = 0;
  }

  async function deleteNotification(id) {
    await notificationService.delete(id);
    const n = notifications.value.find(n => n.id === id);
    if (n && !n.is_read && unreadCount.value > 0) unreadCount.value--;
    notifications.value = notifications.value.filter(n => n.id !== id);
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
