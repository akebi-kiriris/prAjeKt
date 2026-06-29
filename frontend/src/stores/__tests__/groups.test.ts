import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

const socketCallbacks = vi.hoisted(() => ({
  connect: null as null | (() => void),
  disconnect: null as null | (() => void),
  ready: null as null | ((payload: { user_id?: number | null }) => void),
  groupMessage: null as null | ((payload: Record<string, unknown>) => Promise<void>),
  groupError: null as null | ((payload: { message?: string }) => void),
}));

vi.mock('../../services/groupService', () => ({
  groupService: {
    getAll: vi.fn(),
    create: vi.fn(),
    join: vi.fn(),
    leave: vi.fn(),
    getMessages: vi.fn(),
    sendMessage: vi.fn(),
  },
}));

vi.mock('../../services/socketService', () => ({
  socketService: {
    connect: vi.fn(),
    disconnect: vi.fn(),
    isConnected: vi.fn(),
    getSocket: vi.fn(),
    joinGroup: vi.fn(),
    leaveGroup: vi.fn(),
    sendMessage: vi.fn(),
    onConnect: vi.fn(),
    onDisconnect: vi.fn(),
    onReady: vi.fn(),
    onGroupMessage: vi.fn(),
    onGroupError: vi.fn(),
    offConnect: vi.fn(),
    offDisconnect: vi.fn(),
    offReady: vi.fn(),
    offGroupMessage: vi.fn(),
    offGroupError: vi.fn(),
  },
}));

import { useGroupStore } from '../groups';
import { groupService } from '../../services/groupService';
import { socketService } from '../../services/socketService';

const mockedGroupService = groupService as unknown as Record<string, ReturnType<typeof vi.fn>>;
const mockedSocketService = socketService as unknown as Record<string, ReturnType<typeof vi.fn>>;

