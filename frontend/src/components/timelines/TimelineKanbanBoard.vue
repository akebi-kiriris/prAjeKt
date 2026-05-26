<template>
  <div class="px-4 pb-8">
    <div class="mb-6 flex flex-wrap items-center gap-4">
      <div class="flex-1 min-w-50">
        <label class="block text-sm font-medium text-gray-600 mb-2">選擇專案</label>
        <select :value="selectedKanbanTimeline" class="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm" @change="$emit('update:selected-kanban-timeline', parseNullableNumber($event))">
          <option :value="null">📁 全部專案</option>
          <option v-for="t in timelines" :key="t.id" :value="t.id">📋 {{ t.name }}</option>
        </select>
      </div>
      <div class="flex-1 min-w-50">
        <label class="block text-sm font-medium text-gray-600 mb-2">搜尋任務</label>
        <div class="relative">
          <input :value="searchQuery" type="text" placeholder="輸入任務名稱..." class="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm" @input="$emit('update:search-query', ($event.target as HTMLInputElement).value)" />
          <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
        </div>
      </div>
      <div class="flex items-end gap-2">
        <button @click="$emit('toggle-filter-panel')" :class="['px-4 py-2.5 rounded-xl border transition-all flex items-center gap-2 shadow-sm', hasActiveFilters ? 'bg-linear-to-r from-primary to-blue-600 text-white border-transparent' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300']">
          <span>🎯</span> 篩選
          <span v-if="hasActiveFilters" class="w-5 h-5 bg-white text-primary text-xs font-bold rounded-full flex items-center justify-center shadow">{{ activeFilterCount }}</span>
        </button>
      </div>
    </div>

    <div v-if="showFilterPanel" class="mb-6 p-5 bg-linear-to-r from-white to-gray-50/50 rounded-2xl border border-gray-200 shadow-lg">
      <h4 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
        <span class="w-6 h-6 bg-primary/10 rounded-lg flex items-center justify-center text-xs">🎯</span>
        進階篩選
      </h4>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-2">優先級</label>
          <select :value="filterPriority" class="w-full px-3 py-2.5 border border-gray-200 rounded-xl bg-white shadow-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" @change="$emit('update:filter-priority', parseNullableNumber($event))">
            <option :value="null">全部優先級</option>
            <option :value="1">🔴 高優先</option>
            <option :value="2">🟡 中優先</option>
            <option :value="3">🟢 低優先</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-2">標籤</label>
          <input :value="filterTag" type="text" placeholder="輸入標籤關鍵字..." class="w-full px-3 py-2.5 border border-gray-200 rounded-xl bg-white shadow-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" @input="$emit('update:filter-tag', ($event.target as HTMLInputElement).value)" />
        </div>
        <div class="flex items-end">
          <button @click="$emit('clear-filters')" class="px-4 py-2.5 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all flex items-center gap-2">
            <span>🗑️</span> 清除篩選
          </button>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="bg-linear-to-b from-slate-100 to-slate-50 rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-gray-700 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-slate-400 animate-pulse"></span>
            待辦
            <span class="text-sm font-normal bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{{ pendingTasks.length }}</span>
          </h3>
        </div>
        <draggable :list="pendingTasks" group="kanban" item-key="task_id" :animation="200" ghost-class="kanban-ghost" drag-class="kanban-drag" @start="$emit('drag-start')" @end="$emit('drag-end')" @change="$emit('pending-change', $event)" class="space-y-3 min-h-50">
          <template #item="{ element: task }">
            <TaskCard :task="task" column="pending" :get-priority-badge-class="getPriorityBadgeClass" :get-priority-label="getPriorityLabel" :get-subtask-progress="getSubtaskProgress" :get-completed-subtask-count="getCompletedSubtaskCount" :get-task-timeline-name="getTaskTimelineName" @open="$emit('open-task', task)" />
          </template>
        </draggable>
        <div v-if="pendingTasks.length === 0 && !isDragging" class="text-center py-12 text-gray-400">
          <span class="text-3xl mb-2 block">📋</span>
          <span class="text-sm">拖曳任務到這裡</span>
        </div>
      </div>

      <div class="bg-linear-to-b from-blue-100 to-blue-50 rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-blue-700 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span>
            進行中
            <span class="text-sm font-normal bg-blue-200 text-blue-700 px-2 py-0.5 rounded-full">{{ inProgressTasks.length }}</span>
          </h3>
        </div>
        <draggable :list="inProgressTasks" group="kanban" item-key="task_id" :animation="200" ghost-class="kanban-ghost" drag-class="kanban-drag" @start="$emit('drag-start')" @end="$emit('drag-end')" @change="$emit('in-progress-change', $event)" class="space-y-3 min-h-50">
          <template #item="{ element: task }">
            <TaskCard :task="task" column="in_progress" :get-priority-badge-class="getPriorityBadgeClass" :get-priority-label="getPriorityLabel" :get-subtask-progress="getSubtaskProgress" :get-completed-subtask-count="getCompletedSubtaskCount" :get-task-timeline-name="getTaskTimelineName" @open="$emit('open-task', task)" />
          </template>
        </draggable>
        <div v-if="inProgressTasks.length === 0 && !isDragging" class="text-center py-12 text-gray-400">
          <span class="text-3xl mb-2 block">🚀</span>
          <span class="text-sm">拖曳任務到這裡</span>
        </div>
      </div>

      <div class="bg-linear-to-b from-green-100 to-green-50 rounded-2xl p-4 shadow-sm">
        <div class="flex items-center justify-between mb-4">
          <h3 class="font-bold text-green-700 flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-green-500"></span>
            已完成
            <span class="text-sm font-normal bg-green-200 text-green-700 px-2 py-0.5 rounded-full">{{ completedTasks.length }}</span>
          </h3>
        </div>
        <draggable :list="completedTasks" group="kanban" item-key="task_id" :animation="200" ghost-class="kanban-ghost" drag-class="kanban-drag" @start="$emit('drag-start')" @end="$emit('drag-end')" @change="$emit('completed-change', $event)" class="space-y-3 min-h-50">
          <template #item="{ element: task }">
            <TaskCard :task="task" column="completed" :get-priority-badge-class="getPriorityBadgeClass" :get-priority-label="getPriorityLabel" :get-subtask-progress="getSubtaskProgress" :get-completed-subtask-count="getCompletedSubtaskCount" :get-task-timeline-name="getTaskTimelineName" @open="$emit('open-task', task)" />
          </template>
        </draggable>
        <div v-if="completedTasks.length === 0 && !isDragging" class="text-center py-12 text-gray-400">
          <span class="text-3xl mb-2 block">🎉</span>
          <span class="text-sm">完成的任務會出現在這裡</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import draggable from 'vuedraggable';
