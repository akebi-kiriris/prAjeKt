<template>
  <div class="h-full w-full bg-linear-to-br from-slate-50 to-blue-50/30 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-7xl mx-auto">

      <!-- Header + Stats + View Toggle -->
      <TimelineHeader
        :todayFormatted="todayFormatted"
        :timelines="timelines"
        :urgentCount="urgentCount"
        :totalCompletedTasks="totalCompletedTasks"
        :totalTasks="totalTasks"
        :viewMode="viewMode"
        @update:viewMode="viewMode = $event"
        @create-timeline="showCreateModal = true"
      />

      <!-- 四種視圖模式 + 看板任務詳情 Modal -->
      <TimelineViewModes
        :viewMode="viewMode"
        :timelines="timelines"
        :sortedTimelines="sortedTimelines"
        :allTasks="allTasks"
        @view-timeline="viewTimeline"
        @edit-timeline="editTimeline"
        @delete-timeline="deleteTimeline"
        @create-timeline="showCreateModal = true"
        @refresh-all="onRefreshAll"
      />

    </div>

    <!-- 新增 / 編輯專案 Modal（全域，覆蓋在最上層） -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent">
          <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📁</span>
            {{ editingTimeline ? '編輯專案' : '新增專案' }}
          </h2>
          <button @click="closeModal" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <form @submit.prevent="handleSubmit" class="p-5 space-y-5">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">專案名稱 *</label>
            <input
              v-model.lazy="timelineForm.name"
              type="text"
              placeholder="例如：Q1 產品開發計畫"
              class="w-full px-4 py-3 text-base border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all bg-gray-50/50"
              required
            />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">開始日期</label>
              <input v-model.lazy="timelineForm.start_date" type="date" class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all bg-gray-50/50" />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">結束日期</label>
              <input v-model.lazy="timelineForm.end_date" type="date" class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all bg-gray-50/50" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">專案備註</label>
            <textarea
              v-model.lazy="timelineForm.remark"
              rows="3"
              placeholder="描述專案目標、重要里程碑..."
              class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none bg-gray-50/50"
            ></textarea>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="submit" class="flex-1 py-3 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2">
              <span>✓</span>
              {{ editingTimeline ? '更新專案' : '建立專案' }}
            </button>
            <button type="button" @click="closeModal" class="flex-1 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-all">取消</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 專案詳情 + 任務相關所有 Modal -->
    <TimelineDetailDialog
      v-if="selectedTimeline"
      :selectedTimeline="selectedTimeline"
      :timelineTasks="timelineTasks"
      :apiBaseUrl="apiBaseUrl"
      @close="selectedTimeline = null"
      @toggle-task="onToggleTask"
      @delete-task="onDeleteTask"
      @refresh-all="onRefreshAll"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { taskService } from '../services/taskService';
import { timelineService } from '../services/timelineService';
import TimelineHeader from '../components/timelines/TimelineHeader.vue';
import TimelineViewModes from '../components/timelines/TimelineViewModes.vue';
import TimelineDetailDialog from '../components/timelines/TimelineDetailDialog.vue';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// ────────────── 核心狀態 ──────────────
const timelines = ref([]);
const selectedTimeline = ref(null);
const timelineTasks = ref([]);
const allTasks = ref([]);
const viewMode = ref('card');

// Create/Edit Modal 狀態
const showCreateModal = ref(false);
const editingTimeline = ref(null);
const timelineForm = ref({ name: '', start_date: '', end_date: '', remark: '' });

// ────────────── Computed ──────────────
const todayFormatted = computed(() => {
  const today = new Date();
  return today.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' });
});

const urgentCount = computed(() =>
  timelines.value.filter(t => {
    const days = getDaysRemaining(t.endDate).days;
    return days !== null && days >= 0 && days <= 7;
  }).length
);

const totalCompletedTasks = computed(() =>
  timelines.value.reduce((sum, t) => sum + (t.completedTasks || 0), 0)
);

const totalTasks = computed(() =>
  timelines.value.reduce((sum, t) => sum + (t.totalTasks || 0), 0)
);

