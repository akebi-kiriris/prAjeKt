import { beforeEach, describe, expect, it, vi } from 'vitest';

type MockAxiosInstance = ReturnType<typeof vi.fn> & {
  interceptors: {
    request: { use: ReturnType<typeof vi.fn> };
    response: { use: ReturnType<typeof vi.fn> };
  };
};

const { axiosCreateMock, axiosPostMock, apiInstanceMock, routerPushMock } = vi.hoisted(() => {
  const requestUse = vi.fn();
  const responseUse = vi.fn();

  const apiInstance = Object.assign(vi.fn(), {
    interceptors: {
      request: { use: requestUse },
      response: { use: responseUse },
    },
  }) as MockAxiosInstance;

  return {
    axiosCreateMock: vi.fn(() => apiInstance),
    axiosPostMock: vi.fn(),
    apiInstanceMock: apiInstance,
    routerPushMock: vi.fn(),
  };
});

vi.mock('axios', () => {
  const axiosDefault = {
    create: axiosCreateMock,
    post: axiosPostMock,
  };

  return {
    default: axiosDefault,
    create: axiosCreateMock,
    post: axiosPostMock,
  };
});

vi.mock('../../router', () => ({
  default: {
    push: routerPushMock,
  },
}));

type RetryableRequest = {
  url?: string;
  headers: Record<string, string>;
  _retry?: boolean;
};

const flush = async (): Promise<void> => {
  await Promise.resolve();
  await Promise.resolve();
};

describe('api interceptors', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
    vi.clearAllMocks();
    localStorage.clear();
  });

  async function importApiHandlers(): Promise<{
    onRequest: (config: RetryableRequest) => RetryableRequest;
    onResponseError: (error: { response?: { status?: number }; config: RetryableRequest }) => Promise<unknown>;
  }> {
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:5000/api');
    await import('../api');

    const requestArgs = (apiInstanceMock.interceptors.request.use as ReturnType<typeof vi.fn>).mock.calls[0];
    const responseArgs = (apiInstanceMock.interceptors.response.use as ReturnType<typeof vi.fn>).mock.calls[0];

    return {
      onRequest: requestArgs[0],
      onResponseError: responseArgs[1],
    };
  }

  it('adds Authorization header in request interceptor when access token exists', async () => {
    const { onRequest } = await importApiHandlers();
    localStorage.setItem('access_token', 'a-token');

    const config = onRequest({ headers: {} });

    expect(config.headers.Authorization).toBe('Bearer a-token');
  });

  it('401 from refresh endpoint should clear tokens and redirect to login', async () => {
    const { onResponseError } = await importApiHandlers();
    localStorage.setItem('access_token', 'a-token');
    localStorage.setItem('refresh_token', 'r-token');

    const err = {
      response: { status: 401 },
      config: { url: '/auth/refresh', headers: {} },
    };

    await expect(onResponseError(err)).rejects.toBe(err);
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(localStorage.getItem('refresh_token')).toBeNull();
    expect(routerPushMock).toHaveBeenCalledWith('/login');
  });

  it('401 without refresh token should clear access token and redirect to login', async () => {
    const { onResponseError } = await importApiHandlers();
    localStorage.setItem('access_token', 'a-token');

    const err = {
      response: { status: 401 },
      config: { url: '/tasks', headers: {} },
    };

    await expect(onResponseError(err)).rejects.toBe(err);
    expect(localStorage.getItem('access_token')).toBeNull();
    expect(routerPushMock).toHaveBeenCalledWith('/login');
  });

  it('401 with refresh token should refresh token and retry original request', async () => {
    const { onResponseError } = await importApiHandlers();
    localStorage.setItem('refresh_token', 'r-token');

    axiosPostMock.mockResolvedValue({ data: { access_token: 'new-token' } });
    apiInstanceMock.mockResolvedValue({ data: { ok: true } });

    const originalRequest: RetryableRequest = {
      url: '/tasks',
      headers: {},
    };

    const result = await onResponseError({
      response: { status: 401 },
      config: originalRequest,
    });

    expect(axiosPostMock).toHaveBeenCalledWith(
      'http://localhost:5000/api/auth/refresh',
      {},
      { headers: { Authorization: 'Bearer r-token' } },
    );
    expect(localStorage.getItem('access_token')).toBe('new-token');
    expect(originalRequest.headers.Authorization).toBe('Bearer new-token');
    expect(apiInstanceMock).toHaveBeenCalledWith(originalRequest);
    expect(result).toEqual({ data: { ok: true } });
  });

  it('queued 401 requests should resume after refresh finishes', async () => {
    const { onResponseError } = await importApiHandlers();
    localStorage.setItem('refresh_token', 'r-token');

    let resolveRefresh: (value: { data: { access_token: string } }) => void = () => {};
    const refreshPromise = new Promise<{ data: { access_token: string } }>((resolve) => {
      resolveRefresh = resolve;
    });

    axiosPostMock.mockReturnValue(refreshPromise);
    apiInstanceMock.mockResolvedValue({ data: { ok: true } });

    const req1: RetryableRequest = { url: '/a', headers: {} };
    const req2: RetryableRequest = { url: '/b', headers: {} };

    const p1 = onResponseError({ response: { status: 401 }, config: req1 });
    const p2 = onResponseError({ response: { status: 401 }, config: req2 });

    resolveRefresh({ data: { access_token: 'queued-token' } });
    await flush();

    await expect(p1).resolves.toEqual({ data: { ok: true } });
    await expect(p2).resolves.toEqual({ data: { ok: true } });
    expect(req1.headers.Authorization).toBe('Bearer queued-token');
    expect(req2.headers.Authorization).toBe('Bearer queued-token');
    expect(apiInstanceMock).toHaveBeenCalledWith(req1);
    expect(apiInstanceMock).toHaveBeenCalledWith(req2);
  });
});
