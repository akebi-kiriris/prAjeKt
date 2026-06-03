<template>
  <div class="px-4 pb-8">
    <div class="bg-white rounded-2xl shadow-lg border border-slate-200 overflow-hidden">
      <div class="p-5 border-b border-slate-200 bg-linear-to-r from-primary/5 via-blue-50 to-indigo-50">
        <div class="flex flex-wrap items-center justify-between gap-4">
          <h3 class="font-bold text-slate-800 flex items-center gap-2 text-lg">
            <span class="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center">📅</span>
            專案月曆
          </h3>
          <div class="flex flex-wrap items-center gap-4 text-sm bg-white/80 backdrop-blur-sm px-4 py-2.5 rounded-xl shadow-sm">
            <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-green-400 to-green-500 shadow-sm"></span> 已完成</span>
            <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-red-400 to-red-500 shadow-sm"></span> 已過期</span>
            <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-orange-400 to-orange-500 shadow-sm"></span> 緊急</span>
            <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-yellow-400 to-yellow-500 shadow-sm"></span> 即將到期</span>
            <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-blue-400 to-blue-500 shadow-sm"></span> 進行中</span>
          </div>
        </div>
      </div>
      <div class="p-6">
        <FullCalendar :options="calendarOptions" class="fc-custom" />
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
      <div class="bg-white rounded-2xl p-5 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
        <h4 class="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">📌</span>
          本週截止
        </h4>
        <div class="space-y-2 max-h-36 overflow-y-auto">
          <div v-for="timeline in thisWeekTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="flex items-center justify-between p-3 bg-linear-to-r from-orange-50 to-amber-50 rounded-xl cursor-pointer hover:from-orange-100 hover:to-amber-100 transition-all border border-orange-100">
            <span class="text-sm font-medium text-slate-700 truncate">{{ timeline.name }}</span>
            <span class="text-xs bg-orange-500 text-white px-2 py-1 rounded-full font-medium">{{ getDaysRemaining(timeline.endDate).text }}</span>
          </div>
          <p v-if="thisWeekTimelines.length === 0" class="text-sm text-slate-400 text-center py-4">📋 無專案</p>
        </div>
      </div>
      <div class="bg-white rounded-2xl p-5 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
        <h4 class="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">🔥</span>
          已過期專案
        </h4>
        <div class="space-y-2 max-h-36 overflow-y-auto">
          <div v-for="timeline in overdueTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="flex items-center justify-between p-3 bg-linear-to-r from-red-50 to-rose-50 rounded-xl cursor-pointer hover:from-red-100 hover:to-rose-100 transition-all border border-red-100">
            <span class="text-sm font-medium text-slate-700 truncate">{{ timeline.name }}</span>
            <span class="text-xs bg-red-500 text-white px-2 py-1 rounded-full font-medium">{{ getDaysRemaining(timeline.endDate).text }}</span>
          </div>
          <p v-if="overdueTimelines.length === 0" class="text-sm text-slate-400 text-center py-4">👍 無過期專案</p>
        </div>
      </div>
      <div class="bg-white rounded-2xl p-5 shadow-lg border border-slate-200 hover:shadow-xl transition-shadow">
        <h4 class="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
          <span class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">✅</span>
          近期完成
        </h4>
        <div class="space-y-2 max-h-36 overflow-y-auto">
          <div v-for="timeline in completedTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="flex items-center justify-between p-3 bg-linear-to-r from-green-50 to-emerald-50 rounded-xl cursor-pointer hover:from-green-100 hover:to-emerald-100 transition-all border border-green-100">
            <span class="text-sm font-medium text-slate-700 truncate">{{ timeline.name }}</span>
            <span class="text-xs bg-green-500 text-white px-2 py-1 rounded-full font-medium">100%</span>
          </div>
          <p v-if="completedTimelines.length === 0" class="text-sm text-slate-400 text-center py-4">🎯 尚無完成專案</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import FullCalendar from '@fullcalendar/vue3';
import type { CalendarOptions } from '@fullcalendar/core';
import type { Timeline } from '../../types';

type DaysRemaining = {
  text: string;
};

defineProps<{
  calendarOptions: CalendarOptions;
  thisWeekTimelines: Timeline[];
  overdueTimelines: Timeline[];
  completedTimelines: Timeline[];
  getDaysRemaining: (endDate: string | null | undefined) => DaysRemaining;
}>();

defineEmits<{
  (e: 'view-timeline', timeline: Timeline): void;
}>();
</script>
