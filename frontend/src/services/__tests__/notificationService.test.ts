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
    // 確保所有使用到 .then 的 mock 都回傳一個 Promise，避免測試中讀取到 undefined
    (api.get as unknown as ReturnType<typeof vi.fn>).mockResolvedValue({ data: { count: 0 } } as any);
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
