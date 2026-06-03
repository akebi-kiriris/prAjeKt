<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <section class="mx-auto w-full max-w-6xl">
      <header
        class="mb-6 overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-br from-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]"
      >
        <div class="relative px-5 py-5 md:px-6 md:py-6">
          <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />

          <div class="relative flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
                RECOVERY ZONE
              </p>
              <h1 class="text-[clamp(1.4rem,2vw,1.9rem)] font-black tracking-[0.01em] text-slate-900">垃圾桶</h1>
              <p class="mt-2 max-w-xl text-sm leading-6 text-slate-600">
                這裡暫存已刪除的任務與專案。你可以先檢查內容，再決定還原或永久刪除。
              </p>
            </div>
            <div class="grid grid-cols-2 gap-2">
              <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center shadow-sm">
                <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">已刪任務</p>
                <p class="text-xl font-extrabold text-slate-800">{{ tasks.length }}</p>
              </div>
              <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-center shadow-sm">
                <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">已刪專案</p>
                <p class="text-xl font-extrabold text-slate-800">{{ timelines.length }}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div
        v-if="loading"
        class="flex items-center justify-center rounded-3xl border border-slate-200 bg-white py-24 shadow-[0_12px_28px_rgba(15,23,42,0.06)]"
      >
        <div class="grid justify-items-center gap-3">
          <div class="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p class="text-xs tracking-[0.04em] text-slate-500">載入垃圾桶內容中...</p>
        </div>
      </div>

      <template v-else>
        <div
          v-if="tasks.length === 0 && timelines.length === 0"
          class="rounded-3xl border border-dashed border-slate-300 bg-white py-24 text-center shadow-[0_12px_28px_rgba(15,23,42,0.06)]"
        >
          <div class="mx-auto mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl border border-slate-200 bg-slate-50 text-3xl">
            🗑️
          </div>
          <p class="text-lg font-bold text-slate-700">垃圾桶目前是空的</p>
          <p class="mt-1 text-sm text-slate-500">刪除任務或專案後會出現在這裡</p>
        </div>

        <template v-else>
          <div class="grid gap-5 lg:grid-cols-2">
            <section
              class="rounded-3xl border border-slate-200 bg-white p-4 shadow-[0_12px_26px_rgba(15,23,42,0.05)] md:p-5"
              :class="{ 'opacity-70': timelines.length === 0 }"
            >
              <h2 class="mb-3 flex items-center justify-between gap-3">
                <span class="text-base font-bold text-slate-800">已刪除的專案</span>
                <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{{ timelines.length }}</span>
              </h2>

              <div v-if="timelines.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                目前沒有已刪專案
              </div>

              <div v-else class="space-y-3">
                <article
                  v-for="tl in timelines"
                  :key="tl.id"
                  class="group rounded-2xl border border-slate-200 bg-slate-50/65 p-4 transition hover:-translate-y-px hover:border-slate-300 hover:bg-white hover:shadow-[0_10px_24px_rgba(15,23,42,0.08)]"
                >
                  <div class="mb-1 flex items-start justify-between gap-3">
                    <p class="min-w-0 truncate text-[0.96rem] font-bold text-slate-800">{{ tl.name }}</p>
                    <span class="shrink-0 rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[0.68rem] tracking-[0.05em] text-slate-500">
                      專案
                    </span>
                  </div>
                  <p class="text-xs leading-5 text-slate-500">
                    刪除於 {{ formatDate(tl.deleted_at) }}
                    <span v-if="tl.start_date">
                      · {{ formatDateShort(tl.start_date) }} ~ {{ formatDateShort(tl.end_date) }}
                    </span>
                  </p>
                  <p v-if="!tl.is_owner" class="mt-2 inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-[0.7rem] font-semibold text-amber-700">
                    非建立者，無法操作
                  </p>

                  <div v-if="tl.is_owner" class="mt-3 flex items-center gap-2">
                    <button
                      @click="restoreTimeline(tl)"
                      class="rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-white shadow-[0_6px_16px_rgba(37,99,235,0.28)] transition hover:-translate-y-px hover:shadow-[0_10px_22px_rgba(37,99,235,0.34)]"
                    >
                      還原
                    </button>
                    <button
                      @click="permanentDeleteTimeline(tl)"
                      class="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-sm font-semibold text-red-600 transition hover:bg-red-50"
                    >
                      永久刪除
                    </button>
                  </div>
                </article>
              </div>
            </section>

            <section
              class="rounded-3xl border border-slate-200 bg-white p-4 shadow-[0_12px_26px_rgba(15,23,42,0.05)] md:p-5"
              :class="{ 'opacity-70': tasks.length === 0 }"
            >
              <h2 class="mb-3 flex items-center justify-between gap-3">
                <span class="text-base font-bold text-slate-800">已刪除的任務</span>
                <span class="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-semibold text-slate-600">{{ tasks.length }}</span>
              </h2>

              <div v-if="tasks.length === 0" class="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
                目前沒有已刪任務
              </div>

              <div v-else class="space-y-3">
                <article
                  v-for="task in tasks"
                  :key="task.task_id"
                  class="group rounded-2xl border border-slate-200 bg-slate-50/65 p-4 transition hover:-translate-y-px hover:border-slate-300 hover:bg-white hover:shadow-[0_10px_24px_rgba(15,23,42,0.08)]"
                >
                  <div class="mb-1 flex items-start justify-between gap-2">
                    <p class="min-w-0 truncate text-[0.96rem] font-bold text-slate-800">{{ task.name }}</p>
                    <span :class="priorityBadge(task.priority)" class="shrink-0 rounded-full px-2 py-0.5 text-[0.68rem] font-semibold tracking-[0.04em]">
                      {{ priorityLabel(task.priority) }}
                    </span>
                  </div>
                  <p class="text-xs leading-5 text-slate-500">
                    刪除於 {{ formatDate(task.deleted_at) }}
                    <span v-if="task.end_date"> · 截止 {{ formatDateShort(task.end_date) }}</span>
                  </p>
                  <p v-if="!task.is_owner" class="mt-2 inline-flex rounded-full bg-amber-100 px-2 py-0.5 text-[0.7rem] font-semibold text-amber-700">
                    非建立者，無法操作
                  </p>

                  <div v-if="task.is_owner" class="mt-3 flex items-center gap-2">
                    <button
                      @click="restoreTask(task)"
                      class="rounded-lg bg-primary px-3 py-1.5 text-sm font-semibold text-white shadow-[0_6px_16px_rgba(37,99,235,0.28)] transition hover:-translate-y-px hover:shadow-[0_10px_22px_rgba(37,99,235,0.34)]"
                    >
                      還原
                    </button>
                    <button
                      @click="permanentDeleteTask(task)"
                      class="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-sm font-semibold text-red-600 transition hover:bg-red-50"
                    >
                      永久刪除
                    </button>
                  </div>
                </article>
              </div>
            </section>
          </div>
        </template>
      </template>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { toast } from 'vue-sonner';
