<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <div class="mx-auto grid w-full max-w-6xl grid-cols-1 gap-6">
      <header
        class="overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-br from-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]"
      >
        <div class="relative px-5 py-5 md:px-6 md:py-6">
          <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />
          <div class="relative">
            <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
              WORKSPACE OVERVIEW
            </p>
            <h1 class="text-[clamp(1.45rem,2.2vw,2rem)] font-black tracking-[0.01em] text-slate-900">PrAjeKt 專案管理</h1>
            <p class="mt-2 text-sm leading-6 text-slate-600">高效團隊協作，輕鬆管理專案進度。</p>
          </div>
        </div>
      </header>

    <!-- Navigation Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
      <router-link 
        v-for="card in navCards" 
        :key="card.path"
        :to="card.path" 
        class="no-underline"
      >
        <div class="h-full cursor-pointer rounded-2xl border border-slate-200 bg-white shadow-[0_10px_22px_rgba(15,23,42,0.05)] transition hover:-translate-y-px hover:shadow-[0_16px_30px_rgba(15,23,42,0.08)]">
          <div class="p-8 text-center">
            <span class="text-5xl mb-4 block">{{ card.icon }}</span>
            <h3 class="mb-2 text-xl font-semibold text-slate-800">{{ card.title }}</h3>
            <p class="text-slate-500">{{ card.description }}</p>
          </div>
        </div>
      </router-link>
    </div>

    <!-- 即將到期區塊 -->
    <div class="mt-4">
      <div class="mb-4 flex items-center gap-2">
        <span class="text-2xl">⏰</span>
        <h2 class="text-lg font-bold text-slate-800">即將到期 / 進度落後</h2>
        <span v-if="upcomingItems.length > 0" class="px-2 py-0.5 bg-red-100 text-red-600 text-xs font-semibold rounded-full">{{ upcomingItems.length }}</span>
      </div>

      <div v-if="loadingUpcoming" class="py-8 text-center text-sm text-slate-400">載入中...</div>

      <div v-else-if="upcomingItems.length === 0" class="rounded-2xl border border-slate-200 bg-white p-8 text-center text-slate-400 shadow-sm">
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
          <div :class="['cursor-pointer rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:shadow-md', item.is_overdue ? 'border-red-200' : 'border-amber-200']">
            <div class="flex items-start justify-between gap-2">
              <div class="flex items-center gap-2 min-w-0">
                <span class="shrink-0 text-lg">{{ item.type === 'timeline' ? '📊' : '✅' }}</span>
                <p class="truncate text-sm font-semibold text-slate-800">{{ item.name }}</p>
              </div>
              <span :class="['shrink-0 text-xs px-2 py-0.5 rounded-full font-medium', item.is_overdue ? 'bg-red-100 text-red-600' : 'bg-amber-100 text-amber-700']">
                {{ item.is_overdue ? '已逾期' : '即將到期' }}
              </span>
            </div>
            <div class="mt-2 flex items-center gap-3 text-xs text-slate-400">
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

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { taskService } from '../services/taskService';
import { timelineService } from '../services/timelineService';
import type { NavCard, UpcomingItem, UpcomingTaskRaw } from '../types';

const navCards: NavCard[] = [
  { path: '/timelines', icon: '📊', title: '專案管理', description: '建立專案、分配任務' },
  { path: '/tasks',     icon: '✅', title: '任務管理', description: '管理您的任務與進度' },
  { path: '/todos',     icon: '📝', title: '待辦事項', description: '記錄日常待辦事項' },
  { path: '/groups',    icon: '💬', title: '群組訊息', description: '與團隊溝通協作' },
  { path: '/profile',   icon: '👤', title: '個人資料', description: '管理個人資料' },
];

const upcomingItems = ref<UpcomingItem[]>([]);
const loadingUpcoming = ref<boolean>(true);

onMounted(async () => {
  try {
    const [taskRes, timelineRes] = await Promise.allSettled([
      taskService.upcoming(),
      timelineService.upcoming(),
    ]);
    const tasks: UpcomingTaskRaw[] = taskRes.status === 'fulfilled'
      ? taskRes.value.data || []
      : [];
    const timelines: UpcomingItem[] = timelineRes.status === 'fulfilled'
      ? timelineRes.value.data || []
      : [];

    // 合併、逾期的排最前面，再依截止日升序
    upcomingItems.value = [...tasks.map((t) => ({ ...t, id: t.task_id })), ...timelines]
      .sort((a, b) => {
        if (a.is_overdue !== b.is_overdue) return a.is_overdue ? -1 : 1;
        const endA = new Date(a.end_date).getTime();
        const endB = new Date(b.end_date).getTime();
        if (Number.isNaN(endA) && Number.isNaN(endB)) return 0;
        if (Number.isNaN(endA)) return 1;
        if (Number.isNaN(endB)) return -1;
        if (endA === endB) return 0;
        return endA < endB ? -1 : 1;
      });
  } catch {
    // 靜默失敗，不影響主頁其他功能
  } finally {
    loadingUpcoming.value = false;
  }
});
</script>
