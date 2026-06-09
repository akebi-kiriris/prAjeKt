<template>
  <div v-if="open" class="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4" @click.self="$emit('close')">
    <div class="w-full max-w-lg rounded-2xl border border-slate-200 bg-white shadow-[0_20px_40px_rgba(15,23,42,0.14)]">
      <div class="p-5 border-b border-slate-200 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-slate-800">新增任務</h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">&times;</button>
      </div>
      <form @submit.prevent="$emit('submit')" class="p-5 space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">任務名稱 <span class="text-red-500">*</span></label>
          <input v-model="taskName" type="text" required placeholder="輸入任務名稱" class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">開始日期</label>
            <input v-model="taskStartDate" type="date" class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1.5">截止日期</label>
            <input v-model="taskEndDate" type="date" class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">優先級</label>
          <select v-model="taskPriority" class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white">
            <option :value="1">🔴 高優先</option>
            <option :value="2">🟡 中優先</option>
            <option :value="3">🟢 低優先</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">指派成員（可多選）</label>
          <select
            v-model="assigneeIdsModel"
            multiple
            class="w-full min-h-30 px-3 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white text-sm"
          >
            <option
              v-for="member in timelineMembers"
              :key="`add-assignee-${member.user_id}`"
              :value="member.user_id"
            >
              {{ member.username || member.name }}
            </option>
          </select>
          <p class="text-[11px] text-slate-500 mt-1.5">
            未選擇時預設分派給自己。若分派給他人，衝突明細會只顯示件數。
          </p>
          <div v-if="assigneeIdsModel.length > 0" class="mt-2 flex flex-wrap gap-1.5">
            <span
              v-for="memberId in assigneeIdsModel"
              :key="`add-assignee-chip-${memberId}`"
              class="px-2.5 py-1 text-xs rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100"
            >
              {{ getTimelineMemberName(memberId) }}
            </span>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">前置依賴任務（可多選）</label>
          <select
            v-model="dependencyIdsModel"
            multiple
            class="w-full min-h-30 px-3 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white text-sm"
          >
            <option
              v-for="taskOption in availableDependencyTasks"
              :key="`add-dependency-${taskOption.task_id}`"
              :value="taskOption.task_id"
            >
              {{ taskOption.name }}
            </option>
          </select>
          <p class="text-[11px] text-slate-500 mt-1.5">僅可依賴本專案任務；會自動去重與驗證。</p>
          <div v-if="dependencyIdsModel.length > 0" class="mt-2 flex flex-wrap gap-1.5">
            <span
              v-for="dependencyId in dependencyIdsModel"
              :key="`add-dependency-chip-${dependencyId}`"
              class="px-2.5 py-1 text-xs rounded-full bg-slate-100 text-slate-700 border border-slate-200"
            >
              {{ getTaskNameById(dependencyId) }}
            </span>
          </div>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">標籤（逗號分隔）</label>
          <input v-model="taskTags" type="text" placeholder="例如：前端, 重要, Bug" class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1.5">備註</label>
          <textarea v-model="taskRemark" rows="3" placeholder="任務備註（可選）" class="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"></textarea>
        </div>
        <div v-if="addTaskConflictSummary.hasConflict" class="p-3 bg-amber-50 border border-amber-200 rounded-xl">
          <p class="text-sm font-semibold text-amber-700 mb-1">⚠️ 偵測到 {{ addTaskConflictSummary.totalSignals }} 個排程衝突訊號</p>
          <p class="text-[11px] text-amber-700/90 mb-2">依被分派者逐一檢測，分派給他人時僅顯示件數。</p>
          <div class="space-y-2.5">
            <div
              v-for="item in addTaskConflictPreviews.filter((entry) => entry.preview.has_conflict)"
              :key="`add-conflict-assignee-${item.assignee_user_id ?? 'self'}`"
              class="p-2.5 bg-white/70 border border-amber-200 rounded-lg"
            >
              <p class="text-xs font-semibold text-amber-700 mb-1.5">
                👤 {{ item.assignee_label }}：{{ item.preview.conflict_count }} 個訊號
              </p>
              <div class="text-[11px] text-amber-700/90 space-y-1 mb-2">
                <p v-if="(item.preview.cross_project_conflict_count ?? 0) > 0">跨專案衝突：{{ item.preview.cross_project_conflict_count }} 個</p>
                <p v-if="(item.preview.workload_overload_count ?? 0) > 0">過載日：{{ item.preview.workload_overload_count }} 天</p>
              </div>
              <ul class="list-disc list-inside text-xs text-amber-700 space-y-1">
                <li v-for="conflict in item.preview.conflicts.slice(0, 3)" :key="`add-conflict-${item.assignee_user_id ?? 'self'}-${conflict.task_id}`">
                  {{ conflict.name }}（{{ conflict.reason }}，{{ conflict.start_date }} ~ {{ conflict.end_date }}）
                </li>
              </ul>
              <div
                v-if="(item.preview.workload_overload_days ?? []).length > 0"
                class="mt-2.5 p-2.5 bg-white/80 border border-amber-200 rounded-lg"
              >
                <p class="text-xs font-semibold text-amber-700 mb-1.5">📅 過載日列表</p>
                <ul class="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                  <li
                    v-for="day in item.preview.workload_overload_days"
                    :key="`overload-${item.assignee_user_id ?? 'self'}-${day.date}`"
                    class="text-xs text-amber-700"
                  >
                    <span class="font-medium">{{ formatDate(day.date) || day.date }}</span>
                    <span class="text-amber-600">：{{ day.projected_task_count }} 件（門檻 {{ day.threshold }}）</span>
                    <p v-if="day.sample_tasks.length" class="text-[11px] text-amber-600 mt-0.5 line-clamp-1">既有任務：{{ day.sample_tasks.join('、') }}</p>
                    <p v-else class="text-[11px] text-amber-600 mt-0.5">既有任務：{{ day.existing_task_count }} 件（僅顯示件數）</p>
                  </li>
                </ul>
              </div>
              <p v-if="item.preview.suggestion" class="text-xs text-amber-600 mt-2">建議改期為 {{ item.preview.suggestion.start_date }} ~ {{ item.preview.suggestion.end_date }}</p>
              <button
                type="button"
                @click="$emit('request-ai-suggestion', item.assignee_user_id)"
                :disabled="conflictAiSuggestionLoadingKey === getConflictPreviewKey(item.assignee_user_id)"
                class="mt-2 inline-flex items-center px-2.5 py-1 text-[11px] rounded-md border border-amber-300 text-amber-700 bg-white hover:bg-amber-50 transition-colors disabled:opacity-50"
              >
                {{ conflictAiSuggestionLoadingKey === getConflictPreviewKey(item.assignee_user_id) ? 'AI 產生中...' : '✨ 產生 AI 衝突建議' }}
              </button>
              <p v-if="item.preview.ai_suggestion" class="text-xs text-amber-700 italic mt-2">💡 {{ item.preview.ai_suggestion }}</p>
            </div>
          </div>
        </div>
        <div class="flex gap-3 pt-2">
          <button type="button" @click="$emit('close')" class="flex-1 py-2.5 border border-slate-200 text-slate-600 font-medium rounded-xl hover:bg-slate-50 transition-colors">取消</button>
          <button type="submit" class="flex-1 py-2.5 bg-primary text-white font-semibold rounded-xl hover:brightness-110 transition-all shadow-md shadow-primary/25">新增</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CreateTaskPayload, ResourceConflictResponse, TaskMember, TaskPriority } from '../../types';

