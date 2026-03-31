<template>
  <header class="fixed top-0 left-0 right-0 h-16 bg-white shadow-md flex justify-between items-center z-50 px-3 md:px-8">
    <div class="flex items-center ml">
      <!-- 漢堡選單按鈕（僅桌面版顯示，手機版使用底部導航列） -->
      <button @click="$emit('toggle-sidebar')" class="hidden md:block mr-4 focus:outline-none hover:bg-gray-200 rounded-full p-1 transition-shadow hover:cursor-pointer">
        <svg class="w-8 h-8 text-gray-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <!-- prAjeKt 文字 logo -->
      <span class="text-2xl font-bold text-primary tracking-wider select-none ml-2">PrAjeKt</span>
    </div>
    
    <div class="flex items-center gap-2 md:gap-4 mr-2 md:mr-16">
      <!-- 通知鈴鐺 -->
      <div class="relative" ref="notifRef">
        <button @click.stop="toggleNotifPanel" class="relative p-2 rounded-full hover:bg-gray-100 transition-colors">
          <svg class="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <!-- 未讀紅點 -->
          <span v-if="hasUnread" class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <!-- 通知下拉面板 -->
        <div v-if="showNotifPanel" class="absolute right-0 top-12 w-[min(20rem,calc(100vw-1rem))] bg-white rounded-xl shadow-lg border border-gray-200 z-50">
          <div class="flex justify-between items-center px-4 py-3 border-b">
            <span class="font-semibold text-gray-800">通知</span>
            <button @click="store.markAllAsRead()" class="text-xs text-blue-500 hover:underline">全部已讀</button>
          </div>
          <div class="overflow-y-auto max-h-96">
            <div v-if="notifications.length === 0" class="text-center text-gray-400 py-8 text-sm">沒有通知</div>
            <div
              v-for="n in notifications"
              :key="n.id"
              @click="handleNotifClick(n)"
              class="flex items-start gap-3 px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
              :class="{ 'bg-blue-50': !n.is_read }"
            >
              <span class="text-xl mt-0.5">{{ notifIcon(n.type) }}</span>
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-800 truncate">{{ n.title }}</p>
                <p v-if="n.content" class="text-xs text-gray-500 truncate">{{ n.content }}</p>
                <p class="text-xs text-gray-400 mt-1">{{ formatTimeAgo(n.created_at) }}</p>
              </div>
              <button
                @click.stop="store.deleteNotification(n.id)"
                class="text-gray-300 hover:text-red-400 text-xs ml-1 mt-0.5"
              >✕</button>
            </div>
          </div>
        </div>
      </div>

      <div class="flex items-center gap-2 md:gap-8">
        <span 
          class="hidden md:block text-gray-600 text-lg hover:cursor-pointer hover:text-primary transition-colors"
          @click="router.push('/profile')">{{ userName }}</span>
        <button 
          @click="$emit('logout')" 
          class="px-3 md:px-8 py-2 bg-red-500 text-white rounded-lg font-medium cursor-pointer hover:bg-red-600 transition-colors active:scale-95" 
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
const { notifications, hasUnread } = storeToRefs(store);

const userName = computed(() => authStore.currentUser?.name || '使用者');
const showNotifPanel = ref(false);
const notifRef = ref<HTMLElement | null>(null);
let pollInterval: ReturnType<typeof setInterval> | null = null;

defineEmits<{
  (e: 'logout'): void;
  (e: 'toggle-sidebar'): void;
}>();

const toggleNotifPanel = async () => {
  showNotifPanel.value = !showNotifPanel.value;
  if (showNotifPanel.value) {
    await store.fetchNotifications();
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
