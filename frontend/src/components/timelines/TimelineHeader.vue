<template>
  <div class="space-y-4">
    <div class="px-4 pt-2">
      <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
        PROJECT OPERATIONS
      </p>
      <h1 class="text-[clamp(1.3rem,2vw,1.8rem)] font-black tracking-[0.01em] text-slate-900">專案管理</h1>
      <p class="mt-1 text-sm text-slate-500">{{ todayFormatted }}</p>
    </div>
    
    <!-- Stats Overview -->
    <div class="grid grid-cols-2 gap-4 px-4 md:grid-cols-4">
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_20px_rgba(15,23,42,0.06)]">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">📁</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-slate-800">{{ timelines.length }}</p>
            <p class="text-xs text-slate-500">進行中專案</p>
          </div>
        </div>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_20px_rgba(15,23,42,0.06)]">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">⚠️</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-orange-600">{{ urgentCount }}</p>
            <p class="text-xs text-slate-500">即將到期</p>
          </div>
        </div>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_20px_rgba(15,23,42,0.06)]">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">✅</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-green-600">{{ totalCompletedTasks }}</p>
            <p class="text-xs text-slate-500">已完成任務</p>
          </div>
        </div>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-4 shadow-[0_10px_20px_rgba(15,23,42,0.06)]">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">📋</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-purple-600">{{ totalTasks }}</p>
            <p class="text-xs text-slate-500">總任務數</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- View Toggle & Action Bar -->
    <div class="flex flex-col items-center justify-between gap-4 px-4 sm:flex-row">
      <!-- View Toggle -->
      <div class="flex rounded-xl border border-slate-200 bg-white p-1 shadow-sm">
        <button 
          @click="$emit('update:viewMode', 'card')"
          :class="[
            'rounded-lg px-4 py-2 text-sm font-medium transition-all',
            viewMode === 'card' ? 'bg-primary text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
          ]"
        >
          <span class="mr-1">📇</span> 卡片
        </button>
        <button 
          @click="$emit('update:viewMode', 'kanban')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'kanban' ? 'bg-primary text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
          ]"
        >
          <span class="mr-1">📊</span> 看板
        </button>
        <button 
          @click="$emit('update:viewMode', 'timeline')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'timeline' ? 'bg-primary text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
          ]"
        >
          <span class="mr-1">📋</span> 列表
        </button>
        <button 
          @click="$emit('update:viewMode', 'calendar')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'calendar' ? 'bg-primary text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
          ]"
        >
          <span class="mr-1">📅</span> 月曆
        </button>
        <button 
          @click="$emit('update:viewMode', 'gantt')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'gantt' ? 'bg-primary text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
          ]"
        >
          <span class="mr-1">📈</span> 甘特圖
        </button>
      </div>
      
      <!-- Add Button -->
      <button
        @click="$emit('create-timeline')"
        class="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 font-semibold text-white shadow-[0_8px_18px_rgba(37,99,235,0.24)] transition-all hover:brightness-110"
      >
        <span class="text-lg">➕</span>
        <span>新增專案</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Timeline, ViewMode } from '../../types';

defineProps<{
  todayFormatted: string;
  timelines: Timeline[];
  urgentCount: number;
  totalCompletedTasks: number;
  totalTasks: number;
  viewMode: ViewMode;
}>();

defineEmits<{
  (e: 'update:viewMode', mode: ViewMode): void;
  (e: 'create-timeline'): void;
}>();
</script>
