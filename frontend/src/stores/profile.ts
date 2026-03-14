import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { ChartStats, Task, Timeline, Profile, ProfileUpdatePayload } from '../types';
import { profileService } from '../services/profileService';
import { taskService } from '../services/taskService';
import { timelineService } from '../services/timelineService';
import { groupService } from '../services/groupService';

type ProfileForm = Pick<Profile, 'name' | 'username' | 'email' | 'phone'>;

interface ProfileStats {
  totalTasks: number;
  completedTasks: number;
  totalProjects: number;
  totalGroups: number;
}

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<ProfileForm>({
    name: '',
    username: null,
    email: '',
    phone: null,
  });

  const stats = ref<ProfileStats>({
    totalTasks: 0,
    completedTasks: 0,
    totalProjects: 0,
    totalGroups: 0,
  });

  const loading = ref(false);
  const ownedTimelines = ref<Timeline[]>([]);
  const chartStats = ref<ChartStats | null>(null);
  const chartLoading = ref(false);

  const statCards = computed(() => [
    { icon: '📝', label: '我的任務', value: stats.value.totalTasks },
    { icon: '✅', label: '已完成任務', value: stats.value.completedTasks },
    { icon: '📊', label: '參與專案', value: stats.value.totalProjects },
    { icon: '👥', label: '加入群組', value: stats.value.totalGroups },
  ]);

  async function fetchProfile(): Promise<void> {
    loading.value = true;
    try {
      const response = await profileService.getMe();
      profile.value = {
        name: response.data.name || '',
        username: response.data.username || null,
        email: response.data.email || '',
        phone: response.data.phone || null,
      };
    } catch (error) {
      console.error('取得個人資料失敗:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateProfile(data: ProfileUpdatePayload): Promise<void> {
    const updateData: ProfileUpdatePayload = {
      name: data.name,
      username: data.username,
      email: data.email,
      phone: data.phone,
    };

    if (data.new_password) {
      updateData.current_password = data.current_password || '';
      updateData.new_password = data.new_password;
    }

    await profileService.update(updateData);
    profile.value = {
      name: data.name || '',
      username: data.username || null,
      email: data.email || '',
      phone: data.phone || null,
    };
  }

  async function fetchStats(): Promise<void> {
    try {
      const [tasksRes, timelinesRes, groupsRes] = await Promise.all([
        taskService.getAll(),
        timelineService.getAll(),
        groupService.getAll(),
      ]);

      const taskList = tasksRes.data as Task[];
      const timelineList = timelinesRes.data as Timeline[];

      stats.value = {
        totalTasks: taskList.length,
        completedTasks: taskList.filter(t => t.completed).length,
        totalProjects: timelineList.length,
        totalGroups: groupsRes.data.length,
      };

      ownedTimelines.value = timelineList.filter(t => t.role === 0);
    } catch (error) {
      console.error('取得統計資料失敗:', error);
    }
  }

  async function fetchChartStats(): Promise<void> {
    chartLoading.value = true;
    try {
      const res = await profileService.getChartStats();
      chartStats.value = res.data;
    } catch (error) {
      console.error('取得圖表資料失敗:', error);
    } finally {
      chartLoading.value = false;
    }
  }

  return {
    profile,
    stats,
    loading,
    ownedTimelines,
    chartStats,
    chartLoading,
    statCards,
    fetchProfile,
    updateProfile,
    fetchStats,
    fetchChartStats,
  };
});