const sortedTimelines = computed(() =>
  [...timelines.value].sort((a, b) => {
    if (!a.endDate && !b.endDate) return 0;
    if (!a.endDate) return 1;
    if (!b.endDate) return -1;
    return new Date(a.endDate) - new Date(b.endDate);
  })
);

// ────────────── 工具函式 ──────────────
const getDaysRemaining = (endDate) => {
  if (!endDate) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-gray-400' };
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const end = new Date(endDate); end.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { days: diffDays, text: `已過期 ${Math.abs(diffDays)} 天`, display: `過期 ${Math.abs(diffDays)} 天`, colorClass: 'text-red-500' };
  if (diffDays === 0) return { days: 0, text: '今天到期', display: '今天到期', colorClass: 'text-red-500' };
  if (diffDays <= 3) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-orange-500' };
  if (diffDays <= 7) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-yellow-600' };
  if (diffDays <= 30) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-blue-500' };
  return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-green-500' };
};

// ────────────── 資料取得 ──────────────
const fetchTimelines = async () => {
  try {
    const response = await timelineService.getAll();
    timelines.value = response.data;
  } catch (error) {
    console.error('取得專案失敗:', error);
    alert('取得專案失敗');
  }
};

const fetchAllTasks = async () => {
  try {
    const response = await taskService.getAll();
    allTasks.value = response.data;
  } catch (error) {
    console.error('取得任務失敗:', error);
  }
};

// ────────────── 專案 CRUD ──────────────
const viewTimeline = async (timeline) => {
  selectedTimeline.value = timeline;
  try {
    const response = await timelineService.getTasks(timeline.id);
    timelineTasks.value = response.data;
  } catch (error) {
    console.error('取得任務失敗:', error);
  }
};

const editTimeline = (timeline) => {
  editingTimeline.value = timeline;
  timelineForm.value = {
    name: timeline.name,
    start_date: timeline.startDate || '',
    end_date: timeline.endDate || '',
    remark: timeline.remark || ''
  };
  showCreateModal.value = true;
};

const deleteTimeline = async (id) => {
  if (!confirm('確定要刪除此專案？相關任務也會被刪除！')) return;
  try {
    await timelineService.remove(id);
    alert('專案刪除成功');
    await fetchTimelines();
  } catch (error) {
    alert(error.response?.data?.error || '刪除失敗');
  }
};

const handleSubmit = async () => {
  if (!timelineForm.value.name?.trim()) { alert('請輸入專案名稱'); return; }
  try {
    const formData = {
      name: timelineForm.value.name.trim(),
      start_date: timelineForm.value.start_date ? new Date(timelineForm.value.start_date).toISOString().split('T')[0] : '',
      end_date: timelineForm.value.end_date ? new Date(timelineForm.value.end_date).toISOString().split('T')[0] : '',
      remark: timelineForm.value.remark || ''
    };
    if (editingTimeline.value) {
      await timelineService.update(editingTimeline.value.id, formData);
      alert('專案更新成功');
    } else {
      await timelineService.create(formData);
      alert('專案新增成功');
    }
    await fetchTimelines();
    closeModal();
  } catch (error) {
    alert(error.response?.data?.error || '操作失敗');
  }
};

const closeModal = () => {
  showCreateModal.value = false;
  editingTimeline.value = null;
  timelineForm.value = { name: '', start_date: '', end_date: '', remark: '' };
};

// ────────────── 任務操作（來自 DetailDialog emit） ──────────────
const onToggleTask = async (taskId) => {
  try {
    await taskService.toggle(taskId);
    await viewTimeline(selectedTimeline.value);
    await fetchTimelines();
    await fetchAllTasks();
  } catch {
    alert('更新任務狀態失敗');
  }
};

const onDeleteTask = async (taskId) => {
  if (!confirm('確定要刪除此任務？')) return;
  try {
    await taskService.remove(taskId);
    alert('任務刪除成功');
    await viewTimeline(selectedTimeline.value);
    await fetchTimelines();
  } catch (error) {
    alert(error.response?.data?.error || '刪除任務失敗');
  }
};

// ────────────── 子元件請求全域重整 ──────────────
const onRefreshAll = async () => {
  await fetchTimelines();
  await fetchAllTasks();
  if (selectedTimeline.value) await viewTimeline(selectedTimeline.value);
};

