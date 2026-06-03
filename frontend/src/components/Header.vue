<template>
  <header class="fixed top-0 left-0 right-0 z-50 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-3 backdrop-blur md:px-8">
    <div class="flex items-center">
      <!-- 漢堡選單按鈕（僅桌面版顯示，手機版使用底部導航列） -->
      <button @click="$emit('toggle-sidebar')" class="mr-4 hidden rounded-xl p-1.5 transition-colors hover:cursor-pointer hover:bg-slate-100 md:block">
        <svg class="w-8 h-8 text-slate-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <!-- prAjeKt 文字 logo -->
      <span class="ml-2 select-none text-2xl font-black tracking-[0.06em] text-primary">PrAjeKt</span>
    </div>
    
    <div class="mr-2 flex items-center gap-2 md:mr-16 md:gap-4">
      <!-- 通知鈴鐺 -->
      <div class="relative" ref="notifRef">
        <button @click.stop="toggleNotifPanel" class="relative rounded-xl p-2 transition-colors hover:bg-slate-100">
          <svg class="w-6 h-6 text-slate-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <!-- 未讀紅點 -->
          <span v-if="hasUnread" class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <!-- 通知下拉面板 -->
        <div v-if="showNotifPanel" class="absolute right-0 top-12 z-50 w-[min(22rem,calc(100vw-1rem))] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_18px_32px_rgba(15,23,42,0.14)]">
          <div class="border-b border-slate-200 px-4 py-3">
            <div class="mb-2 flex items-center justify-between">
              <span class="font-semibold text-slate-800">通知中心</span>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">
                未讀 {{ unreadCount }}
              </span>
            </div>
            <div class="flex items-center justify-between gap-2">
              <div class="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-1">
                <button
                  @click="notifFilter = 'all'"
                  class="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                  :class="notifFilter === 'all' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                >
                  全部
                </button>
                <button
                  @click="notifFilter = 'unread'"
                  class="rounded-md px-2.5 py-1 text-xs font-medium transition-colors"
                  :class="notifFilter === 'unread' ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
                >
                  未讀
                </button>
              </div>
              <div class="flex items-center gap-1">
                <button @click="refreshNotifications" class="rounded-md px-2 py-1 text-xs text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700">
                  刷新
                </button>
                <button @click="markAllAsReadInPanel" :disabled="unreadCount === 0 || notifActionLoading" class="rounded-md px-2 py-1 text-xs text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
                  全部已讀
                </button>
                <button @click="clearReadNotifications" :disabled="readCountInPanel === 0 || notifActionLoading" class="rounded-md px-2 py-1 text-xs text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700 disabled:cursor-not-allowed disabled:opacity-40">
                  清除已讀
                </button>
              </div>
            </div>
          </div>

          <div class="max-h-96 overflow-y-auto">
            <div v-if="notifLoading" class="py-10 text-center text-sm text-slate-400">載入通知中...</div>
            <div v-else-if="filteredNotifications.length === 0" class="py-10 text-center text-sm text-slate-400">
              {{ notifFilter === 'unread' ? '目前沒有未讀通知' : '目前沒有通知' }}
            </div>
            <div
              v-for="n in filteredNotifications"
              :key="n.id"
              @click="handleNotifClick(n)"
              class="group flex cursor-pointer items-start gap-3 border-b border-slate-100 px-4 py-3 transition-colors hover:bg-slate-50 last:border-b-0"
              :class="{ 'bg-blue-50/60': !n.is_read }"
            >
              <span class="mt-0.5 text-xl">{{ notifIcon(n.type) }}</span>
              <div class="min-w-0 flex-1">
                <div class="mb-1 flex items-start justify-between gap-2">
                  <p class="truncate text-sm font-medium text-slate-800">{{ n.title }}</p>
                  <span v-if="!n.is_read" class="shrink-0 rounded-full bg-blue-100 px-1.5 py-0.5 text-[10px] font-semibold text-blue-600">NEW</span>
                </div>
                <p v-if="n.content" class="line-clamp-2 text-xs text-slate-500">{{ n.content }}</p>
                <p class="mt-1 text-xs text-slate-400">{{ formatTimeAgo(n.created_at) }}</p>
              </div>
              <button
                @click.stop="store.deleteNotification(n.id)"
                class="ml-1 mt-0.5 text-xs text-slate-300 transition-colors hover:text-red-400 md:opacity-0 md:group-hover:opacity-100"
              >✕</button>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 md:gap-8">
        <span 
          class="hidden md:block text-slate-600 text-lg hover:cursor-pointer hover:text-primary transition-colors"
          @click="router.push('/profile')">{{ userName }}</span>
        <button
          @click="$emit('logout')"
          class="cursor-pointer rounded-xl bg-red-500 px-3 py-2 font-medium text-white transition-colors hover:bg-red-600 active:scale-95 md:px-8"
        >
          登出
        </button>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import { useNotificationStore } from '../stores/notifications';
