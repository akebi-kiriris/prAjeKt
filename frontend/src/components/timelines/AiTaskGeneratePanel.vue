<template>
  <div class="p-6">
    <div v-if="isGeneratingAi" class="text-center py-12">
      <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-spin">
        <span class="text-2xl">🤖</span>
      </div>
      <p class="text-gray-600 font-medium">AI 正在生成任務建議...</p>
      <p class="text-gray-400 text-sm mt-2">請稍候，正在分析專案內容</p>
    </div>

    <div v-else-if="aiGeneratedTasks.length === 0" class="py-8">
      <p class="text-gray-500 mb-4 text-center">可輸入需求情境，讓 AI 透過 MCP 生成更貼近專案的任務建議</p>
      <div class="space-y-3 mb-5">
        <label class="block text-sm font-medium text-gray-700">需求描述（可選）</label>
        <textarea
          :value="aiPrompt"
          rows="4"
          placeholder="例如：這個月要完成登入流程重構，請拆成後端 API、前端頁面、測試與上線準備"
          class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"
          @input="$emit('update:ai-prompt', ($event.target as HTMLTextAreaElement).value)"
        ></textarea>
        <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600">
          <label class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input :checked="useRagPlanning" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" @change="$emit('update:use-rag-planning', ($event.target as HTMLInputElement).checked)" />
            使用 RAG 規劃建議
          </label>
          <label v-if="!useRagPlanning" class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input :checked="useCopilotMcp" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" @change="$emit('update:use-copilot-mcp', ($event.target as HTMLInputElement).checked)" />
            優先使用 AI + MCP 工具路由
          </label>
          <label v-if="useRagPlanning" class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input :checked="usePersonalKnowledge" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" @change="$emit('update:use-personal-knowledge', ($event.target as HTMLInputElement).checked)" />
            納入個人知識庫
          </label>
          <label v-if="useRagPlanning" class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input :checked="useProjectKnowledge" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" @change="onProjectKnowledgeToggle" />
            納入專案檔案
          </label>
          <label class="inline-flex items-center gap-2 cursor-pointer select-none">
            <input :checked="autoCreateAfterGenerate" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" @change="$emit('update:auto-create-after-generate', ($event.target as HTMLInputElement).checked)" />
            生成後直接建立任務
          </label>
        </div>
        <p v-if="ragErrorMessage" class="text-sm text-red-600">{{ ragErrorMessage }}</p>
      </div>
      <div class="text-center">
        <button @click="$emit('generate')" class="px-6 py-3 bg-linear-to-r from-purple-500 to-indigo-500 text-white font-semibold rounded-xl hover:brightness-110 transition-all shadow-lg shadow-purple-200">
          {{ useRagPlanning ? '📚 RAG 規劃生成' : (useCopilotMcp ? '✨ AI 智慧生成' : '🤖 開始生成') }}
        </button>
      </div>
    </div>

    <div v-else class="space-y-4">
      <div class="flex items-center justify-between mb-4">
        <p class="text-sm text-gray-600">共 {{ aiGeneratedTasks.length }} 個建議任務，已選 {{ selectedAiTasks.length }} 個</p>
        <div class="flex gap-2">
          <button @click="$emit('toggle-all')" class="text-sm text-primary hover:underline">{{ selectedAiTasks.length === aiGeneratedTasks.length ? '全部取消' : '全部選取' }}</button>
          <button @click="$emit('reset-generated')" class="text-sm text-gray-400 hover:text-gray-600">重新生成</button>
        </div>
      </div>
      <div v-if="ragSourceReferences.length > 0" class="p-3 rounded-xl border border-indigo-100 bg-indigo-50/60">
        <p class="text-xs font-semibold text-indigo-700 mb-2">來源依據（{{ ragSourceReferences.length }}）</p>
        <p v-if="ragSummary" class="text-xs text-indigo-600 mb-2">{{ ragSummary }}</p>
        <div class="space-y-2 max-h-40 overflow-y-auto pr-1">
          <div v-for="ref in ragSourceReferences" :key="`${ref.source_type}-${ref.source_id}`" class="text-xs text-indigo-700 bg-white/80 border border-indigo-100 rounded-lg p-2">
            <p class="font-medium">{{ getSourceReferenceLabel(ref.source_type) }} · score {{ Number(ref.score || 0).toFixed(2) }}</p>
            <p class="truncate">{{ ref.title }}</p>
            <p class="text-indigo-500 line-clamp-2">{{ ref.snippet }}</p>
          </div>
        </div>
      </div>
      <div class="space-y-3 max-h-80 overflow-y-auto">
        <div
          v-for="(task, index) in aiGeneratedTasks"
          :key="index"
          @click="$emit('toggle-task', index)"
          :class="['p-4 rounded-xl border-2 cursor-pointer transition-all', selectedAiTasks.includes(index) ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-gray-300']"
        >
          <div class="flex items-start gap-3">
            <div :class="['w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5', selectedAiTasks.includes(index) ? 'border-purple-500 bg-purple-500' : 'border-gray-300']">
              <span v-if="selectedAiTasks.includes(index)" class="text-white text-xs">✓</span>
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-2 mb-1">
                <span class="font-medium text-gray-800">{{ task.name }}</span>
                <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', getAiPriorityClass(task.priority)]">{{ getPriorityLabel(task.priority) }}</span>
              </div>
              <div class="flex items-center gap-3 text-xs text-gray-500">
                <span>📅 {{ formatDate(task.start_date) }} - {{ formatDate(task.end_date) }}</span>
                <span v-if="task.tags">🏷️ {{ task.tags }}</span>
              </div>
              <p v-if="(task.depends_on_task_refs || []).length > 0" class="text-xs text-indigo-600 mt-1">
                🔗 前置：{{ (task.depends_on_task_refs || []).join('、') }}
              </p>
              <p v-if="task.remark" class="text-sm text-gray-500 mt-1">{{ task.remark }}</p>
            </div>
          </div>
        </div>
      </div>
      <div class="flex gap-3 pt-2">
        <button @click="$emit('close')" class="flex-1 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-xl hover:bg-gray-50 transition-colors">取消</button>
        <button @click="$emit('batch-create')" :disabled="selectedAiTasks.length === 0" :class="['flex-1 py-2.5 font-semibold rounded-xl transition-all', selectedAiTasks.length > 0 ? 'bg-linear-to-r from-purple-500 to-indigo-500 text-white hover:brightness-110 shadow-lg shadow-purple-200' : 'bg-gray-100 text-gray-400 cursor-not-allowed']">
          新增選取任務 ({{ selectedAiTasks.length }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatDate } from '../../utils/formatters';
import { getAiPriorityClass, getPriorityLabel, getSourceReferenceLabel } from '../../utils/timelineDetailUtils';
import type { AiGeneratedTask, SourceReference } from '../../types';

const props = defineProps<{
  isGeneratingAi: boolean;
  aiGeneratedTasks: AiGeneratedTask[];
  selectedAiTasks: number[];
  aiPrompt: string;
  useRagPlanning: boolean;
  useCopilotMcp: boolean;
  usePersonalKnowledge: boolean;
  useProjectKnowledge: boolean;
  autoCreateAfterGenerate: boolean;
  ragErrorMessage: string;
  ragSourceReferences: SourceReference[];
  ragSummary: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'generate'): void;
  (e: 'toggle-all'): void;
  (e: 'toggle-task', index: number): void;
  (e: 'reset-generated'): void;
  (e: 'batch-create'): void;
  (e: 'touch-project-knowledge'): void;
  (e: 'update:ai-prompt', value: string): void;
  (e: 'update:use-rag-planning', value: boolean): void;
  (e: 'update:use-copilot-mcp', value: boolean): void;
  (e: 'update:use-personal-knowledge', value: boolean): void;
  (e: 'update:use-project-knowledge', value: boolean): void;
  (e: 'update:auto-create-after-generate', value: boolean): void;
}>();

const onProjectKnowledgeToggle = (event: Event) => {
  emit('touch-project-knowledge');
  emit('update:use-project-knowledge', (event.target as HTMLInputElement).checked);
};
</script>
