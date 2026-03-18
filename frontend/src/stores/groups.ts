import { defineStore } from 'pinia';
import { ref, nextTick } from 'vue';
import type {
  Group,
  Message,
  SocketGroupErrorPayload,
  SocketGroupMessagePayload,
  SocketReadyPayload,
} from '../types';
import { groupService } from '../services/groupService';
import { socketService } from '../services/socketService';

type ScrollCallback = () => void;

export const useGroupStore = defineStore('groups', () => {
  const groups = ref<Group[]>([]);
  const currentGroup = ref<Group | null>(null);
  const messages = ref<Message[]>([]);
  const loading = ref(false);
  const socketConnected = ref(false);
  const socketReady = ref(false);
  const activeRoomId = ref<number | null>(null);
  const lastSocketError = ref<string | null>(null);

  const messageIdSet = new Set<number>();
  const activeScrollCallback = ref<ScrollCallback | null>(null);

  let isSocketHandlersBound = false;

  const onSocketConnect = (): void => {
    socketConnected.value = true;
  };

  const onSocketDisconnect = (): void => {
    socketConnected.value = false;
    socketReady.value = false;
  };

  const onSocketReady = (payload: SocketReadyPayload): void => {
    socketReady.value = !!payload?.user_id;
  };

  const appendMessage = async (msg: Message): Promise<void> => {
    if (msg.message_id && messageIdSet.has(msg.message_id)) {
      return;
    }

    if (msg.message_id) messageIdSet.add(msg.message_id);
    messages.value.push(msg);
    messages.value.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());

    if (activeScrollCallback.value) {
      await nextTick();
      activeScrollCallback.value();
    }
  };

  const onSocketGroupMessage = async (payload: SocketGroupMessagePayload): Promise<void> => {
    if (!currentGroup.value) return;
    if (payload.group_id !== currentGroup.value.group_id) return;
    await appendMessage(payload);
  };

  const onSocketGroupError = (payload: SocketGroupErrorPayload): void => {
    lastSocketError.value = payload?.message || 'Socket 發生錯誤';
  };

  function bindSocketHandlers(): void {
    if (isSocketHandlersBound) return;

    socketService.onConnect(onSocketConnect);
    socketService.onDisconnect(onSocketDisconnect);
    socketService.onReady(onSocketReady);
    socketService.onGroupMessage(onSocketGroupMessage);
    socketService.onGroupError(onSocketGroupError);
    isSocketHandlersBound = true;
  }

  function unbindSocketHandlers(): void {
    if (!isSocketHandlersBound) return;

    socketService.offConnect(onSocketConnect);
    socketService.offDisconnect(onSocketDisconnect);
    socketService.offReady(onSocketReady);
    socketService.offGroupMessage(onSocketGroupMessage);
    socketService.offGroupError(onSocketGroupError);
    isSocketHandlersBound = false;
  }

  function ensureSocketConnection(): boolean {
    const token = localStorage.getItem('access_token');
    if (!token) return false;

    socketService.connect(token);
    bindSocketHandlers();
    socketConnected.value = socketService.isConnected();
    return true;
  }

  function clearMessages(): void {
    messages.value = [];
    messageIdSet.clear();
  }

  function leaveActiveRoom(): void {
    if (activeRoomId.value !== null) {
      socketService.leaveGroup(activeRoomId.value);
      activeRoomId.value = null;
    }
  }

  async function fetchGroups(): Promise<void> {
    loading.value = true;
    try {
      const response = await groupService.getAll();
      groups.value = response.data;
    } catch (error) {
      console.error('取得群組失敗:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function createGroup(name: string): Promise<Group> {
    const response = await groupService.create(name);
    await fetchGroups();
    return response.data;
  }

  async function joinGroup(inviteCode: string): Promise<void> {
    await groupService.join(inviteCode);
    await fetchGroups();
  }

  async function leaveGroup(groupId: number): Promise<void> {
    await groupService.leave(groupId);
    await fetchGroups();
    if (currentGroup.value?.group_id === groupId) {
      closeChat();
    }
  }

  async function openChat(group: Group, scrollCallback?: ScrollCallback): Promise<void> {
    activeScrollCallback.value = scrollCallback || null;

    ensureSocketConnection();
    leaveActiveRoom();

    currentGroup.value = group;
    await fetchMessages(group.group_id, scrollCallback);

    if (socketConnected.value || socketService.getSocket()) {
      socketService.joinGroup(group.group_id);
      activeRoomId.value = group.group_id;
    }
  }

  function closeChat(): void {
    leaveActiveRoom();
    activeScrollCallback.value = null;
    currentGroup.value = null;
    clearMessages();
  }

  async function fetchMessages(groupId: number, scrollCallback?: ScrollCallback): Promise<void> {
    try {
      const response = await groupService.getMessages(groupId);
      messages.value = response.data;
      messageIdSet.clear();
      messages.value.forEach(msg => {
        if (msg.message_id) messageIdSet.add(msg.message_id);
      });

      if (scrollCallback) {
        await nextTick();
        scrollCallback();
      }
    } catch (error) {
      console.error('取得訊息失敗:', error);
    }
  }

  async function sendMessage(content: string, scrollCallback?: ScrollCallback): Promise<void> {
    if (!currentGroup.value) return;

    const trimmed = content.trim();
    if (!trimmed) return;

    activeScrollCallback.value = scrollCallback || null;
    lastSocketError.value = null;

    const canUseSocket = socketService.getSocket() && (socketConnected.value || socketService.isConnected());

    if (canUseSocket) {
      socketService.sendMessage(currentGroup.value.group_id, trimmed);
      return;
    }

    await groupService.sendMessage(currentGroup.value.group_id, trimmed);
    await fetchMessages(currentGroup.value.group_id, scrollCallback);
  }

  function destroySocket(): void {
    leaveActiveRoom();
    unbindSocketHandlers();
    socketService.disconnect();
    socketConnected.value = false;
    socketReady.value = false;
    lastSocketError.value = null;
    activeScrollCallback.value = null;
  }

  return {
    groups,
    currentGroup,
    messages,
    loading,
    socketConnected,
    socketReady,
    activeRoomId,
    lastSocketError,
    fetchGroups,
    createGroup,
    joinGroup,
    leaveGroup,
    openChat,
    closeChat,
    fetchMessages,
    sendMessage,
    destroySocket,
  };
});
