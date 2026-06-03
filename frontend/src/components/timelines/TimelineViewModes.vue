<template>
  <div>
    <TimelineKanbanBoard
      v-if="viewMode === 'kanban'"
      :timelines="timelines"
      :selected-kanban-timeline="selectedKanbanTimeline"
      :search-query="searchQuery"
      :show-filter-panel="showFilterPanel"
      :has-active-filters="hasActiveFilters"
      :active-filter-count="activeFilterCount"
      :filter-priority="filterPriority"
      :filter-tag="filterTag"
      :pending-tasks="pendingTasks"
      :in-progress-tasks="inProgressTasks"
      :completed-tasks="completedTasks"
      :is-dragging="isDragging"
      :get-priority-badge-class="getPriorityBadgeClass"
      :get-priority-label="getPriorityLabel"
      :get-subtask-progress="getSubtaskProgress"
      :get-completed-subtask-count="getCompletedSubtaskCount"
      :get-task-timeline-name="getTaskTimelineName"
      :format-date-fn="formatDate"
      @update:selected-kanban-timeline="selectedKanbanTimeline = $event"
      @update:search-query="searchQuery = $event"
      @toggle-filter-panel="showFilterPanel = !showFilterPanel"
      @update:filter-priority="filterPriority = $event"
      @update:filter-tag="filterTag = $event"
      @clear-filters="clearFilters"
      @drag-start="isDragging = true"
      @drag-end="isDragging = false"
      @pending-change="onPendingChange($event as DraggableChangeEvent)"
      @in-progress-change="onInProgressChange($event as DraggableChangeEvent)"
      @completed-change="onCompletedChange($event as DraggableChangeEvent)"
      @open-task="viewKanbanTaskDetail"
    />

    <!-- Calendar View -->
    <TimelineCalendarView
      v-if="viewMode === 'calendar'"
      :calendar-options="calendarOptions"
      :this-week-timelines="thisWeekTimelines"
      :overdue-timelines="overdueTimelines"
      :completed-timelines="completedTimelines"
      :get-days-remaining="getDaysRemaining"
      @view-timeline="$emit('view-timeline', $event)"
    />

    <!-- Timeline (List) View -->
    <TimelineListView
      v-if="viewMode === 'timeline'"
      :sorted-timelines="sortedTimelines"
      :timelines-count="timelines.length"
      :get-timeline-status="getTimelineStatus"
      :get-days-remaining="getDaysRemaining"
      :get-progress-bar-color="getProgressBarColor"
      :get-task-progress="getTaskProgress"
      @view-timeline="$emit('view-timeline', $event)"
      @edit-timeline="$emit('edit-timeline', $event)"
      @delete-timeline="$emit('delete-timeline', $event)"
    />

    <TimelineGanttView
      v-if="viewMode === 'gantt'"
      :timelines="props.timelines"
      :selected-gantt-timeline="selectedGanttTimeline"
      :selected-gantt-range="selectedGanttRange"
      :selected-gantt-view-mode="selectedGanttViewMode"
      :gantt-renderable-task-count="ganttRenderableTasks.length"
      :missing-gantt-task-dates="missingGanttTaskDates"
      :set-gantt-container-ref="setGanttContainerRef"
      @update:selected-gantt-timeline="selectedGanttTimeline = $event"
      @update:selected-gantt-range="selectedGanttRange = $event"
      @update:selected-gantt-view-mode="selectedGanttViewMode = $event"
    />

    <!-- Card View -->
    <TimelineCardView
      v-if="viewMode === 'card'"
      :sorted-timelines="sortedTimelines"
      :timelines-count="timelines.length"
      :get-timeline-status="getTimelineStatus"
      :get-days-remaining="getDaysRemaining"
      :get-time-progress="getTimeProgress"
      :get-progress-text-color="getProgressTextColor"
      :get-progress-bar-color="getProgressBarColor"
      :get-task-progress="getTaskProgress"
      @view-timeline="$emit('view-timeline', $event)"
      @edit-timeline="$emit('edit-timeline', $event)"
      @delete-timeline="$emit('delete-timeline', $event)"
      @create-timeline="$emit('create-timeline')"
    />

    <TimelineKanbanTaskModal
      :show="showKanbanTaskModal"
      :task="selectedKanbanTask"
      :new-subtask-name="newSubtaskName"
      :get-subtask-progress="getSubtaskProgress"
      :get-completed-subtask-count="getCompletedSubtaskCount"
      @close="showKanbanTaskModal = false"
      @priority-select="onPrioritySelect"
      @update:tags="selectedKanbanTask && (selectedKanbanTask.tags = $event)"
      @update-tags="updateTaskTags"
      @toggle-subtask="toggleSubtask"
      @delete-subtask="deleteSubtask"
      @update:new-subtask-name="newSubtaskName = $event"
      @add-subtask="addSubtask"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue';