describe('group store', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    localStorage.clear();
    mockedSocketService.isConnected.mockReturnValue(false);
    mockedSocketService.getSocket.mockReturnValue(null);
    socketCallbacks.connect = null;
    socketCallbacks.disconnect = null;
    socketCallbacks.ready = null;
    socketCallbacks.groupMessage = null;
    socketCallbacks.groupError = null;
    mockedSocketService.onConnect.mockImplementation((callback) => {
      socketCallbacks.connect = callback;
    });
    mockedSocketService.onDisconnect.mockImplementation((callback) => {
      socketCallbacks.disconnect = callback;
    });
    mockedSocketService.onReady.mockImplementation((callback) => {
      socketCallbacks.ready = callback;
    });
    mockedSocketService.onGroupMessage.mockImplementation((callback) => {
      socketCallbacks.groupMessage = callback;
    });
    mockedSocketService.onGroupError.mockImplementation((callback) => {
      socketCallbacks.groupError = callback;
    });
  });

  it('fetchGroups should set groups and loading', async () => {
    mockedGroupService.getAll.mockResolvedValueOnce({ data: [{ group_id: 1, name: 'G1' }] });

    const store = useGroupStore();
    await store.fetchGroups();

    expect(store.groups).toEqual([{ group_id: 1, name: 'G1' }]);
    expect(store.loading).toBe(false);
  });

  it('fetchGroups should throw on error and clear loading', async () => {
    mockedGroupService.getAll.mockRejectedValueOnce(new Error('x'));

    const store = useGroupStore();
    await expect(store.fetchGroups()).rejects.toThrow('x');
    expect(store.loading).toBe(false);
  });

  it('create/join/leave group should call service then refetch', async () => {
    mockedGroupService.create.mockResolvedValueOnce({ data: { message: '任務小組已創建', group_id: 5, invite_code: 'INV123' } });
    mockedGroupService.join.mockResolvedValueOnce({});
    mockedGroupService.leave.mockResolvedValueOnce({});
    mockedGroupService.getAll
      .mockResolvedValueOnce({ data: [{ group_id: 5, name: 'New Group' }] })
      .mockResolvedValueOnce({ data: [{ group_id: 5, name: 'New Group' }] })
      .mockResolvedValueOnce({ data: [] });

    const store = useGroupStore();
    const created = await store.createGroup('New Group');
    await store.joinGroup('INV123');
    await store.leaveGroup(5);

    expect(created).toEqual({ message: '任務小組已創建', group_id: 5, invite_code: 'INV123' });
    expect(mockedGroupService.create).toHaveBeenCalledWith('New Group');
    expect(mockedGroupService.join).toHaveBeenCalledWith('INV123');
    expect(mockedGroupService.leave).toHaveBeenCalledWith(5);
    expect(mockedGroupService.getAll).toHaveBeenCalledTimes(3);
  });

  it('openChat should connect socket, fetch messages and join room', async () => {
    localStorage.setItem('access_token', 'token-a');
    mockedSocketService.isConnected.mockReturnValue(true);
    mockedGroupService.getMessages.mockResolvedValueOnce({
      data: [{ message_id: 1, content: 'hi', created_at: '2026-03-25T00:00:00Z' }],
    });

    const store = useGroupStore();
    const group = { group_id: 10, name: 'Team' } as never;
    await store.openChat(group);

    expect(mockedSocketService.connect).toHaveBeenCalledWith('token-a');
    expect(mockedGroupService.getMessages).toHaveBeenCalledWith(10);
    expect(mockedSocketService.joinGroup).toHaveBeenCalledWith(10);
    expect(store.currentGroup?.group_id).toBe(10);
    expect(store.activeRoomId).toBe(10);
  });

  it('sendMessage should prefer socket and fallback to http when socket unavailable', async () => {
    const store = useGroupStore();
    store.currentGroup = { group_id: 9, name: 'X' } as never;

    mockedSocketService.getSocket.mockReturnValue({ id: 's1' });
    mockedSocketService.isConnected.mockReturnValue(true);
    await store.sendMessage('hello');
    expect(mockedSocketService.sendMessage).toHaveBeenCalledWith(9, 'hello');

    mockedSocketService.getSocket.mockReturnValue(null);
    mockedGroupService.sendMessage.mockResolvedValueOnce({});
    mockedGroupService.getMessages.mockResolvedValueOnce({ data: [] });
    await store.sendMessage('world');

    expect(mockedGroupService.sendMessage).toHaveBeenCalledWith(9, 'world');
    expect(mockedGroupService.getMessages).toHaveBeenCalledWith(9);
  });

  it('closeChat and destroySocket should cleanup state and handlers', async () => {
    localStorage.setItem('access_token', 'token-a');
    mockedSocketService.isConnected.mockReturnValue(true);
    mockedGroupService.getMessages.mockResolvedValueOnce({ data: [] });

    const store = useGroupStore();
    await store.openChat({ group_id: 8, name: 'G8' } as never);
    store.closeChat();

    expect(store.currentGroup).toBeNull();
    expect(store.messages).toEqual([]);

    store.destroySocket();
    expect(mockedSocketService.disconnect).toHaveBeenCalled();
    expect(store.socketConnected).toBe(false);
    expect(store.socketReady).toBe(false);
  });

  it('loads messages over HTTP but does not connect or join without an access token', async () => {
    mockedGroupService.getMessages.mockResolvedValueOnce({ data: [] });
    const store = useGroupStore();

    await store.openChat({ group_id: 20, name: 'No Token' } as never);

    expect(mockedGroupService.getMessages).toHaveBeenCalledWith(20);
    expect(mockedSocketService.connect).not.toHaveBeenCalled();
    expect(mockedSocketService.joinGroup).not.toHaveBeenCalled();
    expect(store.currentGroup?.group_id).toBe(20);
    expect(store.activeRoomId).toBeNull();
  });

  it('deduplicates socket messages, ignores other rooms and keeps messages sorted', async () => {
    localStorage.setItem('access_token', 'token-a');
    mockedSocketService.isConnected.mockReturnValue(true);
    mockedGroupService.getMessages.mockResolvedValueOnce({
      data: [{ message_id: 2, group_id: 10, content: 'later', created_at: '2026-06-25T10:00:00Z' }],
    });
    const scrollCallback = vi.fn();
    const store = useGroupStore();
    await store.openChat({ group_id: 10, name: 'Team' } as never, scrollCallback);

    expect(socketCallbacks.groupMessage).toBeTypeOf('function');
    await socketCallbacks.groupMessage?.({
      message_id: 2,
      group_id: 10,
      content: 'duplicate',
      created_at: '2026-06-25T10:00:00Z',
    });
    await socketCallbacks.groupMessage?.({
      message_id: 3,
      group_id: 99,
      content: 'other room',
      created_at: '2026-06-25T08:00:00Z',
    });
    await socketCallbacks.groupMessage?.({
      message_id: 1,
      group_id: 10,
      content: 'earlier',
      created_at: '2026-06-25T09:00:00Z',
    });

    expect(store.messages).toHaveLength(2);
    expect(store.messages.map((message) => message.message_id)).toEqual([1, 2]);
    expect(store.messages.map((message) => message.content)).not.toContain('other room');
    expect(scrollCallback).toHaveBeenCalledTimes(2);

    store.closeChat();
    await socketCallbacks.groupMessage?.({
      message_id: 4,
      group_id: 10,
      content: 'after close',
      created_at: '2026-06-25T11:00:00Z',
    });
    expect(store.messages).toEqual([]);
  });

  it('updates connection, ready and error state from socket callbacks', async () => {
    localStorage.setItem('access_token', 'token-a');
    mockedGroupService.getMessages.mockResolvedValueOnce({ data: [] });
    const store = useGroupStore();
    await store.openChat({ group_id: 10, name: 'Team' } as never);

    socketCallbacks.connect?.();
    expect(store.socketConnected).toBe(true);

    socketCallbacks.ready?.({ user_id: 12 });
    expect(store.socketReady).toBe(true);

    socketCallbacks.groupError?.({ message: '房間權限不足' });
    expect(store.lastSocketError).toBe('房間權限不足');

    socketCallbacks.disconnect?.();
    expect(store.socketConnected).toBe(false);
    expect(store.socketReady).toBe(false);

    socketCallbacks.groupError?.({});
    expect(store.lastSocketError).toBe('Socket 發生錯誤');
  });

  it('destroySocket leaves the room and unregisters the captured handlers', async () => {
    localStorage.setItem('access_token', 'token-a');
    mockedSocketService.isConnected.mockReturnValue(true);
    mockedGroupService.getMessages.mockResolvedValueOnce({ data: [] });
    const store = useGroupStore();
    await store.openChat({ group_id: 10, name: 'Team' } as never);
    socketCallbacks.connect?.();
    socketCallbacks.ready?.({ user_id: 12 });
    socketCallbacks.groupError?.({ message: 'temporary' });

    store.destroySocket();

    expect(mockedSocketService.leaveGroup).toHaveBeenCalledWith(10);
    expect(mockedSocketService.offConnect).toHaveBeenCalledWith(socketCallbacks.connect);
    expect(mockedSocketService.offDisconnect).toHaveBeenCalledWith(socketCallbacks.disconnect);
    expect(mockedSocketService.offReady).toHaveBeenCalledWith(socketCallbacks.ready);
    expect(mockedSocketService.offGroupMessage).toHaveBeenCalledWith(socketCallbacks.groupMessage);
    expect(mockedSocketService.offGroupError).toHaveBeenCalledWith(socketCallbacks.groupError);
    expect(mockedSocketService.disconnect).toHaveBeenCalled();
    expect(store.activeRoomId).toBeNull();
    expect(store.socketConnected).toBe(false);
    expect(store.socketReady).toBe(false);
    expect(store.lastSocketError).toBeNull();
  });
});