import { formatDate } from '../../utils/formatters';
import type { Subtask, Task, Timeline } from '../../types';

const TaskCard = {
  props: ['task', 'column', 'getPriorityBadgeClass', 'getPriorityLabel', 'getSubtaskProgress', 'getCompletedSubtaskCount', 'getTaskTimelineName'],
  emits: ['open'],
  template: `
    <div @click="$emit('open', task)" :class="[
      'kanban-card rounded-xl p-4 shadow-sm cursor-grab hover:shadow-lg hover:-translate-y-1 active:cursor-grabbing transition-all duration-200',
      column==='pending' ? 'bg-white border-l-4 border-slate-300' : '',
      column==='in_progress' ? 'bg-white border-l-4 border-blue-400' : '',
      column==='completed' ? 'bg-white/80 border-l-4 border-green-400' : ''
    ]">
      <div class="flex items-start justify-between mb-2">
        <span :class="['font-medium text-sm line-clamp-2', column==='completed' ? 'text-gray-500 line-through' : 'text-gray-800']">{{ task.name }}</span>
        <span v-if="column!=='completed'" :class="getPriorityBadgeClass(task.priority)" class="text-xs px-2 py-0.5 rounded-full shrink-0 ml-2 font-medium">{{ getPriorityLabel(task.priority) }}</span>
        <span v-else class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 shrink-0 ml-2 font-medium">✓ 完成</span>
      </div>
      <div v-if="column!=='completed' && task.tags" class="flex flex-wrap gap-1 mb-2">
        <span v-for="tag in task.tags.split(',').slice(0, 3)" :key="tag" class="text-xs px-2 py-0.5 bg-linear-to-r from-blue-100 to-indigo-100 text-blue-700 rounded-full">{{ tag.trim() }}</span>
        <span v-if="task.tags.split(',').length > 3" class="text-xs text-gray-400">+{{ task.tags.split(',').length - 3 }}</span>
      </div>
      <div v-if="column!=='completed' && task.subtasks && task.subtasks.length > 0" class="mb-2">
        <div class="flex items-center gap-2 text-xs text-gray-500">
          <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
            <div class="h-full bg-linear-to-r from-primary to-blue-400 rounded-full transition-all duration-300" :style="{ width: getSubtaskProgress(task) + '%' }"></div>
          </div>
          <span class="font-medium">{{ getCompletedSubtaskCount(task) }}/{{ task.subtasks.length }}</span>
        </div>
      </div>
      <div class="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
        <span :class="[
          'flex items-center gap-1 px-2 py-1 rounded-md',
          column==='in_progress' ? 'bg-blue-100 text-blue-600' : '',
          column==='completed' ? 'bg-green-100 text-green-600' : '',
          column==='pending' ? 'bg-gray-100' : ''
        ]">📅 {{ formatDate(task.end_date) }}</span>
        <span v-if="getTaskTimelineName(task)" :class="['truncate max-w-20 font-medium', column==='completed' ? 'text-green-600' : 'text-primary']">📁 {{ getTaskTimelineName(task) }}</span>
      </div>
    </div>
  `,
};

defineProps<{
  timelines: Timeline[];
  selectedKanbanTimeline: number | null;
  searchQuery: string;
  showFilterPanel: boolean;
  hasActiveFilters: boolean;
  activeFilterCount: number;
  filterPriority: number | null;
  filterTag: string;
  pendingTasks: Task[];
  inProgressTasks: Task[];
  completedTasks: Task[];
  isDragging: boolean;
  getPriorityBadgeClass: (priority: number) => string;
  getPriorityLabel: (priority: number) => string;
  getSubtaskProgress: (task: Task) => number;
  getCompletedSubtaskCount: (task: Task) => number;
  getTaskTimelineName: (task: Task) => string;
}>();

defineEmits<{
  (e: 'update:selected-kanban-timeline', value: number | null): void;
  (e: 'update:search-query', value: string): void;
  (e: 'toggle-filter-panel'): void;
  (e: 'update:filter-priority', value: number | null): void;
  (e: 'update:filter-tag', value: string): void;
  (e: 'clear-filters'): void;
  (e: 'drag-start'): void;
  (e: 'drag-end'): void;
  (e: 'pending-change', evt: unknown): void;
  (e: 'in-progress-change', evt: unknown): void;
  (e: 'completed-change', evt: unknown): void;
  (e: 'open-task', task: Task): void;
}>();

const parseNullableNumber = (event: Event): number | null => {
  const value = (event.target as HTMLSelectElement).value;
  if (value === '' || value === 'null') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
};
</script>
