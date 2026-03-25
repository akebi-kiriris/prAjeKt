import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

vi.mock('../../services/api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

vi.mock('axios', () => ({
  default: {
    isAxiosError: (err: unknown) => !!(err as { isAxiosError?: boolean })?.isAxiosError,
  },
  isAxiosError: (err: unknown) => !!(err as { isAxiosError?: boolean })?.isAxiosError,
}));

import api from '../../services/api';
import { useAuthStore } from '../auth';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe('auth store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('login success should persist tokens and fetch current user', async () => {
    mockedApi.post.mockResolvedValueOnce({
      data: {
        access_token: 'access-1',
        refresh_token: 'refresh-1',
        user: { id: 1, email: 'a@b.com' },
      },
    });
    mockedApi.get.mockResolvedValueOnce({
      data: { id: 1, name: 'User A', email: 'a@b.com' },
    });

    const store = useAuthStore();
    const res = await store.login('a@b.com', 'pw');

    expect(res.success).toBe(true);
    expect(mockedApi.post).toHaveBeenCalledWith('/auth/login', { email: 'a@b.com', password: 'pw' });
    expect(mockedApi.get).toHaveBeenCalledWith('/auth/me');
    expect(localStorage.getItem('access_token')).toBe('access-1');
    expect(localStorage.getItem('refresh_token')).toBe('refresh-1');
    expect(store.isAuthenticated).toBe(true);
    expect(store.user?.name).toBe('User A');
  });

  it('login failure should return axios message fallback', async () => {
    mockedApi.post.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { error: '帳號或密碼錯誤' } },
    });

    const store = useAuthStore();
    const res = await store.login('a@b.com', 'bad');

    expect(res.success).toBe(false);
    expect(res.error).toBe('帳號或密碼錯誤');
    expect(store.isAuthenticated).toBe(false);
  });

  it('logout should clear state and localStorage even if api call fails', async () => {
    mockedApi.post.mockRejectedValueOnce(new Error('network'));

    const store = useAuthStore();
    store.accessToken = 'access-1';
    store.refreshToken = 'refresh-1';
    store.user = { id: 1, email: 'a@b.com' } as never;
    localStorage.setItem('access_token', 'access-1');
    localStorage.setItem('refresh_token', 'refresh-1');

    await store.logout();

    expect(store.user).toBeNull();
    expect(store.accessToken).toBeNull();
    expect(store.refreshToken).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });
});
