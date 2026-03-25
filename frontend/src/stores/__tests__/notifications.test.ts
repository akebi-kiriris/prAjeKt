import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../../services/notificationService', () => ({
  notificationService: {
    getAll: vi.fn(),
    getUnreadCount: vi.fn(),
    markAsRead: vi.fn(),
    markAllAsRead: vi.fn(),
    delete: vi.fn(),
  },
}));

import { useNotificationStore } from '../notifications';
import { notificationService } from '../../services/notificationService';

const mockedNotificationService = notificationService as unknown as Record<string, ReturnType<typeof vi.fn>>;

describe('notification store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it('fetch methods should sync notifications and unread count', async () => {
    mockedNotificationService.getAll.mockResolvedValueOnce({
      data: [{ id: 1, is_read: false }],
    });
    mockedNotificationService.getUnreadCount.mockResolvedValueOnce({
      data: { count: 1 },
    });

    const store = useNotificationStore();
    await store.fetchNotifications();
    await store.fetchUnreadCount();

    expect(store.notifications).toEqual([{ id: 1, is_read: false }]);
    expect(store.unreadCount).toBe(1);
    expect(store.hasUnread).toBe(true);
  });

  it('markAsRead should update local status and decrease unread count', async () => {
    mockedNotificationService.markAsRead.mockResolvedValueOnce({});
    const store = useNotificationStore();
    store.notifications = [{ id: 2, is_read: false } as never];
    store.unreadCount = 2;

    await store.markAsRead(2);

    expect(store.notifications[0].is_read).toBe(true);
    expect(store.unreadCount).toBe(1);
  });

  it('deleteNotification should remove item and adjust unread count when needed', async () => {
    mockedNotificationService.delete.mockResolvedValueOnce({});
    const store = useNotificationStore();
    store.notifications = [
      { id: 10, is_read: false } as never,
      { id: 11, is_read: true } as never,
    ];
    store.unreadCount = 1;

    await store.deleteNotification(10);

    expect(store.notifications).toEqual([{ id: 11, is_read: true }]);
    expect(store.unreadCount).toBe(0);
  });
});
