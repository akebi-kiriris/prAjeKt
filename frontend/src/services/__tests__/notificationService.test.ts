import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { notificationService } from '../notificationService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('notificationService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map notification endpoints correctly', () => {
    notificationService.getAll();
    notificationService.getUnreadCount();
    notificationService.markAsRead(5);
    notificationService.markAllAsRead();
    notificationService.delete(5);

    expect(mockedApi.get).toHaveBeenCalledWith('/notifications');
    expect(mockedApi.get).toHaveBeenCalledWith('/notifications/unread-count');
    expect(mockedApi.patch).toHaveBeenCalledWith('/notifications/5/read');
    expect(mockedApi.patch).toHaveBeenCalledWith('/notifications/read-all');
    expect(mockedApi.delete).toHaveBeenCalledWith('/notifications/5');
  });
});
