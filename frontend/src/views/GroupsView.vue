<template>
  <div class="h-full w-full bg-gray-50 px-6 pt-6 pb-24 md:pb-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-4xl md:text-6xl mb-4 block animate-pulse-custom">💬</span>
      <h1 class="text-2xl md:text-4xl font-bold mb-2 text-gray-800">群組訊息</h1>
      <p class="text-lg text-gray-600">與團隊即時交流互動</p>
    </div>
    
    <!-- Action Bar -->
    <div class="flex justify-center gap-4 px-4 mb-6">
      <button 
        @click="showCreateGroup = true"
        class="px-6 py-3 bg-linear-to-r from-primary to-primary-light text-white font-semibold rounded-full shadow-lg hover:-translate-y-0.5 hover:shadow-xl transition-all flex items-center gap-2"
      >
        <span>➕</span>
        <span>建立群組</span>
      </button>
      <button 
        @click="showJoinGroup = true"
        class="px-6 py-3 bg-green-500 text-white font-semibold rounded-full shadow-lg hover:-translate-y-0.5 hover:shadow-xl transition-all flex items-center gap-2"
      >
        <span>🔗</span>
        <span>加入群組</span>
      </button>
    </div>
    
    <!-- Create Group Modal -->
    <div v-if="showCreateGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showCreateGroup = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-slideUp">
        <h3 class="text-xl font-semibold text-primary mb-6">建立新群組</h3>
        <div class="relative mb-6">
          <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">💬</span>
          <input 
            v-model="newGroupName"
            type="text" 
            placeholder="請輸入群組名稱"
            class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
          />
        </div>
        <div class="flex gap-3">
          <button 
            @click="showCreateGroup = false"
            class="flex-1 px-4 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all"
          >
            取消
          </button>
          <button 
            @click="handleCreateGroup"
            class="flex-1 px-4 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center justify-center gap-2"
            style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
          >
            <span>✓</span>
            建立
          </button>
        </div>
      </div>
    </div>
    
    <!-- Join Group Modal -->
    <div v-if="showJoinGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showJoinGroup = false">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-slideUp">
        <h3 class="text-xl font-semibold text-primary mb-6">加入群組</h3>
        <div class="relative mb-6">
          <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔑</span>
          <input 
            v-model="inviteCode"
            type="text" 
            placeholder="請輸入六位數邀請碼"
            maxlength="6"
            class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
          />
        </div>
        <div class="flex gap-3">
          <button 
            @click="showJoinGroup = false"
            class="flex-1 px-4 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all"
          >
            取消
          </button>
          <button 
            @click="handleJoinGroup"
            class="flex-1 px-4 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center justify-center gap-2"
            style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
          >
            <span>✓</span>
            加入
          </button>
        </div>
      </div>
    </div>
    
    <!-- Group List -->
    <div class="pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="group in groups" 
          :key="group.group_id" 
          class="bg-white rounded-xl shadow-md hover:-translate-y-1 hover:shadow-xl transition-all animate-fadeIn"
        >
          <div class="p-6">
            <h3 class="text-xl font-semibold text-primary flex items-center gap-2 mb-4">
              <span>💬</span>
              {{ group.group_name }}
            </h3>
            
            <div class="space-y-3 text-gray-600 text-sm">
              <p class="flex items-center gap-2">
                <span>🔑</span>
                <strong>邀請碼：</strong>
                <span class="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full font-mono font-semibold">
                  {{ group.invite_code }}
                </span>
              </p>
              <p class="flex items-center gap-2 text-gray-400">
                <span>⏰</span>
                建立於 {{ formatDate(group.created_at) }}
              </p>
            </div>
            
            <div class="mt-4 pt-4 border-t space-y-2">
              <div class="flex gap-2">
                <button 
                  @click="openChat(group)"
                  class="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center gap-2"
                >
                  <span>💬</span>
                  開啟聊天
                </button>
                <button 
                  @click="leaveGroup(group.group_id)"
                  class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center gap-2"
                >
                  <span>✕</span>
                  離開
                </button>
              </div>

              <div class="flex gap-2">
                <button
                  @click="generateSnapshot(group.group_id)"
                  :disabled="snapshotLoadingGroupId === group.group_id"
                  class="flex-1 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 disabled:bg-indigo-300 transition-colors flex items-center justify-center gap-2"
                >
                  <span>🧠</span>
                  生成快照
                </button>
                <button
                  @click="viewLatestSnapshot(group.group_id)"
                  :disabled="snapshotLoadingGroupId === group.group_id"
                  class="flex-1 px-4 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:bg-amber-300 transition-colors flex items-center justify-center gap-2"
                >
                  <span>📄</span>
                  最新快照
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="groups.length === 0" class="text-center py-16">
        <span class="text-6xl block mb-4">💬</span>
        <p class="text-xl text-gray-600">目前尚未加入任何群組</p>
      </div>
    </div>
    
    <!-- Chat Modal -->
    <div v-if="currentGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="closeChat">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl h-[80vh] flex flex-col animate-slideUp">
        <div class="p-4 border-b flex justify-between items-center">
          <h3 class="text-xl font-semibold text-primary">{{ currentGroup?.group_name }}</h3>
          <button @click="closeChat" class="text-gray-400 hover:text-gray-600 text-2xl">✕</button>
        </div>

        <div v-if="lastSocketError" class="mx-4 mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          即時連線異常：{{ lastSocketError }}，將自動回退至 REST。
        </div>
        
        <div class="flex-1 overflow-y-auto p-4 bg-gray-50" ref="messagesContainer">
          <div v-for="msg in messages" :key="msg.message_id" class="mb-4 p-3 bg-white rounded-lg border-l-4 border-primary">
            <div class="flex items-center gap-2 text-primary font-semibold text-sm mb-1">
              <span>👤</span>
              {{ msg.sender_name }}
            </div>
            <p class="text-gray-800 mb-1">{{ msg.content }}</p>
            <div class="text-xs text-gray-400 flex items-center gap-1">
              <span>⏰</span>
              {{ formatDateTime(msg.created_at) }}
            </div>
          </div>
          
          <div v-if="messages.length === 0" class="text-center py-8 text-gray-400">
            <span class="text-4xl block mb-2">💬</span>
            <p>目前沒有訊息</p>
          </div>
        </div>
        
        <div class="p-4 border-t">
          <div class="flex gap-2">
            <input 
              v-model="newMessage"
              type="text" 
              placeholder="輸入訊息..."
              @keyup.enter="sendMessage"
              class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
            <button 
              @click="sendMessage"
              class="px-6 py-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors"
            >
              📤
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Snapshot Modal -->
    <div v-if="showSnapshotModal && snapshotPreview" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="closeSnapshotModal">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] overflow-hidden flex flex-col animate-slideUp">
        <div class="p-4 border-b flex justify-between items-center">
          <div>
            <h3 class="text-xl font-semibold text-primary">群組知識快照</h3>
            <p class="text-sm text-gray-500 mt-1">來源訊息：{{ snapshotPreview.source_count }} 則</p>
          </div>
          <button @click="closeSnapshotModal" class="text-gray-400 hover:text-gray-600 text-2xl">✕</button>
        </div>

        <div class="p-4 overflow-y-auto space-y-4 bg-gray-50">
          <section class="bg-white rounded-xl border p-4">
            <h4 class="font-semibold text-gray-800 mb-2">🎯 一句重點</h4>
            <p class="text-sm text-gray-700">{{ snapshotDigestOverview || '目前沒有足夠訊息產出重點。' }}</p>
          </section>

          <section class="bg-white rounded-xl border p-4">
            <h4 class="font-semibold text-gray-800 mb-2">🧭 你現在要做什麼</h4>
            <ul v-if="snapshotTodoItems.length > 0" class="space-y-2 text-sm text-gray-700">
              <li
                v-for="(item, index) in snapshotTodoItems"
                :key="`todo-${index}-${item.text}`"
                class="border-l-4 border-amber-400 pl-3"
              >
                <div class="font-medium">{{ index + 1 }}. {{ item.text }}</div>
                <div class="text-xs text-gray-500">負責人：{{ item.assignee || '未指定' }}</div>
                <div class="text-xs text-gray-500">來源 message_ids: {{ item.message_ids?.join(', ') || '無' }}</div>
              </li>
            </ul>
            <p v-else class="text-sm text-gray-500">目前沒有明確行動項，建議先在群組補充具體下一步。</p>
          </section>

          <section class="bg-white rounded-xl border p-4">
            <h4 class="font-semibold text-gray-800 mb-2">⚠️ 目前阻塞/風險</h4>
            <ul v-if="snapshotWatchOutItems.length > 0" class="space-y-2 text-sm text-gray-700">
              <li
                v-for="(item, index) in snapshotWatchOutItems"
                :key="`risk-${index}-${item.text}`"
                class="border-l-4 border-red-400 pl-3"
              >
                <div class="font-medium">{{ item.text }}</div>
                <div class="text-xs text-gray-500">來源 message_ids: {{ item.message_ids?.join(', ') || '無' }}</div>
              </li>
            </ul>
            <p v-else class="text-sm text-gray-500">目前未偵測到明確阻塞。</p>
          </section>

          <section class="bg-white rounded-xl border p-4">
            <h4 class="font-semibold text-gray-800 mb-2">✅ 已有共識（精簡）</h4>
            <ul v-if="snapshotDecisionItems.length > 0" class="space-y-2 text-sm text-gray-700">
              <li
                v-for="(item, index) in snapshotDecisionItems"
                :key="`decision-${index}-${item.text}`"
                class="border-l-4 border-green-400 pl-3"
              >
                <div class="font-medium">{{ item.text }}</div>
                <div class="text-xs text-gray-500">來源 message_ids: {{ item.message_ids?.join(', ') || '無' }}</div>
              </li>
            </ul>
            <p v-else class="text-sm text-gray-500">目前尚未形成明確決議。</p>
          </section>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import type { AxiosError } from 'axios';