onMounted(() => {
  fetchTimelines();
  fetchAllTasks();
});
</script>

<style>
/* FullCalendar 自訂樣式（供 TimelineViewModes 內的 FullCalendar 使用） */
.fc-custom {
  --fc-border-color: #e2e8f0;
  --fc-button-bg-color: #f8fafc;
  --fc-button-border-color: #e2e8f0;
  --fc-button-text-color: #475569;
  --fc-button-hover-bg-color: #f1f5f9;
  --fc-button-hover-border-color: #cbd5e1;
  --fc-button-active-bg-color: var(--color-primary);
  --fc-button-active-border-color: var(--color-primary);
  --fc-today-bg-color: rgba(59, 130, 246, 0.06);
  font-family: inherit;
}
.fc-custom .fc-toolbar { padding: 1rem 0; gap: 1rem; }
.fc-custom .fc-toolbar-title { font-size: 1.5rem; font-weight: 700; color: #1e293b; letter-spacing: -0.025em; }
.fc-custom .fc-button { padding: 0.625rem 1.25rem; font-size: 0.875rem; font-weight: 600; border-radius: 0.75rem; transition: all 0.2s ease; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
.fc-custom .fc-button:hover { transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
.fc-custom .fc-button:focus { box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3); outline: none; }
.fc-custom .fc-button-active { background: linear-gradient(135deg, var(--color-primary) 0%, #2563eb 100%) !important; border-color: transparent !important; color: white !important; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important; }
.fc-custom .fc-daygrid-day-number { padding: 0.625rem; font-size: 0.875rem; font-weight: 500; color: #475569; }
.fc-custom .fc-daygrid-day.fc-day-today { background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.05) 100%) !important; }
.fc-custom .fc-daygrid-day.fc-day-today .fc-daygrid-day-number { background: linear-gradient(135deg, var(--color-primary) 0%, #6366f1 100%); color: white; border-radius: 50%; width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center; font-weight: 700; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3); }
.fc-custom .fc-event { padding: 0.375rem 0.625rem; border-radius: 0.5rem; font-size: 0.8125rem; font-weight: 600; border: none; margin: 2px 4px 4px 4px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); cursor: pointer; transition: all 0.2s ease; }
.fc-custom .fc-event:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
.fc-custom .fc-event-main { padding: 0; }
.fc-custom .fc-daygrid-event-dot { display: none; }
.fc-custom .fc-col-header-cell { padding: 1rem 0; background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); font-weight: 700; color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 2px solid #e2e8f0; }
.fc-custom .fc-scrollgrid { border-radius: 1rem; overflow: hidden; border: 1px solid #e2e8f0; }
.fc-custom .fc-daygrid-day-frame { min-height: 110px; padding: 4px; }
.fc-custom .fc-more-link { color: var(--color-primary); font-weight: 600; padding: 4px 8px; border-radius: 4px; background: rgba(59, 130, 246, 0.1); margin: 2px 4px; transition: all 0.2s; }
.fc-custom .fc-more-link:hover { background: rgba(59, 130, 246, 0.2); }
.fc-custom .fc-multimonth { border: none; }
.fc-custom .fc-multimonth-month { border: 1px solid #e2e8f0; border-radius: 1rem; margin: 0.75rem; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.fc-custom .fc-multimonth-header { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); padding: 0.75rem; }
.fc-custom .fc-multimonth-title { font-weight: 700; color: #334155; }
.fc-custom .fc-popover { border-radius: 0.75rem; box-shadow: 0 10px 40px rgba(0,0,0,0.15); border: 1px solid #e2e8f0; overflow: hidden; }
.fc-custom .fc-popover-header { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); padding: 0.75rem 1rem; font-weight: 600; }

/* ========== 看板拖拽樣式 ========== */
.kanban-ghost { opacity: 0.5; background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%) !important; border: 2px dashed #3b82f6 !important; border-radius: 0.75rem; }
.kanban-drag { transform: rotate(3deg); box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important; z-index: 1000; }
.kanban-card { transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); }
.kanban-card:hover { border-color: #3b82f6 !important; }
.sortable-chosen { cursor: grabbing !important; }
@keyframes slideIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
.kanban-card { animation: slideIn 0.3s ease-out; }
</style>
