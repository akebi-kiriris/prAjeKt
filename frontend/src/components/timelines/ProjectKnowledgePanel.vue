<template>
  <div class="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
    <div class="flex items-center justify-between gap-3 mb-3">
      <div>
        <p class="text-sm font-semibold text-indigo-700">專案檔案區</p>
        <p class="text-xs text-indigo-500">支援上傳、批次操作與 RAG 引用來源</p>
      </div>
      <div class="flex items-center gap-2">
        <input
          ref="fileInput"
          type="file"
          class="hidden"
          @change="handleUpload"
        />
        <button
          type="button"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-100 transition-colors disabled:opacity-60"
          :disabled="uploading"
          @click="fileInput?.click()"
        >
          {{ uploading ? '上傳中...' : '上傳檔案' }}
        </button>
        <button type="button" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-100 transition-colors" @click="$emit('refresh')">刷新</button>
      </div>
    </div>

    <div class="grid md:grid-cols-3 gap-2 mb-3">
      <input
        :value="query"
        type="text"
        placeholder="搜尋檔名"
        class="px-3 py-2 text-xs border border-indigo-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
        @input="$emit('update:query', ($event.target as HTMLInputElement).value)"
      />
      <select
        :value="sort"
        class="px-3 py-2 text-xs border border-indigo-200 rounded-lg bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
        @change="$emit('update:sort', ($event.target as HTMLSelectElement).value as 'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc')"
      >
        <option value="created_desc">最新建立</option>
        <option value="created_asc">最早建立</option>
        <option value="name_asc">檔名 A-Z</option>
        <option value="name_desc">檔名 Z-A</option>
        <option value="status_asc">狀態</option>
      </select>
      <select
        :value="status"
        class="px-3 py-2 text-xs border border-indigo-200 rounded-lg bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
        @change="$emit('update:status', ($event.target as HTMLSelectElement).value)"
      >
        <option value="">全部狀態</option>
        <option value="uploaded">uploaded</option>
        <option value="indexing">indexing</option>
        <option value="ready">ready</option>
        <option value="failed">failed</option>
      </select>
    </div>

    <div class="flex items-center gap-2 mb-3">
      <button type="button" class="px-3 py-1.5 text-xs rounded-lg border border-red-200 text-red-600 bg-white hover:bg-red-50 disabled:opacity-40" :disabled="selectedIds.length === 0" @click="$emit('batch-delete')">批次刪除</button>
      <button type="button" class="px-3 py-1.5 text-xs rounded-lg border border-amber-200 text-amber-700 bg-white hover:bg-amber-50 disabled:opacity-40" :disabled="selectedIds.length === 0" @click="$emit('batch-reindex')">批次重建</button>
      <button type="button" class="px-3 py-1.5 text-xs rounded-lg border border-indigo-200 text-indigo-700 bg-white hover:bg-indigo-50" @click="$emit('refresh')">套用篩選</button>
    </div>

    <p v-if="error" class="mb-2 text-xs text-red-600">{{ error }}</p>
    <div v-if="loading" class="text-xs text-indigo-500">載入中...</div>
    <div v-else-if="documents.length === 0" class="text-xs text-indigo-400">目前沒有檔案</div>
    <div v-else class="space-y-2 mb-3">
      <div v-for="doc in documents" :key="`pk-doc-${doc.id}`" class="p-2.5 bg-white border border-indigo-100 rounded-lg text-xs flex items-start gap-2">
        <input type="checkbox" class="mt-0.5" :checked="selectedIds.includes(doc.id)" @change="$emit('toggle-selection', doc.id)" />
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2">
            <p class="font-medium text-indigo-700 truncate">{{ doc.original_filename || doc.filename }}</p>
            <span class="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">{{ doc.status }}</span>
          </div>
          <p class="text-indigo-500 mt-0.5">
            {{ typeof doc.chunk_count === 'number' ? `${doc.chunk_count} chunks` : '索引數未知' }}
          </p>
          <p v-if="doc.error_message" class="text-red-500 mt-0.5">{{ doc.error_message }}</p>
        </div>
        <div class="flex items-center gap-1">
          <button type="button" class="px-2 py-1 border border-indigo-200 rounded text-indigo-700 hover:bg-indigo-50" @click="$emit('download', doc)">下載</button>
          <button type="button" class="px-2 py-1 border border-indigo-200 rounded text-indigo-700 hover:bg-indigo-50" @click="$emit('preview', doc)">預覽</button>
        </div>
      </div>
    </div>

    <div>
      <p class="text-xs font-semibold text-indigo-700 mb-1">最近操作</p>
      <div v-if="events.length === 0" class="text-xs text-indigo-400">尚無紀錄</div>
      <div v-else class="space-y-1 max-h-24 overflow-y-auto pr-1">
        <p v-for="evt in events" :key="`pk-evt-${evt.id}`" class="text-xs text-indigo-600">
          {{ evt.event_type }} · #{{ evt.document_id || '-' }} · {{ formatDateTime(evt.created_at || '') }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import type { KnowledgeDocumentEventItem, KnowledgeDocumentItem } from '../../types';

defineProps<{
  documents: KnowledgeDocumentItem[];
  events: KnowledgeDocumentEventItem[];
  loading: boolean;
  uploading: boolean;
  selectedIds: number[];
  query: string;
  sort: 'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc';
  status: string;
  error: string;
  formatDateTime: (value: string) => string;
}>();

const emit = defineEmits<{
  (e: 'upload', event: Event): void;
  (e: 'refresh'): void;
  (e: 'batch-delete'): void;
  (e: 'batch-reindex'): void;
  (e: 'toggle-selection', documentId: number): void;
  (e: 'download', document: KnowledgeDocumentItem): void;
  (e: 'preview', document: KnowledgeDocumentItem): void;
  (e: 'update:query', value: string): void;
  (e: 'update:sort', value: 'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc'): void;
  (e: 'update:status', value: string): void;
}>();

const fileInput = ref<HTMLInputElement | null>(null);

const handleUpload = (event: Event) => {
  emit('upload', event);
  if (fileInput.value) {
    fileInput.value.value = '';
  }
};
</script>
