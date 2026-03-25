import { beforeEach, describe, expect, it, vi } from 'vitest';

const { ioMock } = vi.hoisted(() => ({
  ioMock: vi.fn(() => ({
    connected: false,
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    disconnect: vi.fn(),
  })),
}));

vi.mock('socket.io-client', () => ({
  io: ioMock,
}));

describe('socketService environment resolution', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.unstubAllEnvs();
    ioMock.mockClear();
  });

  it('uses VITE_SOCKET_URL when provided', async () => {
    vi.stubEnv('VITE_SOCKET_URL', 'http://socket-host:6001');
    vi.stubEnv('VITE_API_BASE_URL', 'http://api-host:5000/api');

    const { socketService } = await import('../socketService');
    socketService.connect('token');

    expect(ioMock).toHaveBeenCalledWith(
      'http://socket-host:6001',
      expect.objectContaining({
        auth: { token: 'Bearer token' },
      }),
    );
  });

  it('derives socket base by stripping /api suffix when VITE_SOCKET_URL is missing', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://api-host:5000/api');

    const { socketService } = await import('../socketService');
    socketService.connect('token');

    expect(ioMock).toHaveBeenCalledWith(
      'http://api-host:5000',
      expect.any(Object),
    );
  });

  it('keeps api base when it does not end with /api and VITE_SOCKET_URL is missing', async () => {
    vi.stubEnv('VITE_API_BASE_URL', 'http://api-host:5000/custom-base');

    const { socketService } = await import('../socketService');
    socketService.connect('token');

    expect(ioMock).toHaveBeenCalledWith(
      'http://api-host:5000/custom-base',
      expect.any(Object),
    );
  });

  it('falls back to localhost defaults when both env vars are missing', async () => {
    const { socketService } = await import('../socketService');
    socketService.connect('token');

    expect(ioMock).toHaveBeenCalledWith(
      'http://localhost:5000',
      expect.any(Object),
    );
  });
});
