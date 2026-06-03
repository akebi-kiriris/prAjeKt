<template>
  <div class="px-4 pb-8">
    <div class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="p-4 border-b border-slate-200 bg-linear-to-r from-sky-50 via-white to-cyan-50">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h3 class="font-semibold text-slate-800 flex items-center gap-2">
              <span class="w-8 h-8 bg-white rounded-lg shadow-sm flex items-center justify-center">📈</span>
              任務甘特圖（frappe-gantt）
            </h3>
            <p class="text-xs text-slate-500 mt-1">支援拖曳調整日期；依賴關係使用任務 depends_on_task_ids </p>
          </div>
          <div class="flex flex-wrap items-center gap-3 text-xs text-slate-600">
            <div>
              <label class="mr-2 text-slate-500">專案篩選</label>
              <select :value="selectedGanttTimeline" class="px-3 py-1.5 border border-slate-200 rounded-lg bg-white" @change="$emit('update:selected-gantt-timeline', ($event.target as HTMLSelectElement).value)">
                <option value="all">全部專案</option>
                <option v-for="timeline in timelines" :key="timeline.id" :value="String(timeline.id)">{{ timeline.name }}</option>
              </select>
            </div>
            <div>
              <label class="mr-2 text-slate-500">時間範圍</label>
              <select :value="selectedGanttRange" class="px-3 py-1.5 border border-slate-200 rounded-lg bg-white" @change="$emit('update:selected-gantt-range', ($event.target as HTMLSelectElement).value as 'all' | '90d' | '30d')">
                <option value="all">全部</option>
                <option value="90d">近 90 天</option>
                <option value="30d">近 30 天</option>
              </select>
            </div>
            <div>
              <label class="mr-2 text-slate-500">縮放</label>
              <select :value="selectedGanttViewMode" class="px-3 py-1.5 border border-slate-200 rounded-lg bg-white" @change="$emit('update:selected-gantt-view-mode', ($event.target as HTMLSelectElement).value as 'Day' | 'Week' | 'Month')">
                <option value="Day">日</option>
                <option value="Week">週</option>
                <option value="Month">月</option>
              </select>
            </div>
            <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-full">任務 {{ ganttRenderableTaskCount }}</span>
            <span class="px-2 py-1 bg-amber-100 text-amber-700 rounded-full">缺日期 {{ missingGanttTaskDates }}</span>
          </div>
        </div>
      </div>

      <div v-if="ganttRenderableTaskCount === 0" class="text-center py-16">
        <span class="text-5xl block mb-3">🗓️</span>
        <p class="text-lg text-slate-700">目前沒有可繪製的任務</p>
        <p class="text-sm text-slate-400 mt-1">任務需同時有開始與結束日期才能顯示在甘特圖上。</p>
      </div>

      <div v-else class="p-4">
        <div :ref="setGanttContainerRef" class="frappe-gantt-container w-full overflow-x-auto"></div>
        <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
          <span class="px-2 py-1 bg-slate-100 rounded-full">提示：拖曳條形可調整任務時程</span>
          <span class="px-2 py-1 bg-slate-100 rounded-full">點擊任務可開啟所屬專案面板</span>
          <span class="px-2 py-1 bg-slate-100 rounded-full">滑鼠移入可檢視任務資訊</span>
          <span class="px-2 py-1 bg-sky-50 text-sky-700 rounded-full">主責人會用固定顏色區分</span>
          <span class="px-2 py-1 bg-amber-50 text-amber-700 rounded-full">有協作者的任務會顯示虛線外框</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Timeline } from '../../types';

defineProps<{
  timelines: Timeline[];
  selectedGanttTimeline: string;
  selectedGanttRange: 'all' | '90d' | '30d';
  selectedGanttViewMode: 'Day' | 'Week' | 'Month';
  ganttRenderableTaskCount: number;
  missingGanttTaskDates: number;
  setGanttContainerRef: (el: Element | null) => void;
}>();

defineEmits<{
  (e: 'update:selected-gantt-timeline', value: string): void;
  (e: 'update:selected-gantt-range', value: 'all' | '90d' | '30d'): void;
  (e: 'update:selected-gantt-view-mode', value: 'Day' | 'Week' | 'Month'): void;
}>();
</script>