import { toast } from 'vue-sonner';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import multiMonthPlugin from '@fullcalendar/multimonth';
import Gantt from 'frappe-gantt';
import '../../styles/frappe-gantt.css';
import TimelineKanbanBoard from './TimelineKanbanBoard.vue';
import TimelineListView from './TimelineListView.vue';
import TimelineCalendarView from './TimelineCalendarView.vue';
import TimelineCardView from './TimelineCardView.vue';
import TimelineGanttView from './TimelineGanttView.vue';
import TimelineKanbanTaskModal from './TimelineKanbanTaskModal.vue';
import type { CalendarOptions, EventClickArg, EventMountArg, DayCellMountArg } from '@fullcalendar/core';
import { taskService } from '../../services/taskService';
import { formatDate } from '../../utils/formatters';
import { buildGanttPopupHtml } from '../../utils/ganttPopup';
import type { Task, Timeline, Subtask, TaskUpdatePayload, TimelineViewModesProps, DaysRemainingResult } from '../../types';

const props = defineProps<TimelineViewModesProps>();

interface DraggableChangeEvent {
  added?: {
    element: Task;
  };
}

const emit = defineEmits<{
  (e: 'view-timeline', timeline: Timeline): void;
  (e: 'edit-timeline', timeline: Timeline): void;
  (e: 'delete-timeline', timelineId: number): void;
  (e: 'create-timeline'): void;
  (e: 'refresh-all'): void;
}>();

// 看板本地狀態
const selectedKanbanTimeline = ref<number | null>(null);
const searchQuery = ref('');
const showFilterPanel = ref(false);
const filterPriority = ref<number | null>(null);
const filterTag = ref('');
const isDragging = ref(false);
const showKanbanTaskModal = ref(false);
const selectedKanbanTask = ref<Task | null>(null);
const newSubtaskName = ref('');

type TaskStatus = Task['status'];

// 月曆 ref

// ────────────── 篩選 computed ──────────────
const filteredTasks = computed(() => {
  let tasks = props.allTasks;
  if (selectedKanbanTimeline.value) tasks = tasks.filter(t => t.timeline_id === selectedKanbanTimeline.value);
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    tasks = tasks.filter(t => t.name.toLowerCase().includes(q));
  }
  if (filterPriority.value) tasks = tasks.filter(t => t.priority === filterPriority.value);
  if (filterTag.value) {
    const tag = filterTag.value.toLowerCase();
    tasks = tasks.filter(t => t.tags && t.tags.toLowerCase().includes(tag));
  }
  return tasks;
});

const pendingTasksComputed = computed(() => filteredTasks.value.filter(t => t.status === 'pending' && !t.completed));
const inProgressTasksComputed = computed(() => filteredTasks.value.filter(t => t.status === 'in_progress' && !t.completed));
const completedTasksComputed = computed(() => filteredTasks.value.filter(t => t.status === 'completed' || t.completed));

// vuedraggable 需要可變陣列；以本地清單承接，避免直接操作 computed 衍生結果。
const pendingTasks = ref<Task[]>([]);
const inProgressTasks = ref<Task[]>([]);
const completedTasks = ref<Task[]>([]);

const hasActiveFilters = computed<boolean>(() => {
  return filterPriority.value !== null || filterTag.value.trim().length > 0;
});
const activeFilterCount = computed(() => (filterPriority.value ? 1 : 0) + (filterTag.value ? 1 : 0));

const clearFilters = () => { filterPriority.value = null; filterTag.value = ''; };

