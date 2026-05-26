<template>
  <div class="p-6 space-y-6">
    <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
      <div><p class="text-xs text-gray-500 mb-1">開始日期</p><p class="font-medium text-gray-800">{{ formatDate(selectedTask.start_date) || '未設定' }}</p></div>
      <div><p class="text-xs text-gray-500 mb-1">截止日期</p><p class="font-medium text-gray-800">{{ formatDate(selectedTask.end_date) || '未設定' }}</p></div>
    </div>
    <div v-if="selectedTask.task_remark" class="p-4 bg-yellow-50 rounded-xl">
      <h4 class="font-semibold text-gray-700 mb-2">📝 備註</h4>
      <p class="text-gray-600 text-sm">{{ selectedTask.task_remark }}</p>
    </div>
    <div class="p-4 bg-slate-50 rounded-xl">
      <h4 class="font-semibold text-gray-700 mb-2">🔗 前置依賴</h4>
      <select
        :value="selectedTaskDependencyIds"
        multiple
        class="w-full min-h-30 px-3 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white text-sm"
        @change="onDependencySelectChange"
      >
        <option
          v-for="taskOption in selectedTaskDependencyOptions"
          :key="`detail-dependency-option-${taskOption.task_id}`"
          :value="taskOption.task_id"
        >
          {{ taskOption.name }}
        </option>
      </select>
      <p class="text-[11px] text-gray-500 mt-1.5">僅可依賴本專案任務；會自動去重與驗證。</p>
      <div v-if="selectedTaskDependencyIds.length > 0" class="mt-2 flex flex-wrap gap-1.5">
        <span
          v-for="dependencyId in selectedTaskDependencyIds"
          :key="`detail-dependency-chip-${dependencyId}`"
          class="px-2.5 py-1 text-xs rounded-full bg-slate-200 text-slate-700"
        >
          {{ getTaskNameById(dependencyId) }}
        </span>
      </div>
      <div class="mt-3 flex justify-end">
        <button
          type="button"
          @click="$emit('save-dependencies')"
          :disabled="isSavingTaskDependencies"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors disabled:opacity-50"
        >
          {{ isSavingTaskDependencies ? '儲存中...' : '儲存前置依賴' }}
        </button>
      </div>
    </div>

    <div v-if="canManageTaskMembers(selectedTask)" class="p-4 bg-indigo-50/60 rounded-xl">
      <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <span>👥</span> 指派成員
      </h4>
      <div v-if="taskMembersForAssign.length > 0" class="flex flex-wrap gap-2 mb-3">
        <div
          v-for="member in taskMembersForAssign"
          :key="member.user_id"
          class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
          :class="member.role === 0 ? 'bg-primary/20 text-primary' : 'bg-white border border-gray-200 text-gray-700'"
        >
          <span>{{ member.name }}</span>
          <span class="text-gray-400 text-[10px]">{{ member.role === 0 ? '負責人' : '協作者' }}</span>
          <button
            v-if="member.role !== 0"
            @click="$emit('set-owner', member)"
            class="ml-0.5 px-1.5 py-0.5 text-[10px] rounded-md bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
          >主責</button>
          <button
            v-if="member.role !== 0"
            @click="$emit('kick-member', member)"
            class="ml-0.5 text-gray-400 hover:text-red-500 transition-colors leading-none"
          >✕</button>
        </div>
      </div>
      <div v-else class="text-xs text-gray-400 mb-3">尚未指派任何成員</div>
      <div v-if="timelineMembers.length > 0">
        <p class="text-xs text-gray-500 mb-2">快速指派專案成員：</p>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="m in timelineMembers.filter(m => !taskMembersForAssign.some(tm => tm.user_id === m.user_id))"
            :key="m.user_id"
            @click="$emit('quick-assign', m)"
            class="flex items-center gap-1.5 px-3 py-1 bg-white border border-indigo-200 text-indigo-700 text-xs font-medium rounded-full hover:bg-indigo-100 transition-colors"
          >
            <span class="w-5 h-5 bg-indigo-100 rounded-full flex items-center justify-center font-bold text-[10px]">{{ (m.username || m.name || '?')[0].toUpperCase() }}</span>
            {{ m.username || m.name }}
          </button>
          <span v-if="timelineMembers.filter(m => !taskMembersForAssign.some(tm => tm.user_id === m.user_id)).length === 0" class="text-xs text-gray-400">所有成員已加入</span>
        </div>
      </div>
    </div>

    <div>
      <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <span>📋</span> 子任務
        <span class="text-sm font-normal text-gray-500">({{ taskSubtasks.filter(s => s.completed).length }}/{{ taskSubtasks.length }})</span>
      </h4>
      <div v-if="taskSubtasks.length > 0" class="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
        <div class="h-full bg-primary rounded-full transition-all duration-300" :style="{ width: subtaskProgress + '%' }"></div>
      </div>
      <div class="space-y-2 mb-3">
        <div v-for="subtask in taskSubtasks" :key="subtask.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group hover:bg-gray-100 transition-colors">
          <input type="checkbox" :checked="subtask.completed" @change="$emit('toggle-subtask', subtask)" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" />
          <span :class="['flex-1 text-sm', subtask.completed ? 'line-through text-gray-400' : 'text-gray-700']">{{ subtask.name }}</span>
          <button @click="$emit('delete-subtask', subtask)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all">🗑️</button>
        </div>
        <div v-if="taskSubtasks.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無子任務</div>
      </div>
      <div class="flex gap-2">
        <input :value="newSubtaskName" type="text" placeholder="輸入子任務名稱..." @input="$emit('update:new-subtask-name', ($event.target as HTMLInputElement).value)" @keyup.enter="$emit('add-subtask')" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
        <button @click="$emit('add-subtask')" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">新增</button>
      </div>
    </div>

    <div>
      <div class="flex items-center justify-between mb-3">
        <h4 class="font-semibold text-gray-700 flex items-center gap-2">
          <span>📎</span> 附件
          <span class="text-xs text-gray-400 font-normal">({{ taskFiles.length }})</span>
        </h4>
        <label class="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-lg hover:bg-primary/20 transition-colors">
          <span>＋</span> 上傳檔案
          <input type="file" class="hidden" accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.csv,.mp4,.mov" @change="$emit('file-upload', $event)" />
        </label>
      </div>
      <div v-if="taskFiles.length === 0" class="text-center py-6 text-gray-400 text-sm bg-gray-50 rounded-xl border border-dashed border-gray-200">
        尚無附件，點擊「上傳檔案」新增
      </div>
      <div v-else class="space-y-2">
        <div v-for="file in taskFiles" :key="file.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors group">
          <img v-if="isImageFile(file.original_filename)" :src="`${apiBaseUrl}/tasks/files/${file.filename}`" class="w-12 h-12 object-cover rounded-lg border border-gray-200 shrink-0" :alt="file.original_filename" />
          <span v-else class="text-3xl shrink-0">{{ getFileIcon(file.original_filename) }}</span>
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-gray-700 truncate">{{ file.original_filename }}</p>
            <p class="text-xs text-gray-400">{{ formatFileSize(file.file_size) }} · {{ formatDateTime(file.uploaded_at) }}</p>
          </div>
          <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button @click="$emit('download-file', file)" class="w-8 h-8 flex items-center justify-center text-primary hover:bg-primary/10 rounded-lg transition-colors" title="下載">⬇️</button>
            <button @click="$emit('delete-file', file.id)" class="w-8 h-8 flex items-center justify-center text-red-400 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors" title="刪除">🗑️</button>
          </div>
        </div>
      </div>
    </div>

    <div>
      <div class="mb-4 flex items-center justify-between gap-3">
        <h4 class="font-semibold text-gray-700 flex items-center gap-2">
          <span>💬</span> 留言
          <span class="text-xs text-gray-400 font-normal">({{ taskComments.length }})</span>
        </h4>
        <button @click="$emit('summarize-comments')" :disabled="isSummarizingComments" class="px-3 py-1.5 bg-violet-100 text-violet-700 text-xs font-semibold rounded-lg hover:bg-violet-200 transition-colors disabled:opacity-50">
          {{ isSummarizingComments ? '摘要中...' : '🤖 AI 摘要' }}
        </button>
      </div>

      <div v-if="commentSummary" class="mb-4 p-4 bg-violet-50 border border-violet-100 rounded-xl text-sm text-gray-700 space-y-3">
        <div>
          <p class="font-semibold text-violet-800 mb-1">決議</p>
          <ul v-if="commentSummary.decisions.length" class="list-disc list-inside space-y-1">
            <li v-for="(item, idx) in commentSummary.decisions" :key="`d-${idx}`">{{ item }}</li>
          </ul>
          <p v-else class="text-gray-400">暫無</p>
        </div>
        <div>
          <p class="font-semibold text-violet-800 mb-1">風險</p>
          <ul v-if="commentSummary.risks.length" class="list-disc list-inside space-y-1">
            <li v-for="(item, idx) in commentSummary.risks" :key="`r-${idx}`">{{ item }}</li>
          </ul>
          <p v-else class="text-gray-400">暫無</p>
        </div>
        <div>
          <p class="font-semibold text-violet-800 mb-1">下一步</p>
          <ul v-if="commentSummary.next_actions.length" class="list-disc list-inside space-y-1">
            <li v-for="(item, idx) in commentSummary.next_actions" :key="`n-${idx}`">{{ item }}</li>
          </ul>
          <p v-else class="text-gray-400">暫無</p>
        </div>
        <p v-if="commentSummaryMeta?.truncated" class="text-xs text-violet-600">
          已自動截斷較舊留言，摘要以最近 {{ commentSummaryMeta.used_comments }} / {{ commentSummaryMeta.total_comments }} 筆為主。
        </p>
      </div>

      <div class="space-y-3 max-h-60 overflow-y-auto mb-4">
        <div v-for="comment in taskComments" :key="comment.comment_id" class="flex gap-3 p-3 bg-gray-50 rounded-xl group">
          <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
            {{ comment.user_name?.charAt(0)?.toUpperCase() }}
          </div>
          <div class="flex-1">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-medium text-gray-700">{{ comment.user_name }}</span>
              <span class="text-xs text-gray-400">{{ formatDateTime(comment.created_at) }}</span>
            </div>
            <p class="text-sm text-gray-600">{{ comment.task_message }}</p>
          </div>
          <button @click="$emit('delete-comment', comment.comment_id)" class="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all shrink-0" title="刪除留言">✕</button>
        </div>
        <div v-if="taskComments.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無留言</div>
      </div>
      <div class="flex gap-2">
        <input :value="newComment" type="text" placeholder="新增留言..." @input="$emit('update:new-comment', ($event.target as HTMLInputElement).value)" @keyup.enter="$emit('add-comment')" class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
        <button @click="$emit('add-comment')" :disabled="!newComment.trim()" class="px-4 py-2.5 bg-primary text-white font-medium rounded-xl hover:brightness-110 transition-all disabled:opacity-50">傳送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate, formatDateTime, formatFileSize, getFileIcon, isImageFile } from '../../utils/formatters';