import type { Ref } from 'vue';
import { toast } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '../stores/groups';
import { groupService } from '../services/groupService';
import { formatDate, formatDateTime } from '../utils/formatters';
import { useConfirm } from '../composables/useConfirm';
import type {
  Group,
  Message,
  GroupCreateResponse,
  GroupErrorPayload,
  GroupSnapshotResponse,
  GroupSnapshotJobStatus,
} from '../types';

const { confirm } = useConfirm();

const groupStore = useGroupStore();

// ────────────── Store 狀態（響應式解構）──────────────
const {
  groups: storeGroups,
  currentGroup: storeCurrentGroup,
  messages: storeMessages,
  lastSocketError: storeLastSocketError,
} = storeToRefs(groupStore);

const groups = storeGroups as unknown as Ref<Group[]>;
const currentGroup = storeCurrentGroup as unknown as Ref<Group | null>;
const messages = storeMessages as unknown as Ref<Message[]>;
const lastSocketError = storeLastSocketError as unknown as Ref<string | null>;

// ────────────── View-local UI 狀態 ──────────────
const newMessage = ref('');
const newGroupName = ref('');
const inviteCode = ref('');
const showCreateGroup = ref(false);
const showJoinGroup = ref(false);
const messagesContainer = ref<HTMLDivElement | null>(null);
const showSnapshotModal = ref(false);
const snapshotPreview = ref<GroupSnapshotResponse | null>(null);
const snapshotLoadingGroupId = ref<number | null>(null);

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
};

