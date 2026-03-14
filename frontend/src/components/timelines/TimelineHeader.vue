<template>
  <div>
    <!-- Header -->
    <div class="text-center pt-6 pb-2 px-4 animate-slideDown">
      <div class="inline-flex items-center gap-3 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-sm mb-4">
        <span class="text-4xl">📊</span>
        <div class="text-left">
          <h1 class="text-2xl font-bold text-gray-800">專案管理</h1>
          <p class="text-sm text-gray-500">{{ todayFormatted }}</p>
        </div>
      </div>
    </div>
    
    <!-- Stats Overview -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 px-4">
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">📁</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">{{ timelines.length }}</p>
            <p class="text-xs text-gray-500">進行中專案</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">⚠️</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-orange-600">{{ urgentCount }}</p>
            <p class="text-xs text-gray-500">即將到期</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">✅</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-green-600">{{ totalCompletedTasks }}</p>
            <p class="text-xs text-gray-500">已完成任務</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">📋</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-purple-600">{{ totalTasks }}</p>
            <p class="text-xs text-gray-500">總任務數</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- View Toggle & Action Bar -->
    <div class="flex flex-col sm:flex-row justify-between items-center gap-4 px-4">
      <!-- View Toggle -->
      <div class="flex bg-white rounded-xl p-1 shadow-sm border border-gray-100">
        <button 
          @click="$emit('update:viewMode', 'card')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'card' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📇</span> 卡片
        </button>
        <button 
          @click="$emit('update:viewMode', 'kanban')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'kanban' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📊</span> 看板
        </button>
        <button 
          @click="$emit('update:viewMode', 'timeline')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'timeline' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📋</span> 列表
        </button>
        <button 
          @click="$emit('update:viewMode', 'calendar')"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'calendar' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📅</span> 月曆
        </button>
      </div>
      
      <!-- Add Button -->
      <button 
        @click="$emit('create-timeline')"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:brightness-110 transition-all"
      >
        <span class="text-lg">➕</span>
        <span>新增專案</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Timeline } from '../../types';

type ViewMode = 'card' | 'kanban' | 'timeline' | 'calendar';

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