watch(
  [pendingTasksComputed, inProgressTasksComputed, completedTasksComputed, isDragging],
  () => {
    if (isDragging.value) return;
    pendingTasks.value = [...pendingTasksComputed.value];
    inProgressTasks.value = [...inProgressTasksComputed.value];
    completedTasks.value = [...completedTasksComputed.value];
  },
  { immediate: true }
);

// ────────────── 甘特圖相關 ──────────────
const ganttContainerRef = ref<HTMLElement | null>(null);
const setGanttContainerRef = (el: Element | null) => {
  ganttContainerRef.value = el as HTMLElement | null;
};
const selectedGanttTimeline = ref<string>('all');
const selectedGanttRange = ref<'all' | '90d' | '30d'>('90d');
const selectedGanttViewMode = ref<'Day' | 'Week' | 'Month'>('Week');

type GanttRenderableTask = {
  task_id: number;
  name: string;
  timeline_id: number | null;
  start_date: string;
  end_date: string;
  progress: number;
  depends_on_task_ids: number[];
};

type FrappeTask = {
  id: string;
  name: string;
  full_name: string;
  start: string;
  end: string;
  progress: number;
  dependencies: string;
  custom_class?: string;
};

let ganttInstance: Gantt | null = null;
const ganttSavingTaskIds = new Set<number>();
const ganttSaveTimers = new Map<number, ReturnType<typeof setTimeout>>();
const ganttClickLockedUntil = new Map<number, number>();
const SUPPRESS_CLICK_AFTER_DRAG_MS = 800;

const clearGantt = () => {
  if (ganttContainerRef.value) ganttContainerRef.value.innerHTML = '';
  ganttInstance = null;
};

const parseDateToDay = (raw: string | null | undefined): Date | null => {
  if (!raw) return null;
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  d.setHours(0, 0, 0, 0);
  return d;
};

const dayToIso = (date: Date): string => {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const getDurationDays = (startDate: string, endDate: string): number => {
  const start = parseDateToDay(startDate);
  const end = parseDateToDay(endDate);
  if (!start || !end) return 1;
  return Math.max(1, Math.round((end.getTime() - start.getTime()) / (24 * 60 * 60 * 1000)) + 1);
};

const truncateWithEllipsis = (text: string, maxChars: number): string => {
  if (text.length <= maxChars) return text;
  if (maxChars <= 3) return `${text.slice(0, 1)}...`;
  return `${text.slice(0, maxChars - 3)}...`;
};

const getGanttLabelByView = (name: string, durationDays: number): string => {
  let maxChars = 12;
  if (selectedGanttViewMode.value === 'Day') {
    maxChars = Math.min(34, Math.max(7, Math.floor(durationDays * 1.4)));
  } else if (selectedGanttViewMode.value === 'Week') {
    maxChars = Math.min(18, Math.max(5, Math.floor(durationDays * 0.45)));
  } else {
    maxChars = Math.min(14, Math.max(4, Math.floor(durationDays * 0.25)));
  }

  return truncateWithEllipsis(name, maxChars);
};

const addDaysToDate = (date: Date, days: number): Date => {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
};

const ganttFilteredTasks = computed(() => {
  let tasks = props.allTasks;

  if (selectedGanttTimeline.value !== 'all') {
    const timelineId = Number(selectedGanttTimeline.value);
    tasks = tasks.filter(task => task.timeline_id === timelineId);
  }

  if (selectedGanttRange.value !== 'all') {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const rangeDays = selectedGanttRange.value === '30d' ? 30 : 90;
    const rangeStart = addDaysToDate(today, -rangeDays);
    const rangeEnd = addDaysToDate(today, rangeDays);

    tasks = tasks.filter(task => {
      const start = parseDateToDay(task.start_date);
      const end = parseDateToDay(task.end_date);
      if (!start || !end) return false;
      return end >= rangeStart && start <= rangeEnd;
    });
  }

  return tasks;
});

const ganttRenderableTasks = computed<GanttRenderableTask[]>(() => {
  return ganttFilteredTasks.value
    .map(task => {
      const start = parseDateToDay(task.start_date);
      const end = parseDateToDay(task.end_date);
      if (!start || !end) return null;

      const safeEnd = end < start ? start : end;

      return {
        task_id: task.task_id,
        name: task.name,
        timeline_id: task.timeline_id,
        start_date: dayToIso(start),
        end_date: dayToIso(safeEnd),
        progress: task.completed ? 100 : task.status === 'in_progress' ? 50 : 0,
        depends_on_task_ids: task.depends_on_task_ids || [],
      };
    })
    .filter((task): task is GanttRenderableTask => task !== null)
    .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());
});

