<template>
  <div class="p-6 max-w-4xl mx-auto">
    <!-- 標題 -->
    <div class="mb-6">
      <h1 class="text-2xl font-bold text-gray-800 flex items-center gap-2">🗑️ 垃圾桶</h1>
      <p class="text-sm text-gray-500 mt-1">已刪除的項目會保留在這裡，可以還原或永久刪除。只有建立者可以操作。</p>
    </div>

    <!-- 載入中 -->
    <div v-if="loading" class="flex justify-center items-center py-20">
      <div class="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>

    <template v-else>
      <!-- 垃圾桶為空 -->
      <div v-if="tasks.length === 0 && timelines.length === 0" class="text-center py-20 text-gray-400">
        <span class="text-6xl block mb-4">🗑️</span>
        <p class="text-lg font-medium">垃圾桶是空的</p>
        <p class="text-sm mt-1">刪除任務或專案後會出現在這裡</p>
      </div>

      <template v-else>
        <!-- 已刪除的專案 -->
        <section v-if="timelines.length > 0" class="mb-8">
          <h2 class="text-base font-semibold text-gray-600 mb-3 flex items-center gap-2">
            <span>📊</span> 已刪除的專案
            <span class="bg-gray-200 text-gray-600 text-xs px-2 py-0.5 rounded-full">{{ timelines.length }}</span>
          </h2>
          <div class="space-y-2">
            <div v-for="tl in timelines" :key="tl.id"
              class="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-300 transition-colors">
              <div class="flex-1 min-w-0">
                <p class="font-medium text-gray-700 truncate">{{ tl.name }}</p>
                <p class="text-xs text-gray-400 mt-0.5">
                  刪除於 {{ formatDate(tl.deleted_at) }}
                  <span v-if="tl.start_date"> · {{ formatDateShort(tl.start_date) }} ~ {{ formatDateShort(tl.end_date) }}</span>
                  <span v-if="!tl.is_owner" class="ml-2 text-orange-400">（非建立者，無法操作）</span>
                </p>
              </div>
              <div v-if="tl.is_owner" class="flex items-center gap-2 shrink-0">
                <button @click="restoreTimeline(tl)"
                  class="px-3 py-1.5 text-sm font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors">
                  ↩ 還原
                </button>
                <button @click="permanentDeleteTimeline(tl)"
                  class="px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors">
                  🗑 永久刪除
                </button>
              </div>
            </div>
          </div>
        </section>

        <!-- 已刪除的任務 -->
        <section v-if="tasks.length > 0">
          <h2 class="text-base font-semibold text-gray-600 mb-3 flex items-center gap-2">
            <span>✅</span> 已刪除的任務
            <span class="bg-gray-200 text-gray-600 text-xs px-2 py-0.5 rounded-full">{{ tasks.length }}</span>
          </h2>
          <div class="space-y-2">
            <div v-for="task in tasks" :key="task.task_id"
              class="flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-300 transition-colors">
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <p class="font-medium text-gray-700 truncate">{{ task.name }}</p>
                  <span :class="priorityBadge(task.priority)" class="text-xs px-2 py-0.5 rounded-full shrink-0">
                    {{ priorityLabel(task.priority) }}
                  </span>
                </div>
                <p class="text-xs text-gray-400 mt-0.5">
                  刪除於 {{ formatDate(task.deleted_at) }}
                  <span v-if="task.end_date"> · 截止 {{ formatDateShort(task.end_date) }}</span>
                  <span v-if="!task.is_owner" class="ml-2 text-orange-400">（非建立者，無法操作）</span>
                </p>
              </div>
              <div v-if="task.is_owner" class="flex items-center gap-2 shrink-0">
                <button @click="restoreTask(task)"
                  class="px-3 py-1.5 text-sm font-medium text-primary bg-primary/10 hover:bg-primary/20 rounded-lg transition-colors">
                  ↩ 還原
                </button>
                <button @click="permanentDeleteTask(task)"
                  class="px-3 py-1.5 text-sm font-medium text-red-600 bg-red-50 hover:bg-red-100 rounded-lg transition-colors">
                  🗑 永久刪除
                </button>
              </div>
            </div>
          </div>
        </section>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { trashService } from '../services/trashService';

const loading = ref(true);
const tasks = ref([]);
const timelines = ref([]);

const loadTrash = async () => {
  loading.value = true;
  try {
    const res = await trashService.getAll();
    tasks.value = res.data.tasks || [];
    timelines.value = res.data.timelines || [];
  } catch (err) {
    alert('無法載入垃圾桶內容');
  } finally {
    loading.value = false;
  }
};

const restoreTask = async (task) => {
  try {
    await trashService.restoreTask(task.task_id);
    tasks.value = tasks.value.filter(t => t.task_id !== task.task_id);
  } catch (err) {
    alert(err.response?.data?.error || '還原失敗');
  }
};

const permanentDeleteTask = async (task) => {
  if (!confirm(`確定要永久刪除「${task.name}」？此操作無法復原，所有附件也會一併刪除。`)) return;
  try {
    await trashService.permanentDeleteTask(task.task_id);
    tasks.value = tasks.value.filter(t => t.task_id !== task.task_id);
  } catch (err) {
    alert(err.response?.data?.error || '永久刪除失敗');
  }
};

const restoreTimeline = async (tl) => {
  try {
    await trashService.restoreTimeline(tl.id);
    timelines.value = timelines.value.filter(t => t.id !== tl.id);
  } catch (err) {
    alert(err.response?.data?.error || '還原失敗');
  }
};

const permanentDeleteTimeline = async (tl) => {
  if (!confirm(`確定要永久刪除專案「${tl.name}」？此操作無法復原，專案內所有任務與附件也會一併刪除。`)) return;
  try {
    await trashService.permanentDeleteTimeline(tl.id);
    // 重新 call API：cascade 同時刪除了底下所有任務，前端無法自行推算哪些要移除
    await loadTrash();
  } catch (err) {
    alert(err.response?.data?.error || '永久刪除失敗');
  }
};

// ── Helpers ──
const formatDate = (str) => {
  if (!str) return '';
  return new Date(str).toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};
const formatDateShort = (str) => {
  if (!str) return '';
  return new Date(str).toLocaleDateString('zh-TW', { month: '2-digit', day: '2-digit' });
};
const priorityLabel = (p) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[p] || '🟡 中');
const priorityBadge = (p) => ({
  1: 'bg-red-100 text-red-700',
  2: 'bg-yellow-100 text-yellow-700',
  3: 'bg-green-100 text-green-700',
}[p] || 'bg-gray-100 text-gray-600');

onMounted(loadTrash);
</script>
