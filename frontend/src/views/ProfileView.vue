<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <div class="mx-auto grid w-full max-w-6xl grid-cols-1 gap-6">
      <header
        class="overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-brrom-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]"
      >
        <div class="relative px-5 py-5 md:px-6 md:py-6">
          <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />
          <div class="relative flex flex-wrap items-start justify-between gap-4">
            <div>
              <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
                PROFILE CENTER
              </p>
              <h1 class="text-[clamp(1.45rem,2.2vw,2rem)] font-black tracking-[0.01em] text-slate-900">個人資料</h1>
              <p class="mt-2 text-sm leading-6 text-slate-600">管理您的個人資訊與任務數據。</p>
            </div>
          </div>
        </div>
      </header>
    
    <!-- Profile Container -->
    <div class="pb-8">
      <!-- Loading -->
      <div v-if="loading" class="rounded-3xl border border-slate-200 bg-white p-12 text-center shadow-[0_12px_28px_rgba(15,23,42,0.06)]">
        <span class="mb-4 block text-4xl animate-spin">⏳</span>
        <p class="text-slate-600">載入中...</p>
      </div>
      
      <!-- Profile Card -->
      <div v-else class="mb-8 overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_12px_28px_rgba(15,23,42,0.06)]">
        <div class="flex items-center justify-between border-b border-slate-200 p-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-slate-800">
            基本資料
          </h2>
          <button 
            v-if="!isEditing"
            @click="isEditing = true"
            class="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
          >
            編輯資料
          </button>
        </div>
        
        <div class="p-6">
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">姓名 *</label>
                <div>
                  <input 
                    v-model="profileForm.name" 
                    type="text" 
                    :disabled="!isEditing"
                    class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20 disabled:cursor-not-allowed disabled:bg-slate-100"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">用戶名（選填）</label>
                <div>
                  <input 
                    v-model="profileForm.username" 
                    type="text" 
                    :disabled="!isEditing"
                    placeholder="如：john_doe"
                    class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20 disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">電子郵件 *</label>
                <div>
                  <input 
                    v-model="profileForm.email" 
                    type="email" 
                    :disabled="!isEditing"
                    class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20 disabled:cursor-not-allowed disabled:bg-slate-100"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">電話</label>
                <div>
                  <input 
                    v-model="profileForm.phone" 
                    type="tel" 
                    :disabled="!isEditing"
                    class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20 disabled:cursor-not-allowed disabled:bg-slate-100"
                  />
                </div>
              </div>
            </div>
            
            <!-- Password Section -->
            <template v-if="isEditing">
              <div class="flex items-center gap-2 my-6">
                <div class="h-px flex-1 bg-slate-200"></div>
                <span class="flex items-center gap-2 px-4 text-sm text-slate-400">
                  變更密碼（選填）
                </span>
                <div class="h-px flex-1 bg-slate-200"></div>
              </div>
              
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">目前密碼</label>
                <input 
                  v-model="profileForm.current_password" 
                  type="password" 
                  placeholder="如要變更密碼，請輸入目前密碼"
                  class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                />
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="mb-2 block text-sm font-semibold text-slate-600">新密碼</label>
                  <input 
                    v-model="profileForm.new_password" 
                    type="password" 
                    placeholder="請輸入新密碼"
                    class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                  />
                </div>
                
                <div>
                  <label class="mb-2 block text-sm font-semibold text-slate-600">確認新密碼</label>
                  <input 
                    v-model="profileForm.confirm_password" 
                    type="password" 
                    placeholder="再次輸入新密碼"
                    class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                  />
                </div>
              </div>
            </template>
            
            <div v-if="isEditing" class="flex gap-3 pt-4">
              <button 
                type="submit"
                class="rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)]"
              >
                儲存變更
              </button>
              <button 
                type="button"
                @click="cancelEdit"
                class="rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
      
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <div 
          v-for="stat in statCards" 
          :key="stat.label"
          class="rounded-2xl border border-slate-200 bg-white p-6 shadow-[0_12px_26px_rgba(15,23,42,0.06)] transition hover:-translate-y-px hover:shadow-[0_16px_30px_rgba(15,23,42,0.08)]"
        >
          <div class="flex items-center gap-4">
            <span class="text-3xl">{{ stat.icon }}</span>
            <div>
              <h4 class="text-sm font-medium text-slate-500">{{ stat.label }}</h4>
              <p class="text-2xl font-bold text-slate-800">{{ stat.value }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ── Level 1: 個人數據分析 ── -->
      <div v-if="chartLoading" class="mt-8 flex justify-center py-8">
        <span class="text-2xl animate-spin">⏳</span>
      </div>
      <div v-else-if="chartStats" class="mt-8 space-y-6">
        <h3 class="flex items-center gap-2 text-lg font-semibold text-slate-700">
          個人數據分析
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_22px_rgba(15,23,42,0.05)]">
            <h4 class="mb-3 text-sm font-semibold text-slate-600">近 30 天完成趨勢</h4>
            <v-chart :option="trendOption" autoresize style="height:220px" />
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_22px_rgba(15,23,42,0.05)]">
            <h4 class="mb-3 text-sm font-semibold text-slate-600">任務狀態分布</h4>
            <v-chart :option="statusPieOption" autoresize style="height:220px" />
          </div>
        </div>
        <div v-if="chartStats.tasks_by_project.length > 0" class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_22px_rgba(15,23,42,0.05)]">
          <h4 class="mb-3 text-sm font-semibold text-slate-600">各專案任務量</h4>
          <v-chart
            :option="projectBarOption"
            autoresize
            :style="`height:${Math.max(160, chartStats.tasks_by_project.length * 36 + 60)}px`"
          />
        </div>
      </div>

      <!-- ── Level 2: 專案數據分析（負責人） ── -->
      <div v-if="ownedTimelines.length > 0" class="mb-8 mt-8 space-y-4">
        <h3 class="flex items-center gap-2 text-lg font-semibold text-slate-700">
          專案數據分析
          <span class="ml-1 text-xs font-normal text-slate-400">（僅負責人可見）</span>
        </h3>
        <div class="flex items-center gap-3 flex-wrap">
          <label class="whitespace-nowrap text-sm text-slate-600">選擇專案：</label>
          <select
            v-model="selectedTimelineId"
            @change="loadProjectStats"
            class="rounded-lg border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
          >
            <option v-for="tl in ownedTimelines" :key="tl.id" :value="tl.id">{{ tl.name }}</option>
          </select>
          <span v-if="loadingProjectStats" class="animate-spin text-lg">⏳</span>
        </div>
        <div v-if="projectStats" class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_22px_rgba(15,23,42,0.05)]">
            <h4 class="mb-10 text-sm font-semibold text-slate-600">成員任務貢獻</h4>
            <v-chart
              :option="memberBarOption"
              autoresize
              :style="`height:${Math.max(160, projectStats.members.length * 44 + 60)}px`"
            />
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_22px_rgba(15,23,42,0.05)]">
            <h4 class="mb-1 text-sm font-semibold text-slate-600">專案任務狀態</h4>
            <p class="mb-2 text-xs text-slate-400">共 {{ projectStats.total_tasks }} 筆任務</p>
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
import { getApiErrorMessage } from '../utils/apiError';
import type {
  ProfileForm,
  ProfileUpdatePayload,
  ProjectStats,
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
  chartStats,
  chartLoading,
  ownedTimelines,
} = storeToRefs(profileStore);

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
    toast.error(getApiErrorMessage(error, '更新失敗'));
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

const isStatusKey = (value: string): value is StatusKey => value in STATUS_LABELS;

const mapStatusDistributionToPieData = (distribution: Record<string, number>) =>
  Object.entries(distribution)
    .filter((entry): entry is [StatusKey, number] => {
      const [key, count] = entry;
      return count > 0 && isStatusKey(key);
    })
    .map(([key, value]) => ({
      name: STATUS_LABELS[key],
      value,
      itemStyle: { color: STATUS_COLORS[key] },
    }));

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
  const pieData = mapStatusDistributionToPieData(chartStats.value.status_distribution);
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
  } catch (error) {
    toast.error(getApiErrorMessage(error, '載入專案統計失敗'));
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
  const pieData = mapStatusDistributionToPieData(projectStats.value.status_distribution);
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
    selectedTimelineId.value = ownedTimelines.value[0].id;
    await loadProjectStats();
  }
});
</script>
