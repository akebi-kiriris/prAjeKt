import { io, type Socket } from 'socket.io-client';
import type {
  SocketGroupErrorPayload,
  SocketGroupMessagePayload,
  SocketReadyPayload,
} from '../types';

const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';
const socketBase =
  import.meta.env.VITE_SOCKET_URL ||
  (apiBase.endsWith('/api') ? apiBase.slice(0, -4) : apiBase);

let socket: Socket | null = null;

export const socketService = {
  connect(token: string): Socket {
    if (socket) return socket;

    socket = io(socketBase, {
      auth: { token: `Bearer ${token}` },
      transports: ['websocket', 'polling'],
      withCredentials: true,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
    });

    return socket;
  },

  getSocket(): Socket | null {
    return socket;
  },

  isConnected(): boolean {
    return !!socket?.connected;
  },

  disconnect(): void {
    if (!socket) return;
    socket.disconnect();
    socket = null;
  },

  joinGroup(groupId: number): void {
    socket?.emit('group:join', { group_id: groupId });
  },

  leaveGroup(groupId: number): void {
    socket?.emit('group:leave', { group_id: groupId });
  },

  sendMessage(groupId: number, content: string): void {
    socket?.emit('group:send-message', { group_id: groupId, content });
  },

  onConnect(handler: () => void): void {
    socket?.on('connect', handler);
  },

  offConnect(handler: () => void): void {
    socket?.off('connect', handler);
  },

  onDisconnect(handler: () => void): void {
    socket?.on('disconnect', handler);
  },

  offDisconnect(handler: () => void): void {
    socket?.off('disconnect', handler);
  },

  onReady(handler: (payload: SocketReadyPayload) => void): void {
    socket?.on('socket:ready', handler);
  },

  offReady(handler: (payload: SocketReadyPayload) => void): void {
    socket?.off('socket:ready', handler);
  },

  onGroupMessage(handler: (payload: SocketGroupMessagePayload) => void): void {
    socket?.on('group:new-message', handler);
  },

  offGroupMessage(handler: (payload: SocketGroupMessagePayload) => void): void {
    socket?.off('group:new-message', handler);
  },

  onGroupError(handler: (payload: SocketGroupErrorPayload) => void): void {
    socket?.on('group:error', handler);
  },

  offGroupError(handler: (payload: SocketGroupErrorPayload) => void): void {
    socket?.off('group:error', handler);
  },
};