import type { Task, TaskComment, TaskCommentSummary, TaskFile, TaskMember, Subtask } from '../../types';

defineProps<{
  selectedTask: Task;
  selectedTaskDependencyIds: number[];
  selectedTaskDependencyOptions: Array<{ task_id: number; name: string }>;
  isSavingTaskDependencies: boolean;
  getTaskNameById: (id: number) => string;
  canManageTaskMembers: (task: Task) => boolean;
  taskMembersForAssign: TaskMember[];
  timelineMembers: TaskMember[];
  taskSubtasks: Subtask[];
  subtaskProgress: number;
  newSubtaskName: string;
  taskFiles: TaskFile[];
  apiBaseUrl: string;
  taskComments: TaskComment[];
  isSummarizingComments: boolean;
  commentSummary: TaskCommentSummary | null;
  commentSummaryMeta: { total_comments?: number; used_comments?: number; truncated?: boolean } | null;
  newComment: string;
}>();

const emit = defineEmits<{
  (e: 'update:selected-task-dependency-ids', value: number[]): void;
  (e: 'save-dependencies'): void;
  (e: 'set-owner', member: TaskMember): void;
  (e: 'kick-member', member: TaskMember): void;
  (e: 'quick-assign', member: TaskMember): void;
  (e: 'toggle-subtask', subtask: Subtask): void;
  (e: 'delete-subtask', subtask: Subtask): void;
  (e: 'update:new-subtask-name', value: string): void;
  (e: 'add-subtask'): void;
  (e: 'file-upload', event: Event): void;
  (e: 'download-file', file: TaskFile): void;
  (e: 'delete-file', fileId: number): void;
  (e: 'summarize-comments'): void;
  (e: 'delete-comment', commentId: number): void;
  (e: 'update:new-comment', value: string): void;
  (e: 'add-comment'): void;
}>();

const onDependencySelectChange = (event: Event) => {
  const target = event.target as HTMLSelectElement;
  const ids = Array.from(target.selectedOptions)
    .map((option) => Number(option.value))
    .filter((id) => Number.isInteger(id) && id > 0);
  emit('update:selected-task-dependency-ids', ids);
};
</script>
