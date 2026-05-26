<template>
  <div v-if="show && task" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
    <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slideUp">
      <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent sticky top-0 bg-white z-10">
        <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
          <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📌</span>
          {{ task.name }}
        </h2>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
      </div>
      <div class="p-6 space-y-6">
        <div class="flex flex-wrap items-center gap-4">
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">狀態：</span>
            <span :class="['px-3 py-1 text-sm font-medium rounded-full', task.status === 'completed' ? 'bg-green-100 text-green-700' : task.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700']">
              {{ task.status === 'completed' ? '✅ 已完成' : task.status === 'in_progress' ? '🔄 進行中' : '📋 待辦' }}
            </span>
          </div>
          <div class="flex items-center gap-2">
            <span class="text-sm text-gray-500">優先級：</span>
            <select :value="task.priority" @change="$emit('priority-select', $event)" class="px-3 py-1 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
              <option :value="1">🔴 高優先</option>
              <option :value="2">🟡 中優先</option>
              <option :value="3">🟢 低優先</option>
            </select>
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
          <div>
            <p class="text-xs text-gray-500 mb-1">開始日期</p>
            <p class="font-medium text-gray-800">{{ formatDate(task.start_date) || '未設定' }}</p>
          </div>
          <div>
            <p class="text-xs text-gray-500 mb-1">截止日期</p>
            <p class="font-medium text-gray-800">{{ formatDate(task.end_date) || '未設定' }}</p>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-600 mb-2"><span>🏷️</span> 標籤（逗號分隔）</label>
          <div class="flex gap-2">
            <input :value="task.tags" type="text" placeholder="例如：前端, 重要, Bug" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" @input="$emit('update:tags', ($event.target as HTMLInputElement).value)" />
            <button @click="$emit('update-tags')" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">儲存</button>
          </div>
          <div v-if="task.tags" class="flex flex-wrap gap-2 mt-2">
            <span v-for="tag in task.tags.split(',')" :key="tag" class="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">{{ tag.trim() }}</span>
          </div>
        </div>
        <div>
          <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <span>📋</span> 子任務
            <span class="text-sm font-normal text-gray-500">({{ getCompletedSubtaskCount(task) }}/{{ task.subtasks?.length || 0 }})</span>
          </h4>
          <div v-if="task.subtasks && task.subtasks.length > 0" class="mb-4">
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div class="h-full bg-primary rounded-full transition-all duration-300" :style="{ width: getSubtaskProgress(task) + '%' }"></div>
            </div>
          </div>
          <div class="space-y-2 mb-4">
            <div v-for="subtask in task.subtasks" :key="subtask.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group hover:bg-gray-100 transition-colors">
              <input type="checkbox" :checked="subtask.completed" @change="$emit('toggle-subtask', subtask)" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" />
              <span :class="['flex-1 text-sm', subtask.completed ? 'line-through text-gray-400' : 'text-gray-700']">{{ subtask.name }}</span>
              <button @click="$emit('delete-subtask', subtask)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all">🗑️</button>
            </div>
            <div v-if="!task.subtasks || task.subtasks.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無子任務</div>
          </div>
          <div class="flex gap-2">
            <input :value="newSubtaskName" type="text" placeholder="輸入子任務名稱..." @input="$emit('update:new-subtask-name', ($event.target as HTMLInputElement).value)" @keyup.enter="$emit('add-subtask')" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
            <button @click="$emit('add-subtask')" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">新增</button>
          </div>
        </div>
        <div v-if="task.task_remark" class="p-4 bg-yellow-50 rounded-xl">
          <h4 class="font-semibold text-gray-700 mb-2 flex items-center gap-2"><span>📝</span> 備註</h4>
          <p class="text-gray-600 text-sm">{{ task.task_remark }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '../../utils/formatters';
import type { Subtask, Task } from '../../types';

defineProps<{
  show: boolean;
  task: Task | null;
  newSubtaskName: string;
  getSubtaskProgress: (task: Task) => number;
  getCompletedSubtaskCount: (task: Task) => number;
}>();

defineEmits<{
  (e: 'close'): void;
  (e: 'priority-select', event: Event): void;
  (e: 'update:tags', value: string): void;
  (e: 'update-tags'): void;
  (e: 'toggle-subtask', subtask: Subtask): void;
  (e: 'delete-subtask', subtask: Subtask): void;
  (e: 'update:new-subtask-name', value: string): void;
  (e: 'add-subtask'): void;
}>();
</script>
