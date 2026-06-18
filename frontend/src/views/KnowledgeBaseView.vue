<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <div class="mx-auto max-w-6xl space-y-6">
      <header class="overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-br from-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]">
        <div class="relative px-5 py-5 md:px-6 md:py-6">
          <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />
          <div class="relative flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
                PERSONAL KNOWLEDGE
              </p>
              <h1 class="text-2xl font-bold text-slate-800">個人知識庫</h1>
              <p class="mt-1 text-sm text-slate-500">管理會被 RAG 規劃引用的私人文件。</p>
            </div>
        <div class="flex items-center gap-2">
          <input
            ref="fileInput"
            type="file"
            class="hidden"
            accept=".md,.txt,.pdf,text/markdown,text/plain,application/pdf"
            @change="handleUpload"
          />
          <button
            type="button"
            class="rounded-lg border border-emerald-200 bg-white px-4 py-2 text-sm font-medium text-emerald-700 transition-colors hover:bg-emerald-50 disabled:opacity-50"
            :disabled="uploading"
            @click="fileInput?.click()"
          >
            {{ uploading ? '上傳中...' : '上傳文件' }}
          </button>
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100"
            @click="loadDocuments"
          >
            刷新
          </button>
        </div>
          </div>
        </div>
      </header>

      <section class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <div class="grid gap-3 md:grid-cols-[1fr_180px_180px]">
          <input
            v-model="query"
            type="text"
            placeholder="搜尋檔名"
            class="rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
            @keyup.enter="applyFilters"
          />
          <select
            v-model="status"
            class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          >
            <option value="">全部狀態</option>
            <option value="uploaded">uploaded</option>
            <option value="indexing">indexing</option>
            <option value="ready">ready</option>
            <option value="failed">failed</option>
          </select>
          <select
            v-model="sort"
            class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100"
          >
            <option value="created_desc">最新建立</option>
            <option value="created_asc">最早建立</option>
            <option value="name_asc">檔名 A-Z</option>
            <option value="name_desc">檔名 Z-A</option>
            <option value="status_asc">狀態</option>
          </select>
        </div>
        <div class="mt-3 flex items-center justify-between gap-3">
          <p class="text-xs text-slate-400">支援 md、txt、pdf。個人知識庫不會帶入 project_id。</p>
          <button
            type="button"
            class="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700"
            @click="applyFilters"
          >
            套用篩選
          </button>
        </div>
      </section>

      <p v-if="errorMessage" class="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
        {{ errorMessage }}
      </p>

      <section class="rounded-xl border border-slate-200 bg-white shadow-sm">
        <div v-if="loading" class="flex items-center justify-center py-20">
          <div class="h-8 w-8 animate-spin rounded-full border-4 border-emerald-500 border-t-transparent"></div>
        </div>

        <div v-else-if="documents.length === 0" class="py-20 text-center">
          <p class="text-lg font-medium text-slate-500">目前沒有文件</p>
          <p class="mt-1 text-sm text-slate-400">上傳文件後，RAG 規劃就能引用你的私人知識。</p>
        </div>

        <div v-else class="divide-y divide-slate-100">
          <article
            v-for="doc in documents"
            :key="doc.id"
            class="flex flex-col gap-3 p-4 md:flex-row md:items-center"
          >
            <div class="flex min-w-0 flex-1 items-start gap-3">
              <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-lg">
                {{ getFileIcon(doc.original_filename || doc.filename) }}
              </div>
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-center gap-2">
                  <p class="truncate font-medium text-slate-800">{{ doc.original_filename || doc.filename }}</p>
                  <span :class="statusClass(doc.status)" class="rounded-full px-2 py-0.5 text-xs font-medium">
                    {{ doc.status }}
                  </span>
                </div>
                <p class="mt-1 text-xs text-slate-400">
                  {{ formatFileSize(doc.size_bytes) || '大小未知' }}
                  <span> · {{ typeof doc.chunk_count === 'number' ? `${doc.chunk_count} chunks` : '索引數未知' }}</span>
                  <span v-if="doc.created_at"> · 建立於 {{ formatDateTime(doc.created_at) }}</span>
                </p>
                <p v-if="doc.error_message" class="mt-1 text-xs text-red-500">{{ doc.error_message }}</p>
              </div>
            </div>
            <div class="flex shrink-0 items-center gap-2">
              <button
                type="button"
                class="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-700 transition-colors hover:bg-amber-100 disabled:opacity-50"
                :disabled="busyDocumentId === doc.id"
                @click="reindexDocument(doc)"
              >
                重建索引
              </button>
              <button
                type="button"
                class="rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-medium text-red-600 transition-colors hover:bg-red-100 disabled:opacity-50"
                :disabled="busyDocumentId === doc.id"
                @click="deleteDocument(doc)"
              >
                刪除
              </button>
            </div>
          </article>
        </div>
      </section>

      <footer class="flex items-center justify-between">
        <p class="text-sm text-slate-400">共 {{ totalCount }} 份文件</p>
        <div class="flex items-center gap-2">
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 disabled:opacity-40"
            :disabled="offset === 0 || loading"
            @click="previousPage"
          >
            上一頁
          </button>
          <button
            type="button"
            class="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm text-slate-600 disabled:opacity-40"
            :disabled="documents.length < limit || loading"
            @click="nextPage"
          >
            下一頁
          </button>
        </div>
      </footer>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { toast } from 'vue-sonner';
