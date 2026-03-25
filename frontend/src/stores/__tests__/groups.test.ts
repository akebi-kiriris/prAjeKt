import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';

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
    mockedGroupService.create.mockResolvedValueOnce({ data: { group_id: 5, name: 'New Group' } });
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

    expect(created).toEqual({ group_id: 5, name: 'New Group' });
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
});
