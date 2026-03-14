import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { Timeline, Task, DaysRemainingResult, CreateTimelinePayload, UpdateTimelinePayload } from '../types';
import { timelineService } from '../services/timelineService';
import { taskService } from '../services/taskService';

export const useTimelineStore = defineStore('timelines', () => {
  const timelines = ref<Timeline[]>([]);
  const allTasks = ref<Task[]>([]);
  const loading = ref(false);

  const urgentCount = computed(() =>
    timelines.value.filter(t => {
      const days = getDaysRemaining(t.endDate).days;
      return days !== null && days >= 0 && days <= 7;
    }).length,
  );

  const totalCompletedTasks = computed(() =>
    timelines.value.reduce((sum, t) => sum + (t.completedTasks || 0), 0),
  );

  const totalTasks = computed(() =>
    timelines.value.reduce((sum, t) => sum + (t.totalTasks || 0), 0),
  );

  const sortedTimelines = computed(() =>
    [...timelines.value].sort((a, b) => {
      if (!a.endDate && !b.endDate) return 0;
      if (!a.endDate) return 1;
      if (!b.endDate) return -1;
      return new Date(a.endDate).getTime() - new Date(b.endDate).getTime();
    }),
  );

  function getDaysRemaining(endDate: string | null | undefined): DaysRemainingResult {
    if (!endDate) {
      return { days: null, text: '未設定', display: '未設定', colorClass: 'text-gray-400' };
    }
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const end = new Date(endDate);
    end.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return { days: diffDays, text: `已過期 ${Math.abs(diffDays)} 天`, display: `過期 ${Math.abs(diffDays)} 天`, colorClass: 'text-red-500' };
    }
    if (diffDays === 0) {
      return { days: 0, text: '今天到期', display: '今天到期', colorClass: 'text-red-500' };
    }
    if (diffDays <= 3) {
      return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-orange-500' };
    }
    if (diffDays <= 7) {
      return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-yellow-600' };
    }
    if (diffDays <= 30) {
      return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-blue-500' };
    }
    return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-green-500' };
  }

  async function fetchTimelines(): Promise<void> {
    loading.value = true;
    try {
      const response = await timelineService.getAll();
      timelines.value = response.data;
    } catch (error) {
      console.error('取得專案失敗:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function fetchAllTasks(): Promise<void> {
    try {
      const response = await taskService.getAll();
      allTasks.value = response.data;
    } catch (error) {
      console.error('取得任務失敗:', error);
    }
  }

  async function fetchAll(): Promise<void> {
    await Promise.all([fetchTimelines(), fetchAllTasks()]);
  }

  async function addTimeline(data: CreateTimelinePayload): Promise<void> {
    const formData = {
      name: data.name.trim(),
      start_date: data.start_date ? new Date(data.start_date).toISOString().split('T')[0] : '',
      end_date: data.end_date ? new Date(data.end_date).toISOString().split('T')[0] : '',
      remark: data.remark || '',
    };
    await timelineService.create(formData);
    await fetchTimelines();
  }

  async function updateTimeline(id: number, data: UpdateTimelinePayload): Promise<void> {
    const formData: UpdateTimelinePayload = {};

    if (Object.prototype.hasOwnProperty.call(data, 'name')) {
      formData.name = data.name?.trim();
    }

    if (Object.prototype.hasOwnProperty.call(data, 'start_date')) {
      formData.start_date = data.start_date ? new Date(data.start_date).toISOString().split('T')[0] : '';
    }

    if (Object.prototype.hasOwnProperty.call(data, 'end_date')) {
      formData.end_date = data.end_date ? new Date(data.end_date).toISOString().split('T')[0] : '';
    }

    if (Object.prototype.hasOwnProperty.call(data, 'remark')) {
      formData.remark = data.remark ?? '';
    }

    if (Object.keys(formData).length === 0) {
      return;
    }

    await timelineService.update(id, formData);
    await fetchTimelines();
  }

  async function removeTimeline(id: number): Promise<void> {
    await timelineService.remove(id);
    await fetchTimelines();
  }

  async function getTimelineTasks(timelineId: number): Promise<Task[]> {
    const response = await timelineService.getTasks(timelineId);
    return response.data;
  }

  async function toggleTask(taskId: number): Promise<void> {
    await taskService.toggle(taskId);
    await fetchTimelines();
    await fetchAllTasks();
  }

  async function removeTask(taskId: number): Promise<void> {
    await taskService.remove(taskId);
    await fetchTimelines();
  }

  return {
    timelines,
    allTasks,
    loading,
    urgentCount,
    totalCompletedTasks,
    totalTasks,
    sortedTimelines,
    getDaysRemaining,
    fetchTimelines,
    fetchAllTasks,
    fetchAll,
    addTimeline,
    updateTimeline,
    removeTimeline,
    getTimelineTasks,
    toggleTask,
    removeTask,
  };
});