import { knowledgeService } from '../services/knowledgeService';
import { getApiErrorMessage } from '../utils/apiError';
import type { KnowledgeDocumentItem } from '../types';
import { formatDateTime, formatFileSize, getFileIcon } from '../utils/formatters';
import { useConfirm } from '../composables/useConfirm';

const { confirm } = useConfirm();

const fileInput = ref<HTMLInputElement | null>(null);
const documents = ref<KnowledgeDocumentItem[]>([]);
const loading = ref(false);
const uploading = ref(false);
const errorMessage = ref('');
const busyDocumentId = ref<number | null>(null);
const query = ref('');
const status = ref('');
const sort = ref<'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc'>('created_desc');
const limit = 20;
const offset = ref(0);
const totalCount = ref(0);

const loadDocuments = async () => {
  loading.value = true;
  errorMessage.value = '';
  try {
    const res = await knowledgeService.listDocuments({
      limit,
      offset: offset.value,
      q: query.value.trim() || undefined,
      status: status.value || undefined,
      sort: sort.value,
    });
    documents.value = res.data.documents || [];
    totalCount.value = res.data.meta?.count ?? documents.value.length;
  } catch (err: unknown) {
    errorMessage.value = getApiErrorMessage(err, '讀取個人知識庫失敗');
  } finally {
    loading.value = false;
  }
};

const applyFilters = () => {
  offset.value = 0;
  void loadDocuments();
};

const handleUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement | null;
  const file = target?.files?.[0];
  if (!file) return;
  uploading.value = true;
  try {
    await knowledgeService.uploadDocument(file);
    toast.success('文件已上傳');
    offset.value = 0;
    await loadDocuments();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '上傳文件失敗'));
  } finally {
    uploading.value = false;
    if (fileInput.value) fileInput.value.value = '';
  }
};

const reindexDocument = async (document: KnowledgeDocumentItem) => {
  busyDocumentId.value = document.id;
  try {
    await knowledgeService.reindexDocument(document.id);
    toast.success('已重建索引');
    await loadDocuments();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '重建索引失敗'));
  } finally {
    busyDocumentId.value = null;
  }
};

const deleteDocument = async (document: KnowledgeDocumentItem) => {
  if (!await confirm({
    title: `確定刪除「${document.original_filename || document.filename}」？`,
    message: '刪除後，RAG 規劃將不再引用這份文件。',
    danger: true,
  })) return;

  busyDocumentId.value = document.id;
  try {
    await knowledgeService.deleteDocument(document.id);
    toast.success('文件已刪除');
    await loadDocuments();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '刪除文件失敗'));
  } finally {
    busyDocumentId.value = null;
  }
};

const previousPage = () => {
  offset.value = Math.max(0, offset.value - limit);
  void loadDocuments();
};

const nextPage = () => {
  offset.value += limit;
  void loadDocuments();
};

const statusClass = (value: string) => {
  if (value === 'ready') return 'bg-emerald-100 text-emerald-700';
  if (value === 'failed') return 'bg-red-100 text-red-700';
  if (value === 'indexing') return 'bg-amber-100 text-amber-700';
  return 'bg-slate-100 text-slate-600';
};

onMounted(() => {
  void loadDocuments();
});
</script>
