<template>
  <div class="px-4 pb-24">
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
      <div
        v-for="timeline in sortedTimelines" :key="timeline.id"
        @click="$emit('view-timeline', timeline)"
        :class="['group bg-white rounded-2xl shadow-sm border hover:-translate-y-1 hover:shadow-lg transition-all cursor-pointer overflow-hidden', getTimelineStatus(timeline).borderClass]"
      >
        <div :class="['h-1.5', getTimelineStatus(timeline).barClass]"></div>
        <div class="p-5">
          <div class="flex justify-between items-start mb-4">
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-800 truncate mb-1">{{ timeline.name }}</h3>
              <span :class="['inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full', getTimelineStatus(timeline).badgeClass]">
                {{ getTimelineStatus(timeline).icon }} {{ getTimelineStatus(timeline).label }}
              </span>
            </div>
            <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
              <button v-if="timeline.role === 0" @click="$emit('edit-timeline', timeline)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors">✏️</button>
              <button v-if="timeline.role === 0" @click="$emit('delete-timeline', timeline.id)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">🗑️</button>
            </div>
          </div>
          <div class="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-xl">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ getTimelineStatus(timeline).icon }}</span>
              <div>
                <p class="text-xs text-gray-500">剩餘時間</p>
                <p :class="['text-lg font-bold', getDaysRemaining(timeline.endDate).colorClass]">{{ getDaysRemaining(timeline.endDate).display }}</p>
              </div>
            </div>
            <div class="text-right">
              <p class="text-xs text-gray-500">截止日期</p>
              <p class="text-sm font-medium text-gray-700">{{ formatDate(timeline.endDate) || '未設定' }}</p>
            </div>
          </div>
          <div class="mb-4" v-if="timeline.startDate && timeline.endDate">
            <div class="flex justify-between text-xs text-gray-400 mb-1">
              <span>{{ formatDate(timeline.startDate) }}</span>
              <span>{{ formatDate(timeline.endDate) }}</span>
            </div>
            <div class="relative h-2 bg-gray-100 rounded-full overflow-hidden">
              <div class="absolute left-0 top-0 h-full bg-linear-to-r from-blue-400 to-blue-500 rounded-full transition-all duration-500" :style="{ width: getTimeProgress(timeline) + '%' }"></div>
              <div v-if="getTimeProgress(timeline) > 0 && getTimeProgress(timeline) < 100" class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-full shadow-sm" :style="{ left: getTimeProgress(timeline) + '%', transform: 'translate(-50%, -50%)' }"></div>
            </div>
            <p class="text-xs text-gray-400 text-center mt-1">時程進度 {{ getTimeProgress(timeline) }}%</p>
          </div>
          <div class="mb-4">
            <div class="flex justify-between text-sm mb-1">
              <span class="text-gray-500">任務完成度</span>
              <span class="font-semibold" :class="getProgressTextColor(timeline)">{{ timeline.completedTasks || 0 }} / {{ timeline.totalTasks || 0 }}</span>
            </div>
            <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
              <div :class="['h-full rounded-full transition-all duration-500', getProgressBarColor(timeline)]" :style="{ width: getTaskProgress(timeline) + '%' }"></div>
            </div>
          </div>
          <div class="flex items-center justify-between pt-3 border-t border-gray-100">
            <div class="flex items-center gap-2 text-xs text-gray-400"><span>📅 {{ formatDate(timeline.startDate) || '未設定' }}</span></div>
            <span class="text-xs text-primary font-medium group-hover:underline">查看詳情 →</span>
          </div>
        </div>
      </div>
    </div>
    <div v-if="timelinesCount === 0" class="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
      <span class="text-6xl block mb-4">📁</span>
      <p class="text-xl text-gray-600 mb-2">目前尚無專案</p>
      <p class="text-sm text-gray-400 mb-6">建立您的第一個專案來開始追蹤進度</p>
      <button @click="$emit('create-timeline')" class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:shadow-xl transition-all">
        <span>➕</span> 新增專案
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '../../utils/formatters';
import type { Timeline } from '../../types';

type TimelineStatus = {
  label: string;
  icon: string;
  badgeClass: string;
  borderClass: string;
  barClass: string;
};

type DaysRemaining = {
  display: string;
  colorClass: string;
};

defineProps<{
  sortedTimelines: Timeline[];
  timelinesCount: number;
  getTimelineStatus: (timeline: Timeline) => TimelineStatus;
  getDaysRemaining: (endDate: string | null | undefined) => DaysRemaining;
  getTimeProgress: (timeline: Timeline) => number;
  getProgressTextColor: (timeline: Timeline) => string;
  getProgressBarColor: (timeline: Timeline) => string;
  getTaskProgress: (timeline: Timeline) => number;
}>();

defineEmits<{
  (e: 'view-timeline', timeline: Timeline): void;
  (e: 'edit-timeline', timeline: Timeline): void;
  (e: 'delete-timeline', timelineId: number): void;
  (e: 'create-timeline'): void;
}>();
</script>
