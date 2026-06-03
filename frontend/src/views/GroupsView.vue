<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <div class="mx-auto grid w-full max-w-6xl grid-cols-1 gap-6">
      <header
        class="overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-br from-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]"
      >
        <div class="relative px-5 py-5 md:px-6 md:py-6">
          <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />
          <div class="relative flex flex-wrap items-center justify-between gap-4">
            <div>
              <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
                TEAM CHAT HUB
              </p>
              <h1 class="text-[clamp(1.45rem,2.2vw,2rem)] font-black tracking-[0.01em] text-slate-900">群組訊息</h1>
              <p class="mt-2 text-sm leading-6 text-slate-600">與團隊即時交流互動，並快速生成知識快照。</p>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center shadow-sm">
                <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">群組數量</p>
                <p class="text-xl font-extrabold text-slate-800">{{ groups.length }}</p>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center shadow-sm">
                <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">目前訊息</p>
                <p class="text-xl font-extrabold text-slate-800">{{ messages.length }}</p>
              </div>
            </div>
          </div>
        </div>
      </header>
    
    <!-- Action Bar -->
    <div class="flex flex-wrap justify-center gap-3">
      <button 
        @click="showCreateGroup = true"
        class="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.3)]"
      >
        建立群組
      </button>
      <button 
        @click="showJoinGroup = true"
        class="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
      >
        加入群組
      </button>
    </div>
    
    <!-- Create Group Modal -->
    <div v-if="showCreateGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showCreateGroup = false">
      <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <h3 class="mb-6 text-xl font-semibold text-slate-800">建立新群組</h3>
        <div class="relative mb-6">
          <input 
            v-model="newGroupName"
            type="text" 
            placeholder="請輸入群組名稱"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
          />
        </div>
        <div class="flex gap-3">
          <button 
            @click="showCreateGroup = false"
            class="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            取消
          </button>
          <button 
            @click="handleCreateGroup"
            class="flex-1 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_24px_rgba(37,99,235,0.33)]"
          >
            建立
          </button>
        </div>
      </div>
    </div>
    
    <!-- Join Group Modal -->
    <div v-if="showJoinGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="showJoinGroup = false">
      <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <h3 class="mb-6 text-xl font-semibold text-slate-800">加入群組</h3>
        <div class="relative mb-6">
          <input 
            v-model="inviteCode"
            type="text" 
            placeholder="請輸入六位數邀請碼"
            maxlength="6"
            class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
          />
        </div>
        <div class="flex gap-3">
          <button 
            @click="showJoinGroup = false"
            class="flex-1 rounded-xl border border-slate-300 bg-white px-4 py-3 font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            取消
          </button>
          <button 
            @click="handleJoinGroup"
            class="flex-1 rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_24px_rgba(37,99,235,0.33)]"
          >
            加入
          </button>
        </div>
      </div>
    </div>
    
    <!-- Group List -->
    <div class="pb-8">
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div 
          v-for="group in groups" 
          :key="group.group_id" 
          class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_26px_rgba(15,23,42,0.06)] transition hover:-translate-y-px hover:shadow-[0_16px_30px_rgba(15,23,42,0.08)]"
        >
          <div>
            <h3 class="mb-4 truncate text-lg font-bold text-slate-800">
              {{ group.group_name }}
            </h3>
            
            <div class="space-y-2 text-sm text-slate-600">
              <p class="flex items-center gap-2">
                <strong>邀請碼：</strong>
                <span class="rounded-full bg-amber-100 px-2.5 py-1 font-mono text-amber-700">
                  {{ group.invite_code }}
                </span>
              </p>
              <p class="text-xs text-slate-500">
                建立於 {{ formatDate(group.created_at) }}
              </p>
            </div>
            
            <div class="mt-4 space-y-2 border-t border-slate-200 pt-4">
              <div class="flex gap-2">
                <button 
                  @click="openChat(group)"
                  class="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
                >
                  開啟聊天
                </button>
                <button 
                  @click="leaveGroup(group.group_id)"
                  class="rounded-lg border border-red-200 bg-white px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50"
                >
                  離開
                </button>
              </div>

              <div class="flex gap-2">
                <button
                  @click="generateSnapshot(group.group_id)"
                  :disabled="snapshotLoadingGroupId === group.group_id"
                  class="flex-1 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:bg-slate-300"
                >
                  生成快照
                </button>
                <button
                  @click="viewLatestSnapshot(group.group_id)"
                  :disabled="snapshotLoadingGroupId === group.group_id"
                  class="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  最新快照
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="groups.length === 0" class="rounded-3xl border border-dashed border-slate-300 bg-white py-16 text-center shadow-[0_12px_28px_rgba(15,23,42,0.06)]">
        <p class="text-lg font-semibold text-slate-700">目前尚未加入任何群組</p>
        <p class="mt-1 text-sm text-slate-500">可以先建立一個群組，或輸入邀請碼加入。</p>
      </div>
    </div>
    
    <!-- Chat Modal -->
    <div v-if="currentGroup" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="closeChat">
      <div class="flex h-[80vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-200 p-4">
          <h3 class="text-lg font-bold text-slate-800">{{ currentGroup?.group_name }}</h3>
          <button @click="closeChat" class="text-2xl text-slate-400 transition hover:text-slate-600">✕</button>
        </div>

        <div v-if="lastSocketError" class="mx-4 mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-800">
          即時連線異常：{{ lastSocketError }}，將自動回退至 REST。
        </div>
        
        <div class="flex-1 overflow-y-auto bg-slate-50 p-4" ref="messagesContainer">
          <div v-for="msg in messages" :key="msg.message_id" class="mb-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
            <div class="mb-1 flex items-center gap-2 text-sm font-semibold text-primary">
              {{ msg.sender_name }}
            </div>
            <p class="mb-1 text-slate-800">{{ msg.content }}</p>
            <div class="text-xs text-slate-400">
              {{ formatDateTime(msg.created_at) }}
            </div>
          </div>
          
          <div v-if="messages.length === 0" class="py-8 text-center text-slate-400">
            <p>目前沒有訊息</p>
          </div>
        </div>
        
        <div class="border-t border-slate-200 p-4">
          <div class="flex gap-2">
            <input 
              v-model="newMessage"
              type="text" 
              placeholder="輸入訊息..."
              @keyup.enter="sendMessage"
              class="flex-1 rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
            />
            <button 
              @click="sendMessage"
              class="rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:brightness-110"
            >
              送出
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Snapshot Modal -->
    <div v-if="showSnapshotModal && snapshotPreview" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="closeSnapshotModal">
      <div class="flex max-h-[85vh] w-full max-w-3xl flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
        <div class="flex items-center justify-between border-b border-slate-200 p-4">
          <div>
            <h3 class="text-xl font-semibold text-slate-800">群組知識快照</h3>
            <p class="mt-1 text-sm text-slate-500">來源訊息：{{ snapshotPreview.source_count }} 則</p>
          </div>
          <button @click="closeSnapshotModal" class="text-2xl text-slate-400 transition hover:text-slate-600">✕</button>
        </div>

        <div class="space-y-4 overflow-y-auto bg-slate-50 p-4">
          <section class="rounded-xl border border-slate-200 bg-white p-4">
            <h4 class="mb-2 font-semibold text-slate-800">一句重點</h4>
            <p class="text-sm text-slate-700">{{ snapshotDigestOverview || '目前沒有足夠訊息產出重點。' }}</p>
          </section>

          <section class="rounded-xl border border-slate-200 bg-white p-4">
            <h4 class="mb-2 font-semibold text-slate-800">你現在要做什麼</h4>
            <ul v-if="snapshotTodoItems.length > 0" class="space-y-2 text-sm text-slate-700">
              <li
                v-for="(item, index) in snapshotTodoItems"
                :key="`todo-${index}-${item.text}`"
                class="border-l-4 border-amber-400 pl-3"
              >
                <div class="font-medium">{{ index + 1 }}. {{ item.text }}</div>
                <div class="text-xs text-slate-500">負責人：{{ item.assignee || '未指定' }}</div>
                <div class="text-xs text-slate-500">來源 message_ids: {{ item.message_ids?.join(', ') || '無' }}</div>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">目前沒有明確行動項，建議先在群組補充具體下一步。</p>
          </section>

          <section class="rounded-xl border border-slate-200 bg-white p-4">
            <h4 class="mb-2 font-semibold text-slate-800">目前阻塞/風險</h4>
            <ul v-if="snapshotWatchOutItems.length > 0" class="space-y-2 text-sm text-slate-700">
              <li
                v-for="(item, index) in snapshotWatchOutItems"
                :key="`risk-${index}-${item.text}`"
                class="border-l-4 border-red-400 pl-3"
              >
                <div class="font-medium">{{ item.text }}</div>
                <div class="text-xs text-slate-500">來源 message_ids: {{ item.message_ids?.join(', ') || '無' }}</div>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">目前未偵測到明確阻塞。</p>
          </section>

          <section class="rounded-xl border border-slate-200 bg-white p-4">
            <h4 class="mb-2 font-semibold text-slate-800">已有共識（精簡）</h4>
            <ul v-if="snapshotDecisionItems.length > 0" class="space-y-2 text-sm text-slate-700">
              <li
                v-for="(item, index) in snapshotDecisionItems"
                :key="`decision-${index}-${item.text}`"
                class="border-l-4 border-green-400 pl-3"
              >
                <div class="font-medium">{{ item.text }}</div>
                <div class="text-xs text-slate-500">來源 message_ids: {{ item.message_ids?.join(', ') || '無' }}</div>
              </li>
            </ul>
            <p v-else class="text-sm text-slate-500">目前尚未形成明確決議。</p>
          </section>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue';
