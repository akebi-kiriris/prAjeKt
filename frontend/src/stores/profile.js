import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { profileService } from '../services/profileService';
import { taskService } from '../services/taskService';
import { timelineService } from '../services/timelineService';
import { groupService } from '../services/groupService';

export const useProfileStore = defineStore('profile', () => {
  // ────────────── 狀態 ──────────────
  const profile = ref({
    name: '',
    username: '',
    email: '',
    phone: '',
  });
  const stats = ref({
    totalTasks: 0,
    completedTasks: 0,
    totalProjects: 0,
    totalGroups: 0,
  });
  const loading = ref(false);

  // ────────────── Computed ──────────────
  const statCards = computed(() => [
    { icon: '📝', label: '我的任務',   value: stats.value.totalTasks },
    { icon: '✅', label: '已完成任務', value: stats.value.completedTasks },
    { icon: '📊', label: '參與專案',   value: stats.value.totalProjects },
    { icon: '👥', label: '加入群組',   value: stats.value.totalGroups },
  ]);

  // ────────────── 方法 ──────────────
  async function fetchProfile() {
    loading.value = true;
    try {
      const response = await profileService.getMe();
      profile.value = {
        name: response.data.name || '',
        username: response.data.username || '',
        email: response.data.email || '',
        phone: response.data.phone || '',
      };
    } catch (error) {
      console.error('取得個人資料失敗:', error);
      throw error;
    } finally {
      loading.value = false;
    }
  }

  async function updateProfile(data) {
    const updateData = {
      name: data.name,
      username: data.username,
      email: data.email,
      phone: data.phone,
    };
    if (data.new_password) {
      updateData.current_password = data.current_password;
      updateData.new_password = data.new_password;
    }
    await profileService.update(updateData);
    // 更新 store 裡的快取
    profile.value = {
      name: data.name,
      username: data.username,
      email: data.email,
      phone: data.phone,
    };
  }

  async function fetchStats() {
    try {
      const [tasksRes, timelinesRes, groupsRes] = await Promise.all([
        taskService.getAll(),
        timelineService.getAll(),
        groupService.getAll(),
      ]);
      stats.value = {
        totalTasks: tasksRes.data.length,
        completedTasks: tasksRes.data.filter(t => t.completed).length,
        totalProjects: timelinesRes.data.length,
        totalGroups: groupsRes.data.length,
      };
    } catch (error) {
      console.error('取得統計資料失敗:', error);
    }
  }

  return {
    // 狀態
    profile,
    stats,
    loading,
    // Computed
    statCards,
    // 方法
    fetchProfile,
    updateProfile,
    fetchStats,
  };
});