import { trashService } from '../services/trashService';
import type { TrashTask, TrashTimeline } from '../types';
import { formatDateTimeCompact as formatDate, formatDateShort } from '../utils/formatters';
import { useConfirm } from '../composables/useConfirm';
import { getApiErrorMessage } from '../utils/apiError';

const { confirm } = useConfirm();

const loading = ref(true);
const tasks = ref<TrashTask[]>([]);
const timelines = ref<TrashTimeline[]>([]);

const loadTrash = async () => {
  loading.value = true;
  try {
    const res = await trashService.getAll();
    tasks.value = res.data.tasks || [];
    timelines.value = res.data.timelines || [];
  } catch {
    toast.error('無法載入垃圾桶內容');
  } finally {
    loading.value = false;
  }
};

const restoreTask = async (task: TrashTask) => {
  try {
    await trashService.restoreTask(task.task_id);
    tasks.value = tasks.value.filter(t => t.task_id !== task.task_id);
  } catch (err) {
    toast.error(getApiErrorMessage(err, '還原失敗'));
  }
};

const permanentDeleteTask = async (task: TrashTask) => {
  if (!await confirm({
    title: `確定要永久刪除「${task.name}」？`,
    message: '此操作無法復原，所有附件也會一併刪除。',
    danger: true,
  })) return;
  try {
    await trashService.permanentDeleteTask(task.task_id);
    tasks.value = tasks.value.filter(t => t.task_id !== task.task_id);
  } catch (err) {
    toast.error(getApiErrorMessage(err, '永久刪除失敗'));
  }
};

const restoreTimeline = async (tl: TrashTimeline) => {
  try {
    await trashService.restoreTimeline(tl.id);
    timelines.value = timelines.value.filter(t => t.id !== tl.id);
  } catch (err) {
    toast.error(getApiErrorMessage(err, '還原失敗'));
  }
};

const permanentDeleteTimeline = async (tl: TrashTimeline) => {
  if (!await confirm({
    title: `確定要永久刪除專案「${tl.name}」？`,
    message: '此操作無法復原，專案內所有任務與附件也會一併刪除。',
    danger: true,
  })) return;
  try {
    await trashService.permanentDeleteTimeline(tl.id);
    await loadTrash();
  } catch (err) {
    toast.error(getApiErrorMessage(err, '永久刪除失敗'));
  }
};

const priorityLabel = (p: number) => ({ 1: '高優先', 2: '中優先', 3: '低優先' }[p] || '中優先');
const priorityBadge = (p: number) => ({
  1: 'bg-red-100 text-red-700',
  2: 'bg-amber-100 text-amber-700',
  3: 'bg-emerald-100 text-emerald-700',
}[p] || 'bg-slate-100 text-slate-600');

onMounted(() => {
  void loadTrash();
});
</script>
