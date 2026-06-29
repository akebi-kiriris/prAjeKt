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

  it('should restore persisted tokens when the store is created', () => {
    localStorage.setItem('access_token', 'persisted-access');
    localStorage.setItem('refresh_token', 'persisted-refresh');

    const store = useAuthStore();

    expect(store.accessToken).toBe('persisted-access');
    expect(store.refreshToken).toBe('persisted-refresh');
    expect(store.isAuthenticated).toBe(true);
  });

  it('logout success should call the API and clear persisted authentication', async () => {
    mockedApi.post.mockResolvedValueOnce({ data: {} });
    const store = useAuthStore();
    store.accessToken = 'access-1';
    store.refreshToken = 'refresh-1';
    store.user = { id: 1, email: 'a@b.com' } as never;
    localStorage.setItem('access_token', 'access-1');
    localStorage.setItem('refresh_token', 'refresh-1');

    await store.logout();

    expect(mockedApi.post).toHaveBeenCalledWith('/auth/logout');
    expect(store.user).toBeNull();
    expect(store.accessToken).toBeNull();
    expect(store.refreshToken).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
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

  it('fetchCurrentUser success should populate the current user', async () => {
    mockedApi.get.mockResolvedValueOnce({
      data: {
        id: 7,
        name: 'User Seven',
        username: 'seven',
        email: 'seven@example.com',
        phone: '0911222333',
      },
    });
    const store = useAuthStore();

    const result = await store.fetchCurrentUser();

    expect(mockedApi.get).toHaveBeenCalledWith('/auth/me');
    expect(result).toEqual({ success: true });
    expect(store.user).toEqual({
      id: 7,
      name: 'User Seven',
      username: 'seven',
      email: 'seven@example.com',
      phone: '0911222333',
    });
  });

  it('fetchCurrentUser should clear the session only when the API reports UNAUTHORIZED', async () => {
    mockedApi.get.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { error_code: 'UNAUTHORIZED' } },
    });
    const store = useAuthStore();
    store.accessToken = 'expired-access';
    store.refreshToken = 'expired-refresh';
    store.user = { id: 1, email: 'user@example.com' } as never;
    localStorage.setItem('access_token', 'expired-access');
    localStorage.setItem('refresh_token', 'expired-refresh');

    const result = await store.fetchCurrentUser();

    expect(result.success).toBe(false);
    expect(result.error).toBe('登入已失效，請重新登入');
    expect(store.user).toBeNull();
    expect(store.accessToken).toBeNull();
    expect(store.refreshToken).toBeNull();
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
  });

  it('fetchCurrentUser should preserve the session for a non-auth API error', async () => {
    mockedApi.get.mockRejectedValueOnce({
      isAxiosError: true,
      response: { data: { error_code: 'SERVICE_UNAVAILABLE' } },
    });
    const store = useAuthStore();
    store.accessToken = 'valid-access';
    store.refreshToken = 'valid-refresh';
    store.user = { id: 2, email: 'keep@example.com' } as never;
    localStorage.setItem('access_token', 'valid-access');
    localStorage.setItem('refresh_token', 'valid-refresh');

    const result = await store.fetchCurrentUser();

    expect(result).toEqual({ success: false, error: '服務暫時不可用，請稍後再試' });
    expect(store.user).toMatchObject({ email: 'keep@example.com' });
    expect(store.accessToken).toBe('valid-access');
    expect(store.refreshToken).toBe('valid-refresh');
    expect(localStorage.getItem('access_token')).toBe('valid-access');
    expect(localStorage.getItem('refresh_token')).toBe('valid-refresh');
  });
});