type AddTaskConflictPreview = {
  assignee_user_id: number | null;
  assignee_label: string;
  preview: ResourceConflictResponse;
};

const props = defineProps<{
  open: boolean;
  taskForm: CreateTaskPayload;
  timelineMembers: TaskMember[];
  addTaskAssigneeIds: number[];
  addTaskDependencyIds: number[];
  availableDependencyTasks: Array<{ task_id: number; name: string }>;
  addTaskConflictSummary: { hasConflict: boolean; totalSignals: number };
  addTaskConflictPreviews: AddTaskConflictPreview[];
  conflictAiSuggestionLoadingKey: string | null;
  getTimelineMemberName: (memberId: number) => string;
  getTaskNameById: (taskId: number) => string;
  formatDate: (value?: string | null) => string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit'): void;
  (e: 'request-ai-suggestion', assigneeUserId: number | null): void;
  (e: 'update:taskForm', value: CreateTaskPayload): void;
  (e: 'update:addTaskAssigneeIds', value: number[]): void;
  (e: 'update:addTaskDependencyIds', value: number[]): void;
}>();

const updateTaskFormField = <K extends keyof CreateTaskPayload>(key: K, value: CreateTaskPayload[K]) => {
  emit('update:taskForm', {
    ...props.taskForm,
    [key]: value,
  });
};

const taskName = computed({
  get: () => props.taskForm.name,
  set: (value: string) => updateTaskFormField('name', value),
});

const taskStartDate = computed({
  get: () => props.taskForm.start_date || '',
  set: (value: string) => updateTaskFormField('start_date', value),
});

const taskEndDate = computed({
  get: () => props.taskForm.end_date || '',
  set: (value: string) => updateTaskFormField('end_date', value),
});

const taskPriority = computed({
  get: () => props.taskForm.priority ?? 2,
  set: (value: TaskPriority) => updateTaskFormField('priority', value),
});

const taskTags = computed({
  get: () => props.taskForm.tags || '',
  set: (value: string) => updateTaskFormField('tags', value),
});

const taskRemark = computed({
  get: () => props.taskForm.task_remark || '',
  set: (value: string) => updateTaskFormField('task_remark', value),
});

const assigneeIdsModel = computed({
  get: () => props.addTaskAssigneeIds,
  set: (value: number[]) => emit('update:addTaskAssigneeIds', value),
});

const dependencyIdsModel = computed({
  get: () => props.addTaskDependencyIds,
  set: (value: number[]) => emit('update:addTaskDependencyIds', value),
});

const getConflictPreviewKey = (assigneeUserId: number | null): string => String(assigneeUserId ?? 'self');
</script>