const missingGanttTaskDates = computed(() => ganttFilteredTasks.value.length - ganttRenderableTasks.value.length);

const getTimelineNameById = (timelineId: number | null): string => {
  if (!timelineId) return '';
  const timeline = props.timelines.find(t => t.id === timelineId);
  return timeline?.name ?? '';
};

const getTaskStatusLabel = (status: Task['status']): string => {
  if (status === 'completed') return '已完成';
  if (status === 'in_progress') return '進行中';
  if (status === 'review') return '審核中';
  if (status === 'cancelled') return '已取消';
  return '待辦';
};

const buildDependencies = (tasks: GanttRenderableTask[]): Map<number, string> => {
  const renderableTaskIds = new Set(tasks.map((task) => task.task_id));
  const dependencyMap = new Map<number, string>();

  tasks.forEach((task) => {
    const validDependencies = (task.depends_on_task_ids || [])
      .filter((dependencyTaskId) => dependencyTaskId !== task.task_id)
      .filter((dependencyTaskId) => renderableTaskIds.has(dependencyTaskId));

    if (validDependencies.length > 0) {
      dependencyMap.set(task.task_id, validDependencies.join(','));
    }
  });

  return dependencyMap;
};

const GANTT_OWNER_COLOR_CLASS_COUNT = 8;

const getGanttOwnerColorClass = (ownerUserId: number | null): string => {
  if (ownerUserId === null) return 'gantt-owner-unknown';
  return `gantt-owner-${Math.abs(ownerUserId) % GANTT_OWNER_COLOR_CLASS_COUNT}`;
};

const getGanttTaskClass = (task: GanttRenderableTask): string => {
  const source = props.allTasks.find(t => t.task_id === task.task_id);
  const members = source?.members ?? [];
  const owner = members.find(m => m.role === 0);
  const hasCollaborator = members.some(m => m.role === 1);

  const ownerClass = getGanttOwnerColorClass(owner?.user_id ?? null);
  return hasCollaborator ? `${ownerClass}-collab` : ownerClass;
};

const frappeTasks = computed<FrappeTask[]>(() => {
  const dependencyMap = buildDependencies(ganttRenderableTasks.value);
  return ganttRenderableTasks.value.map(task => ({
    id: String(task.task_id),
    name: task.name,
    full_name: task.name,
    start: task.start_date,
    end: task.end_date,
    progress: task.progress,
    dependencies: dependencyMap.get(task.task_id) ?? '',
    custom_class: getGanttTaskClass(task)
  }));
});

