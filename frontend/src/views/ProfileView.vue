<template>
  <div class="h-full w-full bg-gray-50 px-6 pt-6 pb-24 md:pb-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-4xl md:text-6xl mb-4 block animate-pulse-custom">👤</span>
      <h1 class="text-2xl md:text-4xl font-bold mb-2 text-gray-800">個人資料</h1>
      <p class="text-lg text-gray-600">管理您的個人資訊與設定</p>
    </div>
    
    <!-- Profile Container -->
    <div class="pb-8">
      <!-- Loading -->
      <div v-if="loading" class="bg-white rounded-2xl shadow-xl p-12 text-center animate-fadeIn">
        <span class="text-4xl block mb-4 animate-spin">⏳</span>
        <p class="text-gray-600">載入中...</p>
      </div>
      
      <!-- Profile Card -->
      <div v-else class="bg-white rounded-2xl shadow-xl overflow-hidden mb-8 animate-slideUp">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>👤</span>
            基本資料
          </h2>
          <button 
            v-if="!isEditing"
            @click="isEditing = true"
            class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors flex items-center gap-2"
          >
            <span>✏️</span>
            編輯資料
          </button>
        </div>
        
        <div class="p-6">
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">姓名 *</label>
                <div>
                  <input 
                    v-model="profileForm.name" 
                    type="text" 
                    :disabled="!isEditing"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">用戶名（選填）</label>
                <div>
                  <input 
                    v-model="profileForm.username" 
                    type="text" 
                    :disabled="!isEditing"
                    placeholder="如：john_doe"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">電子郵件 *</label>
                <div>
                  <input 
                    v-model="profileForm.email" 
                    type="email" 
                    :disabled="!isEditing"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">電話</label>
                <div>
                  <input 
                    v-model="profileForm.phone" 
                    type="tel" 
                    :disabled="!isEditing"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
            
            <!-- Password Section -->
            <template v-if="isEditing">
              <div class="flex items-center gap-2 my-6">
                <div class="flex-1 h-px bg-gray-200"></div>
                <span class="px-4 text-gray-400 text-sm flex items-center gap-2">
                  <span>🔒</span>
                  變更密碼（選填）
                </span>
                <div class="flex-1 h-px bg-gray-200"></div>
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">目前密碼</label>
                <input 
                  v-model="profileForm.current_password" 
                  type="password" 
                  placeholder="如要變更密碼，請輸入目前密碼"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                />
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-semibold text-gray-600 mb-2">新密碼</label>
                  <input 
                    v-model="profileForm.new_password" 
                    type="password" 
                    placeholder="請輸入新密碼"
                    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-semibold text-gray-600 mb-2">確認新密碼</label>
                  <input 
                    v-model="profileForm.confirm_password" 
                    type="password" 
                    placeholder="再次輸入新密碼"
                    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  />
                </div>
              </div>
            </template>
            
            <div v-if="isEditing" class="flex gap-3 pt-4">
              <button 
                type="submit"
                class="px-6 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center gap-2"
                style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
              >
                <span>✓</span>
                儲存變更
              </button>
              <button 
                type="button"
                @click="cancelEdit"
                class="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all flex items-center gap-2"
              >
                <span>✕</span>
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
      
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="stat in statCards" 
          :key="stat.label"
          class="bg-white rounded-xl shadow-md hover:-translate-y-1 hover:shadow-xl transition-all animate-fadeIn p-6"
        >
          <div class="flex items-center gap-4">
            <span class="text-3xl animate-bounce-custom">{{ stat.icon }}</span>
            <div>
              <h4 class="text-sm text-gray-500 font-medium">{{ stat.label }}</h4>
              <p class="text-2xl font-bold gradient-text">{{ stat.value }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Level 1: 個人數據分析 ── -->
      <div v-if="chartLoading" class="mt-8 flex justify-center py-8">
        <span class="text-2xl animate-spin">⏳</span>
      </div>
      <div v-else-if="chartStats" class="mt-8 space-y-6">
        <h3 class="text-lg font-semibold text-gray-700 flex items-center gap-2">
          <span>📊</span> 個人數據分析
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-white rounded-xl shadow-md p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">近 30 天完成趨勢</h4>
            <v-chart :option="trendOption" autoresize style="height:220px" />
          </div>
          <div class="bg-white rounded-xl shadow-md p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-3">任務狀態分布</h4>
            <v-chart :option="statusPieOption" autoresize style="height:220px" />
          </div>
        </div>
        <div v-if="chartStats.tasks_by_project.length > 0" class="bg-white rounded-xl shadow-md p-4">
          <h4 class="text-sm font-semibold text-gray-600 mb-3">各專案任務量</h4>
          <v-chart
            :option="projectBarOption"
            autoresize
            :style="`height:${Math.max(160, chartStats.tasks_by_project.length * 36 + 60)}px`"
          />
        </div>
      </div>

      <!-- ── Level 2: 專案數據分析（負責人） ── -->
      <div v-if="ownedTimelines.length > 0" class="mt-8 space-y-4 mb-8">
        <h3 class="text-lg font-semibold text-gray-700 flex items-center gap-2">
          <span>🏗️</span> 專案數據分析
          <span class="text-xs font-normal text-gray-400 ml-1">（僅負責人可見）</span>
        </h3>
        <div class="flex items-center gap-3 flex-wrap">
          <label class="text-sm text-gray-600 whitespace-nowrap">選擇專案：</label>
          <select
            v-model="selectedTimelineId"
            @change="loadProjectStats"
            class="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
          >
            <option v-for="tl in ownedTimelines" :key="tl.id" :value="tl.id">{{ tl.name }}</option>
          </select>
          <span v-if="loadingProjectStats" class="animate-spin text-lg">⏳</span>
        </div>
        <div v-if="projectStats" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="bg-white rounded-xl shadow-md p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-10">成員任務貢獻</h4>
            <v-chart
              :option="memberBarOption"
              autoresize
              :style="`height:${Math.max(160, projectStats.members.length * 44 + 60)}px`"
            />
          </div>
          <div class="bg-white rounded-xl shadow-md p-4">
            <h4 class="text-sm font-semibold text-gray-600 mb-1">專案任務狀態</h4>
            <p class="text-xs text-gray-400 mb-2">共 {{ projectStats.total_tasks }} 筆任務</p>
            <v-chart :option="projectStatusOption" autoresize style="height:220px" />
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import type { AxiosError } from 'axios';
import type { Ref } from 'vue';
import { toast } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '../stores/profile';
import { useAuthStore } from '../stores/auth';
import VChart from 'vue-echarts';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { LineChart, BarChart, PieChart } from 'echarts/charts';
import { GridComponent, TooltipComponent, LegendComponent } from 'echarts/components';
import { timelineService } from '../services/timelineService';
import type {
  ApiErrorPayload,
  ChartStats,
  ProfileForm,
  ProfileUpdatePayload,
  ProjectStats,
  Timeline,
} from '../types';

use([CanvasRenderer, LineChart, BarChart, PieChart, GridComponent, TooltipComponent, LegendComponent]);

const profileStore = useProfileStore();
const authStore = useAuthStore();

type StatusKey = 'pending' | 'in_progress' | 'review' | 'completed' | 'cancelled';

// ────────────── Store 狀態（響應式解構）──────────────
const {
  profile,
  loading,
  statCards,
  chartStats: rawChartStats,
  chartLoading,
  ownedTimelines,
} = storeToRefs(profileStore);

const chartStats = rawChartStats as unknown as Ref<ChartStats | null>;

// ────────────── View-local UI 狀態 ──────────────
const isEditing = ref(false);
const profileForm = ref<ProfileForm>({
  name: '',
  username: '',
  email: '',
  phone: '',
  current_password: '',
  new_password: '',
  confirm_password: ''
});
const originalProfile = ref<ProfileForm>({ ...profileForm.value });
// ────────────── 初始化表單（從 store profile 同步）──────────────
const syncFormFromStore = () => {
  profileForm.value = {
    name: profile.value.name || '',
    username: profile.value.username || '',
    email: profile.value.email || '',
    phone: profile.value.phone || '',
    current_password: '',
    new_password: '',
    confirm_password: ''
  };
  originalProfile.value = { ...profileForm.value };
};

// ────────────── CRUD ──────────────
const handleSubmit = async () => {
  if (profileForm.value.new_password) {
    if (!profileForm.value.current_password) { toast.warning('請輸入目前密碼'); return; }
    if (profileForm.value.new_password !== profileForm.value.confirm_password) { toast.warning('新密碼與確認密碼不一致'); return; }
    if (profileForm.value.new_password.length < 6) { toast.warning('新密碼至少需要 6 個字元'); return; }
  }

  try {
    const updateData: ProfileUpdatePayload = {
      name: profileForm.value.name,
      username: profileForm.value.username,
      email: profileForm.value.email,
      phone: profileForm.value.phone
    };
    if (profileForm.value.new_password) {
      updateData.current_password = profileForm.value.current_password;
      updateData.new_password = profileForm.value.new_password;
    }
    await profileStore.updateProfile(updateData);
    await authStore.fetchCurrentUser();
    toast.success('個人資料更新成功');
    isEditing.value = false;
    profileForm.value.current_password = '';
    profileForm.value.new_password = '';
    profileForm.value.confirm_password = '';
    originalProfile.value = { ...profileForm.value };
  } catch (error) {
    const message = (error as AxiosError<ApiErrorPayload>).response?.data?.error;
    toast.error(message || '更新失敗');
  }
};

const cancelEdit = () => {
  profileForm.value = { ...originalProfile.value };
  profileForm.value.current_password = '';
  profileForm.value.new_password = '';
  profileForm.value.confirm_password = '';
  isEditing.value = false;
};

// ──────────────── ECharts 輔助常量 ────────────────
const STATUS_LABELS = {
  pending: '待辦', in_progress: '進行中', review: '審核中',
  completed: '已完成', cancelled: '已取消',
} as const;
const STATUS_COLORS = {
  pending: '#6366f1', in_progress: '#f59e0b', review: '#3b82f6',
  completed: '#10b981', cancelled: '#9ca3af',
} as const;

// ──────────────── Level 1：個人圖表 Options ────────────────
const trendOption = computed(() => {
  if (!chartStats.value) return {};
  const data = chartStats.value.daily_completions;
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: 40, right: 16, top: 16, bottom: 36 },
    xAxis: {
      type: 'category',
      data: data.map(d => d.date.slice(5)),
      axisLabel: { fontSize: 10, interval: 5 },
    },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { fontSize: 10 } },
    series: [{
      data: data.map(d => d.count),
      type: 'line',
      smooth: true,
      itemStyle: { color: '#6366f1' },
      areaStyle: { color: 'rgba(99,102,241,0.1)' },
    }],
  };
});