import type { Ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { toast } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useGroupStore } from '../stores/groups';
import { groupService } from '../services/groupService';
import { formatDate, formatDateTime } from '../utils/formatters';
import { useConfirm } from '../composables/useConfirm';
import { getApiErrorMessage } from '../utils/apiError';
import type {
  Group,
  Message,
  GroupCreateResponse,
  GroupSnapshotResponse,
  GroupSnapshotJobStatus,
} from '../types';

const { confirm } = useConfirm();

const groupStore = useGroupStore();
const route = useRoute();
const router = useRouter();

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
    toast.error(getApiErrorMessage(error, '建立群組失敗'));
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
    toast.error(getApiErrorMessage(error, '加入群組失敗'));
  }
};

const openChat = async (group: Group) => {
  const storeGroup = group as unknown as Parameters<typeof groupStore.openChat>[0];
  await groupStore.openChat(storeGroup, scrollToBottom);
  await router.replace({ query: { ...route.query, group_id: String(group.group_id) } });
};

const closeChat = () => {
  groupStore.closeChat();
  const nextQuery = { ...route.query };
  delete nextQuery.group_id;
  void router.replace({ query: nextQuery });
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
    toast.error(getApiErrorMessage(error, (error as Error).message || '生成群組快照失敗'));
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
    toast.error(getApiErrorMessage(error, '取得最新快照失敗'));
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
    toast.error(getApiErrorMessage(error, '發送訊息失敗'));
  }
};

const leaveGroup = async (groupId: number) => {
  if (!await confirm({ title: '確定要離開此群組？', danger: true })) return;
  try {
    await groupStore.leaveGroup(groupId);
    toast.success('已離開群組');
  } catch (error) {
    toast.error(getApiErrorMessage(error, '離開群組失敗'));
  }
};

onMounted(() => {
  void groupStore.fetchGroups();
});

onUnmounted(() => {
  groupStore.destroySocket();
});
</script>