const renderGantt = async () => {
  if (props.viewMode !== 'gantt') return;
  if (ganttSavingTaskIds.size > 0) return;
  await nextTick();

  if (!ganttContainerRef.value) return;
  if (!frappeTasks.value.length) {
    ganttContainerRef.value.innerHTML = '';
    return;
  }

  ganttContainerRef.value.innerHTML = '';

  ganttInstance = new Gantt(ganttContainerRef.value, frappeTasks.value, {
    view_mode: selectedGanttViewMode.value,
    language: 'zh',
    today_button: true,
    popup_on: 'hover',
    custom_popup_html: (task) => {
      const hit = props.allTasks.find(t => String(t.task_id) === String(task.id));
      const timelineName = getTimelineNameById(hit?.timeline_id ?? null) || '未分配專案';
      const statusLabel = hit ? getTaskStatusLabel(hit.status) : '待辦';
      const progress = `${Math.round(task.progress ?? 0)}%`;
      const fullName = (task as FrappeTask).full_name || hit?.name || task.name;
      const dependencyNames = (hit?.depends_on_task_ids || [])
        .map((dependencyTaskId) => props.allTasks.find((item) => item.task_id === dependencyTaskId)?.name || `#${dependencyTaskId}`)
        .join('、');
      return buildGanttPopupHtml({
        fullName,
        timelineName,
        statusLabel,
        start: task.start,
        end: task.end,
        progress,
        dependencyNames: dependencyNames || '無',
      });
    },
    on_click: (task) => {
      const taskId = Number(task.id);
      const lockedUntil = ganttClickLockedUntil.get(taskId) ?? 0;
      if (Date.now() < lockedUntil) return;

      const hit = props.allTasks.find(t => String(t.task_id) === String(task.id));
      if (!hit) return;
      const timeline = props.timelines.find(t => t.id === hit.timeline_id);
      if (timeline) emit('view-timeline', timeline);
    },
    on_date_change: async (task, start, end) => {
      const taskId = Number(task.id);
      const startDate = dayToIso(start);
      const endDate = dayToIso(end);

      // Drag release often triggers a synthetic click on the same bar; temporarily ignore it.
      ganttClickLockedUntil.set(taskId, Date.now() + SUPPRESS_CLICK_AFTER_DRAG_MS);

      const prevTimer = ganttSaveTimers.get(taskId);
      if (prevTimer) clearTimeout(prevTimer);

      const timer = setTimeout(async () => {
        ganttSavingTaskIds.add(taskId);
        try {
          await taskService.update(taskId, { start_date: startDate, end_date: endDate });

          const local = props.allTasks.find(t => t.task_id === taskId);
          if (local) {
            local.start_date = startDate;
            local.end_date = endDate;
          }

          emit('refresh-all');
          toast.success('任務時程已更新');
        } catch {
          toast.error('更新任務時程失敗，已重新整理');
          emit('refresh-all');
        } finally {
          ganttSavingTaskIds.delete(taskId);
          ganttSaveTimers.delete(taskId);
          void renderGantt();
        }
      }, 650);

      ganttSaveTimers.set(taskId, timer);
    }
  });
};

watch(
  [() => props.viewMode, frappeTasks, selectedGanttTimeline, selectedGanttRange, selectedGanttViewMode],
  () => {
    void renderGantt();
  },
  { immediate: true }
);

watch(
  () => props.viewMode,
  (viewMode) => {
    // 避免切換視圖後殘留遮罩或拖曳狀態，導致整頁無法點擊
    isDragging.value = false;
    showFilterPanel.value = false;
    showKanbanTaskModal.value = false;
    selectedKanbanTask.value = null;
    newSubtaskName.value = '';
    if (viewMode !== 'gantt') clearGantt();
  }
);

onBeforeUnmount(() => {
  ganttSaveTimers.forEach(timer => clearTimeout(timer));
  ganttSaveTimers.clear();
  ganttSavingTaskIds.clear();
  ganttClickLockedUntil.clear();
  clearGantt();
});

// ────────────── 月曆相關 ──────────────
const thisWeekTimelines = computed(() => props.timelines.filter((t: Timeline) => {
  const days = getDaysRemaining(t.endDate).days;
  return days !== null && days >= 0 && days <= 7;
}));
const overdueTimelines = computed(() => props.timelines.filter((t: Timeline) => {
  const days = getDaysRemaining(t.endDate).days;
  return days !== null && days < 0;
}));
const completedTimelines = computed(() => props.timelines.filter((t: Timeline) => getTaskProgress(t) === 100));

const normalizeDateOnly = (raw: string | null | undefined): string | null => {
  if (!raw) return null;
  return raw.length >= 10 ? raw.slice(0, 10) : raw;
};

const parseDateOnlyLocal = (raw: string | null | undefined): Date | null => {
  const normalized = normalizeDateOnly(raw);
  if (!normalized) return null;
  const [y, m, d] = normalized.split('-').map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
};

