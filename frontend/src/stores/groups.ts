import { defineStore } from 'pinia';
import { ref, nextTick } from 'vue';
import type { Group, Message } from '../types';
import { groupService } from '../services/groupService';

type ScrollCallback = () => void;

export const useGroupStore = defineStore('groups', () => {
  const groups = ref<Group[]>([]);
  const currentGroup = ref<Group | null>(null);
  const messages = ref<Message[]>([]);
  const loading = ref(false);

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
      currentGroup.value = null;
      messages.value = [];
    }
  }

  async function openChat(group: Group, scrollCallback?: ScrollCallback): Promise<void> {
    currentGroup.value = group;
    await fetchMessages(group.group_id, scrollCallback);
  }

  function closeChat(): void {
    currentGroup.value = null;
    messages.value = [];
  }

  async function fetchMessages(groupId: number, scrollCallback?: ScrollCallback): Promise<void> {
    try {
      const response = await groupService.getMessages(groupId);
      messages.value = response.data;
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
    await groupService.sendMessage(currentGroup.value.group_id, content);
    await fetchMessages(currentGroup.value.group_id, scrollCallback);
  }

  return {
    groups,
    currentGroup,
    messages,
    loading,
    fetchGroups,
    createGroup,
    joinGroup,
    leaveGroup,
    openChat,
    closeChat,
    fetchMessages,
    sendMessage,
  };
});