const handleCreateGroup = async () => {
  if (!newGroupName.value.trim()) {
    toast.warning('請輸入群組名稱');
    return;
  }
  try {
    const data = await groupStore.createGroup(newGroupName.value) as unknown as GroupCreateResponse;
    toast.success(`群組建立成功！邀請碼: ${data.invite_code}`);
    showCreateGroup.value = false;
    newGroupName.value = '';
  } catch (error) {
    const message = (error as AxiosError<GroupErrorPayload>).response?.data?.error;
    toast.error(message || '建立群組失敗');
  }
};

const handleJoinGroup = async () => {
  if (!inviteCode.value.trim()) {
    toast.warning('請輸入邀請碼');
    return;
  }
  try {
    await groupStore.joinGroup(inviteCode.value);
    toast.success('成功加入群組');
    showJoinGroup.value = false;
    inviteCode.value = '';
  } catch (error) {
    const message = (error as AxiosError<GroupErrorPayload>).response?.data?.error;
    toast.error(message || '加入群組失敗');
  }
};

const openChat = async (group: Group) => {
  const storeGroup = group as unknown as Parameters<typeof groupStore.openChat>[0];
  await groupStore.openChat(storeGroup, scrollToBottom);
};

const closeChat = () => {
  groupStore.closeChat();
};