const toDateOnlyString = (date: Date): string => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const calendarEvents = computed(() => props.timelines.map((timeline: Timeline) => {
  const status = getTimelineStatus(timeline);
  const progress = getTaskProgress(timeline);
  let backgroundColor, borderColor, textColor;
  if (progress === 100) { backgroundColor = '#22c55e'; borderColor = '#15803d'; textColor = '#ffffff'; }
  else if (status.label === '已過期') { backgroundColor = '#ef4444'; borderColor = '#b91c1c'; textColor = '#ffffff'; }
  else if (status.label === '緊急') { backgroundColor = '#f97316'; borderColor = '#c2410c'; textColor = '#ffffff'; }
  else if (status.label === '即將到期') { backgroundColor = '#fbbf24'; borderColor = '#d97706'; textColor = '#78350f'; }
  else { backgroundColor = '#3b82f6'; borderColor = '#1d4ed8'; textColor = '#ffffff'; }
  return {
    id: String(timeline.id),
    title: `${status.icon} ${timeline.name} (${progress}%)`,
    start: normalizeDateOnly(timeline.startDate) || normalizeDateOnly(timeline.endDate) || undefined,
    end: timeline.endDate ? addDays(timeline.endDate, 1) ?? undefined : undefined,
    backgroundColor, borderColor, textColor,
    extendedProps: { timeline, status: status.label, progress }
  };
}));

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, interactionPlugin, multiMonthPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-tw',
  headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,multiMonthYear' },
  buttonText: { today: '今天', month: '月', year: '年度' },
  height: 'auto',
  events: calendarEvents.value,
  eventClick: (info: EventClickArg) => emit('view-timeline', info.event.extendedProps.timeline as Timeline),
  eventDidMount: (info: EventMountArg) => {
    const el = info.el;
    el.title = `${info.event.title}\n狀態：${info.event.extendedProps.status}\n進度：${info.event.extendedProps.progress}% 完成`;
    el.style.borderRadius = '8px'; el.style.padding = '4px 8px'; el.style.margin = '2px 4px';
    el.style.fontSize = '12px'; el.style.fontWeight = '500'; el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    el.style.border = 'none'; el.style.borderLeft = `4px solid ${info.event.borderColor}`; el.style.transition = 'all 0.2s ease';
    el.addEventListener('mouseenter', () => { el.style.transform = 'translateY(-2px)'; el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'; });
    el.addEventListener('mouseleave', () => { el.style.transform = 'translateY(0)'; el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'; });
  },
  dayCellDidMount: (info: DayCellMountArg) => {
    const today = new Date();
    if (info.date.toDateString() === today.toDateString()) { info.el.style.backgroundColor = 'rgba(59, 130, 246, 0.08)'; info.el.style.borderRadius = '8px'; }
    const day = info.date.getDay();
    if (day === 0 || day === 6) info.el.style.backgroundColor = 'rgba(100, 116, 139, 0.03)';
  },
  eventDisplay: 'block', displayEventTime: false,
  eventClassNames: 'cursor-pointer fc-event-custom',
  dayMaxEvents: 3, moreLinkClick: 'popover'
}));

const addDays = (dateStr: string | null, days: number) => {
  const date = parseDateOnlyLocal(dateStr);
  if (!date) return null;
  date.setDate(date.getDate() + days);
  return toDateOnlyString(date);
};

const getDaysRemaining = (endDate: string | null | undefined): DaysRemainingResult => {
  if (!endDate) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-slate-400' };
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const end = parseDateOnlyLocal(endDate);
  if (!end) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-slate-400' };
  end.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { days: diffDays, text: `已過期 ${Math.abs(diffDays)} 天`, display: `過期 ${Math.abs(diffDays)} 天`, colorClass: 'text-red-500' };
  if (diffDays === 0) return { days: 0, text: '今天到期', display: '今天到期', colorClass: 'text-red-500' };
  if (diffDays === 1) return { days: 1, text: '明天到期', display: '剩 1 天', colorClass: 'text-orange-500' };
  if (diffDays <= 3) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-orange-500' };
  if (diffDays <= 7) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-yellow-600' };
  if (diffDays <= 30) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-blue-500' };
  return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-green-500' };
};

const getTaskProgress = (timeline: Timeline): number => {
  if (!timeline.totalTasks || timeline.totalTasks === 0) return 0;
  return Math.round((timeline.completedTasks || 0) / timeline.totalTasks * 100);
};

const getTimeProgress = (timeline: Timeline): number => {
  if (!timeline.startDate || !timeline.endDate) return 0;
  const start = parseDateOnlyLocal(timeline.startDate);
  const end = parseDateOnlyLocal(timeline.endDate);
  if (!start || !end) return 0;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (today < start) return 0;
  if (today > end) return 100;

  const totalDuration = end.getTime() - start.getTime();
  if (totalDuration <= 0) {
    return today.getTime() >= end.getTime() ? 100 : 0;
  }

  const elapsed = today.getTime() - start.getTime();
  const progress = Math.round((elapsed / totalDuration) * 100);
  return Math.min(100, Math.max(0, progress));
};

const getTimelineStatus = (timeline: Timeline) => {
  const { days } = getDaysRemaining(timeline.endDate);
  const progress = getTaskProgress(timeline);
  if (progress === 100) return { label: '已完成', icon: '✅', bgClass: 'bg-green-100', textClass: 'text-green-600', badgeClass: 'bg-green-100 text-green-700', borderClass: 'border-green-200', barClass: 'bg-gradient-to-r from-green-400 to-green-500' };
  if (days === null) return { label: '進行中', icon: '📋', bgClass: 'bg-slate-100', textClass: 'text-slate-600', badgeClass: 'bg-slate-100 text-slate-600', borderClass: 'border-slate-200', barClass: 'bg-gradient-to-r from-slate-300 to-slate-400' };
  if (days < 0) return { label: '已過期', icon: '⚠️', bgClass: 'bg-red-100', textClass: 'text-red-600', badgeClass: 'bg-red-100 text-red-700', borderClass: 'border-red-200', barClass: 'bg-gradient-to-r from-red-400 to-red-500' };
  if (days <= 3) return { label: '緊急', icon: '🔥', bgClass: 'bg-orange-100', textClass: 'text-orange-600', badgeClass: 'bg-orange-100 text-orange-700', borderClass: 'border-orange-200', barClass: 'bg-gradient-to-r from-orange-400 to-orange-500' };
  if (days <= 7) return { label: '即將到期', icon: '⏰', bgClass: 'bg-yellow-100', textClass: 'text-yellow-600', badgeClass: 'bg-yellow-100 text-yellow-700', borderClass: 'border-yellow-200', barClass: 'bg-gradient-to-r from-yellow-400 to-yellow-500' };
  return { label: '進行中', icon: '📋', bgClass: 'bg-blue-100', textClass: 'text-blue-600', badgeClass: 'bg-blue-100 text-blue-700', borderClass: 'border-blue-200', barClass: 'bg-gradient-to-r from-blue-400 to-blue-500' };
};

const getProgressBarColor = (timeline: Timeline) => {
  const progress = getTaskProgress(timeline), status = getTimelineStatus(timeline);
  if (progress === 100) return 'bg-gradient-to-r from-green-400 to-green-500';
  if (status.label === '已過期') return 'bg-gradient-to-r from-red-400 to-red-500';
  if (status.label === '緊急') return 'bg-gradient-to-r from-orange-400 to-orange-500';
  return 'bg-gradient-to-r from-primary to-primary-light';
};

const getProgressTextColor = (timeline: Timeline) => {
  const progress = getTaskProgress(timeline);
  if (progress === 100) return 'text-green-600';
  if (progress >= 50) return 'text-blue-600';
  return 'text-slate-600';
};

const getPriorityLabel = (priority: number) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中');

const getPriorityBadgeClass = (priority: number) => ({
  1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
  2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
  3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
}[priority] || 'bg-slate-100 text-slate-700 border border-slate-200');

const getSubtaskProgress = (task: Task): number => {
  if (!task.subtasks || task.subtasks.length === 0) return 0;
  return Math.round((task.subtasks.filter((s: Subtask) => s.completed).length / task.subtasks.length) * 100);
};

const getCompletedSubtaskCount = (task: Task): number => {
  if (!task?.subtasks?.length) return 0;
  return task.subtasks.filter((s: Subtask) => s.completed).length;
};

const getTaskTimelineName = (task: Task): string => {
  if (!task.timeline_id) return '';
  const tl = props.timelines.find((t: Timeline) => t.id === task.timeline_id);
  return tl ? tl.name : '';
};

// ────────────── 看板操作 ──────────────
const onTaskMoved = async (evt: DraggableChangeEvent, newStatus: TaskStatus) => {
  if (!evt.added) return;
  const task = evt.added.element;
  try {
    await taskService.updateStatus(task.task_id, newStatus);
    const local = props.allTasks.find((t: Task) => t.task_id === task.task_id);
    if (local) { local.status = newStatus; local.completed = newStatus === 'completed'; }
  } catch {
    toast.error('更新狀態失敗');
    emit('refresh-all');
  }
};

const onPendingChange = (evt: DraggableChangeEvent) => {
  void onTaskMoved(evt, 'pending');
};

const onInProgressChange = (evt: DraggableChangeEvent) => {
  void onTaskMoved(evt, 'in_progress');
};

const onCompletedChange = (evt: DraggableChangeEvent) => {
  void onTaskMoved(evt, 'completed');
};

const viewKanbanTaskDetail = async (task: Task) => {
  selectedKanbanTask.value = { ...task };
  try {
    const res = await taskService.getSubtasks(task.task_id);
    selectedKanbanTask.value.subtasks = res.data;
  } catch {
    selectedKanbanTask.value.subtasks = [];
  }
  showKanbanTaskModal.value = true;
};

const addSubtask = async () => {
  if (!newSubtaskName.value.trim() || !selectedKanbanTask.value) return;
  try {
    const res = await taskService.createSubtask(selectedKanbanTask.value.task_id, { name: newSubtaskName.value.trim() });
    selectedKanbanTask.value.subtasks.push(res.data);
    newSubtaskName.value = '';
    emit('refresh-all');
  } catch { toast.error('新增子任務失敗'); }
};

const toggleSubtask = async (subtask: Subtask) => {
  if (!selectedKanbanTask.value) return;
  try {
    await taskService.toggleSubtask(selectedKanbanTask.value.task_id, subtask.id);
    subtask.completed = !subtask.completed;
    emit('refresh-all');
  } catch { toast.error('更新子任務失敗'); }
};

const deleteSubtask = async (subtask: Subtask) => {
  if (!selectedKanbanTask.value) return;
  try {
    await taskService.deleteSubtask(selectedKanbanTask.value.task_id, subtask.id);
    selectedKanbanTask.value.subtasks = selectedKanbanTask.value.subtasks.filter((s: Subtask) => s.id !== subtask.id);
    emit('refresh-all');
  } catch { toast.error('刪除子任務失敗'); }
};

const onPrioritySelect = (event: Event) => {
  const target = event.target as HTMLSelectElement | null;
  const priority = Number(target?.value);
  void updateTaskPriority(priority);
};

const updateTaskPriority = async (priority: number) => {
  if (!selectedKanbanTask.value) return;
  try {
    const payload: TaskUpdatePayload = { priority };
    await taskService.update(selectedKanbanTask.value.task_id, payload);
    selectedKanbanTask.value.priority = priority;
    emit('refresh-all');
  } catch { toast.error('更新優先級失敗'); }
};

const updateTaskTags = async () => {
  if (!selectedKanbanTask.value) return;
  try {
    const payload: TaskUpdatePayload = { tags: selectedKanbanTask.value.tags };
    await taskService.update(selectedKanbanTask.value.task_id, payload);
    emit('refresh-all');
  } catch { toast.error('更新標籤失敗'); }
};
</script>

<style>
.frappe-gantt-container .gantt .bar-label.big {
  display: none;
}

.frappe-gantt-container .popup-wrapper {
  max-width: 360px;
}

.frappe-gantt-container .popup-wrapper .details-container h5 {
  margin: 0 0 6px;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  word-break: break-word;
  line-height: 1.3;
}

.frappe-gantt-container .popup-wrapper .details-container p {
  margin: 2px 0;
  white-space: normal;
  word-break: break-word;
}

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-unknown'] .bar { fill: #94a3b8; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-unknown'] .bar-progress { fill: #64748b; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-0'] .bar { fill: #3b82f6; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-0'] .bar-progress { fill: #1d4ed8; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-1'] .bar { fill: #10b981; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-1'] .bar-progress { fill: #047857; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-2'] .bar { fill: #f59e0b; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-2'] .bar-progress { fill: #b45309; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-3'] .bar { fill: #ef4444; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-3'] .bar-progress { fill: #b91c1c; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-4'] .bar { fill: #8b5cf6; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-4'] .bar-progress { fill: #6d28d9; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-5'] .bar { fill: #06b6d4; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-5'] .bar-progress { fill: #0e7490; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-6'] .bar { fill: #f97316; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-6'] .bar-progress { fill: #c2410c; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-7'] .bar { fill: #84cc16; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-7'] .bar-progress { fill: #3f6212; }

.frappe-gantt-container .bar-wrapper[class*='-collab'] .bar {
  stroke: #0f172a;
  stroke-width: 1.3;
  stroke-dasharray: 4 2;
}
</style>
