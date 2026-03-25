import { beforeEach, describe, expect, it, vi } from 'vitest';

const { socketMock, ioMock } = vi.hoisted(() => {
  const s = {
    connected: false,
    emit: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    disconnect: vi.fn(),
  };
  return {
    socketMock: s,
    ioMock: vi.fn(() => s),
  };
});

vi.mock('socket.io-client', () => ({
  io: ioMock,
}));

import { socketService } from '../socketService';

describe('socketService', () => {
  beforeEach(() => {
    socketService.disconnect();
    socketMock.connected = false;
    socketMock.emit.mockClear();
    socketMock.on.mockClear();
    socketMock.off.mockClear();
    socketMock.disconnect.mockClear();
    ioMock.mockClear();
  });

  it('connect should create socket once and reuse existing instance', () => {
    const a = socketService.connect('token-1');
    const b = socketService.connect('token-2');

    expect(ioMock).toHaveBeenCalledTimes(1);
    expect(a).toBe(b);
    expect(socketService.getSocket()).toBe(a);
  });

  it('isConnected should reflect socket connected state', () => {
    expect(socketService.isConnected()).toBe(false);

    socketService.connect('token');
    expect(socketService.isConnected()).toBe(false);

    socketMock.connected = true;
    expect(socketService.isConnected()).toBe(true);
  });

  it('join/leave/send should emit expected events', () => {
    socketService.connect('token');

    socketService.joinGroup(8);
    socketService.leaveGroup(8);
    socketService.sendMessage(8, 'hello');

    expect(socketMock.emit).toHaveBeenCalledWith('group:join', { group_id: 8 });
    expect(socketMock.emit).toHaveBeenCalledWith('group:leave', { group_id: 8 });
    expect(socketMock.emit).toHaveBeenCalledWith('group:send-message', { group_id: 8, content: 'hello' });
  });

  it('on/off helpers should bind expected event names', () => {
    socketService.connect('token');
    const handler = vi.fn();

    socketService.onConnect(handler);
    socketService.offConnect(handler);
    socketService.onDisconnect(handler);
    socketService.offDisconnect(handler);
    socketService.onReady(handler as never);
    socketService.offReady(handler as never);
    socketService.onGroupMessage(handler as never);
    socketService.offGroupMessage(handler as never);
    socketService.onGroupError(handler as never);
    socketService.offGroupError(handler as never);

    expect(socketMock.on).toHaveBeenCalledWith('connect', handler);
    expect(socketMock.off).toHaveBeenCalledWith('connect', handler);
    expect(socketMock.on).toHaveBeenCalledWith('disconnect', handler);
    expect(socketMock.off).toHaveBeenCalledWith('disconnect', handler);
    expect(socketMock.on).toHaveBeenCalledWith('socket:ready', handler);
    expect(socketMock.off).toHaveBeenCalledWith('socket:ready', handler);
    expect(socketMock.on).toHaveBeenCalledWith('group:new-message', handler);
    expect(socketMock.off).toHaveBeenCalledWith('group:new-message', handler);
    expect(socketMock.on).toHaveBeenCalledWith('group:error', handler);
    expect(socketMock.off).toHaveBeenCalledWith('group:error', handler);
  });

  it('disconnect should close socket and clear singleton state', () => {
    socketService.connect('token');
    socketService.disconnect();

    expect(socketMock.disconnect).toHaveBeenCalledTimes(1);
    expect(socketService.getSocket()).toBeNull();
    expect(socketService.isConnected()).toBe(false);
  });
});
