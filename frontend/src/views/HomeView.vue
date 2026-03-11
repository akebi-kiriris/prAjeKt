<template>
  <div class="h-full w-full bg-gray-50 px-6 pt-6 pb-24 md:pb-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-6xl mx-auto">
    <!-- Welcome Card -->
    <div class="mt-4 mb-8 bg-linear-to-r from-primary to-primary-light rounded-2xl shadow-lg animate-slideDown">
      <div class="p-6 md:p-12 text-center text-white">
        <div class="flex items-center justify-center gap-4 mb-4">
          <h1 class="text-2xl md:text-4xl font-bold">PrAjeKt 專案管理</h1>
        </div>
        <p class="text-base md:text-xl opacity-95">高效團隊協作，輕鬆管理專案進度！</p>
      </div>
    </div>

    <!-- Navigation Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
      <router-link 
        v-for="card in navCards" 
        :key="card.path"
        :to="card.path" 
        class="no-underline"
      >
        <div class="bg-white rounded-xl shadow-md hover:shadow-xl hover:-translate-y-1 transition-all cursor-pointer h-full animate-fadeIn">
          <div class="p-8 text-center">
            <span class="text-5xl mb-4 block">{{ card.icon }}</span>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">{{ card.title }}</h3>
            <p class="text-gray-500">{{ card.description }}</p>
          </div>
        </div>
      </router-link>
    </div>

    <!-- 即將到期區塊 -->
    <div class="mt-4">
      <div class="flex items-center gap-2 mb-4">
        <span class="text-2xl">⏰</span>
        <h2 class="text-lg font-bold text-gray-800">即將到期 / 進度落後</h2>
        <span v-if="upcomingItems.length > 0" class="px-2 py-0.5 bg-red-100 text-red-600 text-xs font-semibold rounded-full">{{ upcomingItems.length }}</span>
      </div>

      <div v-if="loadingUpcoming" class="text-center py-8 text-gray-400 text-sm">載入中...</div>

      <div v-else-if="upcomingItems.length === 0" class="bg-white rounded-2xl shadow-sm p-8 text-center text-gray-400">
        <span class="text-4xl block mb-2">🎉</span>
        <p class="text-sm">目前沒有即將到期的項目，繼續保持！</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <router-link
          v-for="item in upcomingItems"
          :key="item.type + item.id"
          :to="item.type === 'timeline' ? '/timelines' : '/tasks'"
          class="no-underline"
        >
          <div :class="['bg-white rounded-2xl shadow-sm p-4 border-l-4 hover:shadow-md transition-all cursor-pointer', item.is_overdue ? 'border-red-500' : 'border-amber-400']">
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0">
                <span class="shrink-0 text-lg">{{ item.type === 'timeline' ? '📊' : '✅' }}</span>
                <p class="text-sm font-semibold text-gray-800 truncate">{{ item.name }}</p>
              </div>
              <span :class="['shrink-0 text-xs px-2 py-0.5 rounded-full font-medium', item.is_overdue ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-700']">
                {{ item.is_overdue ? '已逾期' : '即將到期' }}
              </span>
            </div>
            <div class="mt-2 flex items-center gap-3 text-xs text-gray-400">
              <span>{{ item.type === 'timeline' ? '專案' : '任務' }}</span>
              <span>截止 {{ item.end_date }}</span>
            </div>
          </div>
        </router-link>
      </div>
    </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { taskService } from '../services/taskService';
import { timelineService } from '../services/timelineService';

const navCards = [
  { path: '/timelines', icon: '📊', title: '專案管理', description: '建立專案、分配任務' },
  { path: '/tasks',     icon: '✅', title: '任務管理', description: '管理您的任務與進度' },
  { path: '/todos',     icon: '📝', title: '待辦事項', description: '記錄日常待辦事項' },
  { path: '/groups',    icon: '💬', title: '群組訊息', description: '與團隊溝通協作' },
  { path: '/profile',   icon: '👤', title: '個人資料', description: '管理個人資料' },
];

const upcomingItems = ref([]);
const loadingUpcoming = ref(true);

onMounted(async () => {
  try {
    const [taskRes, timelineRes] = await Promise.allSettled([
      taskService.upcoming(),
      timelineService.upcoming(),
    ]);
    const tasks = taskRes.status === 'fulfilled' ? (taskRes.value.data || []) : [];
    const timelines = timelineRes.status === 'fulfilled' ? (timelineRes.value.data || []) : [];
    // 合併、逾期的排最前面，再依截止日升序
    upcomingItems.value = [...tasks.map(t => ({ ...t, id: t.task_id })), ...timelines]
      .sort((a, b) => {
        if (a.is_overdue !== b.is_overdue) return a.is_overdue ? -1 : 1;
        return a.end_date < b.end_date ? -1 : 1;
      });
  } catch {
    // 靜默失敗，不影響主頁其他功能
  } finally {
    loadingUpcoming.value = false;
  }
});
</script>