const statusPieOption = computed(() => {
  if (!chartStats.value) return {};
  const dist = chartStats.value.status_distribution;
  const pieData = Object.entries(dist)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => {
      const key = k as StatusKey;
      return {
        name: STATUS_LABELS[key] || key,
        value: v,
        itemStyle: { color: STATUS_COLORS[key] },
      };
    });
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 8, top: 'center', textStyle: { fontSize: 11 } },
    series: [{ type: 'pie', radius: ['45%', '70%'], center: ['35%', '50%'], data: pieData, label: { show: false } }],
  };
});

const projectBarOption = computed(() => {
  if (!chartStats.value || !chartStats.value.tasks_by_project.length) return {};
  const data = [...chartStats.value.tasks_by_project].reverse();
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 120, right: 24, top: 12, bottom: 28 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: {
      type: 'category',
      data: data.map(d => d.name),
      axisLabel: { fontSize: 11, overflow: 'truncate', width: 110 },
    },
    series: [{
      data: data.map(d => d.count),
      type: 'bar',
      itemStyle: { color: '#6366f1', borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 10 },
    }],
  };
});

// ──────────────── Level 2：專案圖表 ────────────────
const selectedTimelineId = ref<number | null>(null);
const projectStats = ref<ProjectStats | null>(null);
const loadingProjectStats = ref(false);

