<template>
  <div class="px-4 pb-8">
    <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
      <div class="p-4 border-b border-gray-100 bg-gray-50/50">
        <div class="flex items-center justify-between">
          <h3 class="font-semibold text-gray-700">📋 專案列表</h3>
          <span class="text-sm text-gray-500">依結束日期排序</span>
        </div>
      </div>
      <div class="divide-y divide-gray-100">
        <div
          v-for="timeline in sortedTimelines"
          :key="timeline.id"
          @click="$emit('view-timeline', timeline)"
          class="p-4 hover:bg-blue-50/50 cursor-pointer transition-colors"
        >
          <div class="flex items-start gap-4">
            <div class="shrink-0 w-20 text-center">
              <div :class="['w-12 h-12 mx-auto rounded-xl flex flex-col items-center justify-center', getTimelineStatus(timeline).bgClass]">
                <span class="text-xs font-medium" :class="getTimelineStatus(timeline).textClass">
                  {{ timeline.endDate ? new Date(timeline.endDate).getMonth() + 1 + '月' : '--' }}
                </span>
                <span class="text-lg font-bold -mt-1" :class="getTimelineStatus(timeline).textClass">
                  {{ timeline.endDate ? new Date(timeline.endDate).getDate() : '--' }}
                </span>
              </div>
              <p class="text-xs text-gray-400 mt-1">{{ getDaysRemaining(timeline.endDate).text }}</p>
            </div>
            <div class="flex-1 min-w-0">
              <div class="flex items-start justify-between gap-2 mb-2">
                <h4 class="font-semibold text-gray-800 truncate">{{ timeline.name }}</h4>
                <span :class="['shrink-0 px-2 py-0.5 text-xs font-medium rounded-full', getTimelineStatus(timeline).badgeClass]">
                  {{ getTimelineStatus(timeline).label }}
                </span>
              </div>
              <div class="mb-2">
                <div class="flex items-center gap-2">
                  <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div :class="['h-full rounded-full transition-all duration-500', getProgressBarColor(timeline)]" :style="{ width: getTaskProgress(timeline) + '%' }"></div>
                  </div>
                  <span class="text-xs font-medium text-gray-500 w-10 text-right">{{ getTaskProgress(timeline) }}%</span>
                </div>
              </div>
              <div class="flex items-center gap-4 text-xs text-gray-500">
                <span class="flex items-center gap-1"><span>📅</span> {{ formatDate(timeline.startDate) }} - {{ formatDate(timeline.endDate) }}</span>
                <span class="flex items-center gap-1"><span>✅</span> {{ timeline.completedTasks || 0 }}/{{ timeline.totalTasks || 0 }}</span>
              </div>
            </div>
            <div class="shrink-0 flex items-center gap-1" @click.stop>
              <button v-if="timeline.role === 0" @click="$emit('edit-timeline', timeline)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors">✏️</button>
              <button v-if="timeline.role === 0" @click="$emit('delete-timeline', timeline.id)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">🗑️</button>
            </div>
          </div>
        </div>
        <div v-if="timelinesCount === 0" class="text-center py-16">
          <span class="text-5xl block mb-4">📅</span>
          <p class="text-lg text-gray-600">目前尚無專案</p>
          <p class="text-sm text-gray-400 mt-1">點擊「新增專案」來建立您的第一個專案</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '../../utils/formatters';
import type { Timeline } from '../../types';

type TimelineStatus = {
  label: string;
  bgClass: string;
  textClass: string;
  badgeClass: string;
};

type DaysRemaining = {
  text: string;
};

defineProps<{
  sortedTimelines: Timeline[];
  timelinesCount: number;
  getTimelineStatus: (timeline: Timeline) => TimelineStatus;
  getDaysRemaining: (endDate: string | null | undefined) => DaysRemaining;
  getProgressBarColor: (timeline: Timeline) => string;
  getTaskProgress: (timeline: Timeline) => number;
}>();

defineEmits<{
  (e: 'view-timeline', timeline: Timeline): void;
  (e: 'edit-timeline', timeline: Timeline): void;
  (e: 'delete-timeline', timelineId: number): void;
}>();
</script>
