<template>
  <div class="mb-4 p-4 bg-slate-50 border border-slate-200 rounded-xl">
    <div class="flex items-center justify-between gap-3 mb-3">
      <div>
        <p class="text-sm font-semibold text-slate-700">📊 週報預覽</p>
        <p class="text-xs text-slate-500">完成任務、風險與下一步建議</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="$emit('toggle-expanded')"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
        >
          {{ expanded ? '收合' : '展開' }}
        </button>
        <button
          @click="$emit('refresh')"
          :disabled="loading"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          {{ loading ? '載入中...' : '重新整理' }}
        </button>
      </div>
    </div>

    <div v-show="expanded">
      <div class="grid grid-cols-2 gap-3 mb-3">
        <div>
          <label class="block text-[11px] text-slate-500 mb-1">起始日</label>
          <input
            v-model="startDateModel"
            type="date"
            class="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
          />
        </div>
        <div>
          <label class="block text-[11px] text-slate-500 mb-1">結束日</label>
          <input
            v-model="endDateModel"
            type="date"
            class="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
          />
        </div>
      </div>

      <div v-if="error" class="mb-3 p-2.5 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg">
        {{ error }}
      </div>

      <div v-if="loading" class="text-xs text-slate-500 py-2">正在產生週報...</div>

      <div v-else-if="weeklyReport" class="space-y-3">
        <div v-if="weeklyReport.ai_summary" class="p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p class="text-xs font-medium text-blue-700 mb-1">📌 AI 週報摘要</p>
          <p class="text-xs text-blue-600">{{ weeklyReport.ai_summary }}</p>
          <p class="mt-1 text-[11px] text-blue-500">來源：{{ getAiSourceLabel(weeklyReport.ai_summary_source) }}</p>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
          <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
            <p class="text-[11px] text-slate-500">本期完成</p>
            <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.completed_tasks }}</p>
          </div>
          <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
            <p class="text-[11px] text-slate-500">總任務數</p>
            <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.total_tasks }}</p>
          </div>
          <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
            <p class="text-[11px] text-slate-500">完成率</p>
            <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.completion_rate }}%</p>
          </div>
          <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
            <p class="text-[11px] text-slate-500">風險項目</p>
            <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.at_risk_tasks }}</p>
          </div>
        </div>

        <div class="grid md:grid-cols-2 gap-3">
          <div class="p-3 bg-white border border-slate-200 rounded-lg">
            <p class="text-xs font-medium text-slate-600 mb-2">本期完成任務</p>
            <div v-if="weeklyReport.completed_tasks.length === 0" class="text-xs text-slate-400">本期尚無完成任務</div>
            <ul v-else class="space-y-1.5">
              <li
                v-for="item in weeklyReport.completed_tasks.slice(0, 5)"
                :key="`weekly-done-${item.task_id}`"
                class="text-xs text-slate-600"
              >
                ✓ {{ item.name }}
                <span class="text-slate-400">（{{ formatDate(item.completed_at || item.due_date) || '未標記' }}）</span>
              </li>
            </ul>
          </div>

          <div class="p-3 bg-white border border-slate-200 rounded-lg flex flex-col">
            <p class="text-xs font-medium text-slate-600 mb-2">風險清單</p>
            <div v-if="weeklyReport.risk_items.length === 0" class="text-xs text-slate-400">本期無風險項目</div>
            <ul v-else class="space-y-1.5 overflow-y-auto max-h-48 pr-2">
              <li
                v-for="item in weeklyReport.risk_items"
                :key="`weekly-risk-${item.task_id}`"
                class="text-xs text-amber-700"
              >
                ⚠ {{ item.name }}
                <span class="text-amber-600">（{{ item.reason }}，截止 {{ formatDate(item.due_date) || item.due_date }}）</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { WeeklyReportAiSummarySource, WeeklyReportResponse } from '../../types';

const props = defineProps<{
  expanded: boolean;
  loading: boolean;
  error: string;
  weeklyReport: WeeklyReportResponse | null;
  weeklyReportRange: { start_date: string; end_date: string };
  formatDate: (value?: string | null) => string;
  getAiSourceLabel: (value?: WeeklyReportAiSummarySource | string) => string;
}>();

const emit = defineEmits<{
  (e: 'toggle-expanded'): void;
  (e: 'refresh'): void;
  (e: 'update:weeklyReportRange', value: { start_date: string; end_date: string }): void;
}>();

const startDateModel = computed({
  get: () => props.weeklyReportRange.start_date,
  set: (value: string) => emit('update:weeklyReportRange', { ...props.weeklyReportRange, start_date: value }),
});

const endDateModel = computed({
  get: () => props.weeklyReportRange.end_date,
  set: (value: string) => emit('update:weeklyReportRange', { ...props.weeklyReportRange, end_date: value }),
});
</script>