const loadProjectStats = async () => {
  if (!selectedTimelineId.value) return;
  loadingProjectStats.value = true;
  projectStats.value = null;
  try {
    const res = await timelineService.getMemberStats(selectedTimelineId.value);
    projectStats.value = res.data;
  } catch {
    toast.error('載入專案統計失敗');
  } finally {
    loadingProjectStats.value = false;
  }
};

const memberBarOption = computed(() => {
  if (!projectStats.value) return {};
  const members = [...projectStats.value.members].reverse();
  return {
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['總任務', '已完成'], bottom: 0, textStyle: { fontSize: 10 } },
    grid: { left: 80, right: 24, top: 12, bottom: 44 },
    xAxis: { type: 'value', minInterval: 1 },
    yAxis: {
      type: 'category',
      data: members.map(m => m.name),
      axisLabel: { fontSize: 10, overflow: 'truncate', width: 70 },
    },
    series: [
      { name: '總任務', type: 'bar', data: members.map(m => m.total_tasks), itemStyle: { color: '#cbd5e1', borderRadius: [0, 4, 4, 0] } },
      { name: '已完成', type: 'bar', data: members.map(m => m.completed_tasks), itemStyle: { color: '#10b981', borderRadius: [0, 4, 4, 0] } },
    ],
  };
});

const projectStatusOption = computed(() => {
  if (!projectStats.value) return {};
  const dist = projectStats.value.status_distribution;
  const pieData = Object.entries(dist)
    .filter(([, v]) => v > 0)
    .map(([k, v]) => {
      const key = k as StatusKey;
      return {
        name: STATUS_LABELS[key] || key,
        value: v,
        itemStyle: { color: STATUS_COLORS[key] },
      };
    });
  return {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { orient: 'vertical', right: 8, top: 'center', textStyle: { fontSize: 11 } },
    series: [{ type: 'pie', radius: ['45%', '70%'], center: ['35%', '50%'], data: pieData, label: { show: false } }],
  };
});

onMounted(async () => {
  await profileStore.fetchProfile();
  await profileStore.fetchStats();
  syncFormFromStore();
  await profileStore.fetchChartStats();
  if (ownedTimelines.value.length > 0) {
    selectedTimelineId.value = (ownedTimelines.value[0] as Timeline).id;
    await loadProjectStats();
  }
});
</script>