import { storeToRefs } from 'pinia';
import type { Notification, NotificationType } from '../types';

const authStore = useAuthStore();
const store = useNotificationStore();
const router = useRouter();
const { notifications, hasUnread, unreadCount } = storeToRefs(store);

const userName = computed(() => authStore.currentUser?.name || '使用者');
const showNotifPanel = ref(false);
const notifRef = ref<HTMLElement | null>(null);
const notifLoading = ref(false);
const notifActionLoading = ref(false);
const notifFilter = ref<'all' | 'unread'>('all');
let pollInterval: ReturnType<typeof setInterval> | null = null;

const filteredNotifications = computed(() => {
  if (notifFilter.value === 'unread') {
    return notifications.value.filter((n) => !n.is_read);
  }
  return notifications.value;
});

const readCountInPanel = computed(() => notifications.value.filter((n) => n.is_read).length);

defineEmits<{
  (e: 'logout'): void;
  (e: 'toggle-sidebar'): void;
}>();

const toggleNotifPanel = async () => {
  showNotifPanel.value = !showNotifPanel.value;
  if (showNotifPanel.value) {
    await refreshNotifications();
  }
};

const refreshNotifications = async () => {
  notifLoading.value = true;
  try {
    await Promise.all([store.fetchNotifications(), store.fetchUnreadCount()]);
  } finally {
    notifLoading.value = false;
  }
};

const markAllAsReadInPanel = async () => {
  if (unreadCount.value === 0) return;
  notifActionLoading.value = true;
  try {
    await store.markAllAsRead();
  } finally {
    notifActionLoading.value = false;
  }
};

const clearReadNotifications = async () => {
  const readItems = notifications.value.filter((n) => n.is_read);
  if (readItems.length === 0) return;
  notifActionLoading.value = true;
  try {
    await Promise.all(readItems.map((n) => store.deleteNotification(n.id)));
  } finally {
    notifActionLoading.value = false;
  }
};

const handleNotifClick = async (n: Notification) => {
  if (!n.is_read) await store.markAsRead(n.id);
  if (n.link) router.push(n.link);
  showNotifPanel.value = false;
};

const notifIcon = (type: NotificationType | string) => ({
  task_assigned: '📋',
  comment: '💬',
  deadline: '⏰',
  mention: '👤',
  timeline_invited: '👥',
}[type] || '🔔');

const formatTimeAgo = (isoStr?: string | null) => {
  if (!isoStr) return '';
  const diff = Math.floor((Date.now() - new Date(isoStr).getTime()) / 1000);
  if (diff < 60) return '剛剛';
  if (diff < 3600) return `${Math.floor(diff / 60)} 分鐘前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} 小時前`;
  return `${Math.floor(diff / 86400)} 天前`;
};

// 點擊面板外關閉
const onClickOutside = (e: MouseEvent) => {
  if (notifRef.value && !notifRef.value.contains(e.target as Node)) {
    showNotifPanel.value = false;
  }
};

onMounted(() => {
  document.addEventListener('click', onClickOutside);
  void store.fetchUnreadCount();
  pollInterval = setInterval(() => {
    void store.fetchUnreadCount();
  }, 30000);
});

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside);
  if (pollInterval) {
    clearInterval(pollInterval);
    pollInterval = null;
  }
});
</script>
