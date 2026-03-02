import { defineStore } from 'pinia';
import { ref, nextTick } from 'vue';
import { groupService } from '../services/groupService';

export const useGroupStore = defineStore('groups', () => {
  // ────────────── 狀態 ──────────────
  const groups = ref([]);
  const currentGroup = ref(null);
  const messages = ref([]);
  const loading = ref(false);

  // ────────────── 群組操作 ──────────────
  async function fetchGroups() {
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

  async function createGroup(name) {
    const response = await groupService.create(name);
    await fetchGroups();
    return response.data; // 回傳含 invite_code 的資料
  }

  async function joinGroup(inviteCode) {
    await groupService.join(inviteCode);
    await fetchGroups();
  }

  async function leaveGroup(groupId) {
    await groupService.leave(groupId);
    await fetchGroups();
    if (currentGroup.value?.group_id === groupId) {
      currentGroup.value = null;
      messages.value = [];
    }
  }

  // ────────────── 訊息操作 ──────────────
  async function openChat(group, scrollCallback) {
    currentGroup.value = group;
    await fetchMessages(group.group_id, scrollCallback);
  }

  function closeChat() {
    currentGroup.value = null;
    messages.value = [];
  }

  async function fetchMessages(groupId, scrollCallback) {
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

  async function sendMessage(content, scrollCallback) {
    if (!currentGroup.value) return;
    await groupService.sendMessage(currentGroup.value.group_id, content);
    await fetchMessages(currentGroup.value.group_id, scrollCallback);
  }

  return {
    // 狀態
    groups,
    currentGroup,
    messages,
    loading,
    // 方法
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