const closeSnapshotModal = () => {
  showSnapshotModal.value = false;
  snapshotPreview.value = null;
};

const openSnapshotModal = (payload: GroupSnapshotResponse) => {
  snapshotPreview.value = payload;
  showSnapshotModal.value = true;
};

const snapshotDigestOverview = computed(() => snapshotPreview.value?.summary?.digest?.overview || '');

const snapshotTodoItems = computed(() => {
  const digestItems = snapshotPreview.value?.summary?.digest?.todo_for_user;
  if (Array.isArray(digestItems) && digestItems.length > 0) {
    return digestItems;
  }
  return snapshotPreview.value?.summary?.action_items || [];
});

const snapshotWatchOutItems = computed(() => {
  const digestItems = snapshotPreview.value?.summary?.digest?.watch_out;
  if (Array.isArray(digestItems) && digestItems.length > 0) {
    return digestItems;
  }
  return snapshotPreview.value?.summary?.blockers || [];
});

const snapshotDecisionItems = computed(() => {
  const digestItems = snapshotPreview.value?.summary?.digest?.decisions_brief;
  if (Array.isArray(digestItems) && digestItems.length > 0) {
    return digestItems;
  }
  return snapshotPreview.value?.summary?.decisions || [];
});

const pollSnapshotJob = async (jobId: string): Promise<GroupSnapshotJobStatus> => {
  const maxAttempts = 15;
  const intervalMs = 1000;

  for (let attempt = 0; attempt < maxAttempts; attempt += 1) {
    const response = await groupService.getSnapshotJobStatus(jobId);
    const payload = response.data as GroupSnapshotJobStatus;

    if (payload.status === 'completed') {
      return payload;
    }
    if (payload.status === 'failed') {
      throw new Error(payload.error || '群組快照背景工作失敗');
    }

    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  throw new Error('群組快照背景工作逾時，請稍後再查詢');
};

const generateSnapshot = async (groupId: number) => {
  try {
    snapshotLoadingGroupId.value = groupId;
    const response = await groupService.generateSnapshot(groupId, { window_days: 30, async: false });

    if (response.status === 202) {
      const jobPayload = response.data as GroupSnapshotJobStatus;
      toast.info('群組快照已進入背景工作，正在等待完成...');
      const finalJob = await pollSnapshotJob(jobPayload.job_id);
      if (finalJob.snapshot) {
        openSnapshotModal(finalJob.snapshot);
        toast.success('群組快照生成完成');
      }
      return;
    }

    openSnapshotModal(response.data as GroupSnapshotResponse);
    toast.success('群組快照生成完成');
  } catch (error) {
    const message = (error as AxiosError<GroupErrorPayload>).response?.data?.error || (error as Error).message;
    toast.error(message || '生成群組快照失敗');
  } finally {
    snapshotLoadingGroupId.value = null;
  }
};

const viewLatestSnapshot = async (groupId: number) => {
  try {
    snapshotLoadingGroupId.value = groupId;
    const response = await groupService.getLatestSnapshot(groupId);
    openSnapshotModal(response.data as GroupSnapshotResponse);
  } catch (error) {
    const message = (error as AxiosError<GroupErrorPayload>).response?.data?.error;
    toast.error(message || '取得最新快照失敗');
  } finally {
    snapshotLoadingGroupId.value = null;
  }
};

const sendMessage = async () => {
  if (!newMessage.value.trim()) return;
  try {
    await groupStore.sendMessage(newMessage.value, scrollToBottom);
    newMessage.value = '';
  } catch (error) {
    const message = (error as AxiosError<GroupErrorPayload>).response?.data?.error;
    toast.error(message || '發送訊息失敗');
  }
};

const leaveGroup = async (groupId: number) => {
  if (!await confirm({ title: '確定要離開此群組？', danger: true })) return;
  try {
    await groupStore.leaveGroup(groupId);
    toast.success('已離開群組');
  } catch (error) {
    const message = (error as AxiosError<GroupErrorPayload>).response?.data?.error;
    toast.error(message || '離開群組失敗');
  }
};

onMounted(() => {
  void groupStore.fetchGroups();
});

onUnmounted(() => {
  groupStore.destroySocket();
});
</script>
