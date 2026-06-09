<template>
  <div v-if="open" class="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4" @click.self="$emit('close')">
    <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white shadow-[0_20px_40px_rgba(15,23,42,0.14)]">
      <div class="p-5 border-b border-slate-200 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-slate-800">👥 成員管理</h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">&times;</button>
      </div>
      <div class="p-5 space-y-4">
        <div v-if="timelineMembers.length > 0">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">目前成員</p>
          <div class="space-y-2">
            <div v-for="member in timelineMembers" :key="member.user_id" class="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
                  {{ (member.username || member.name || '?')[0].toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-slate-800">{{ member.username || member.name }}</p>
                  <p class="text-xs text-slate-500">{{ member.email }}</p>
                </div>
              </div>
              <div class="flex items-center gap-1.5">
                <span :class="['px-2 py-0.5 text-xs font-medium rounded-full', member.role === 0 ? 'bg-primary/10 text-primary' : 'bg-slate-100 text-slate-500']">
                  {{ member.role === 0 ? '負責人' : '協作者' }}
                </span>
                <button v-if="member.role !== 0" @click="$emit('kick-member', member)" class="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors text-sm font-bold">✕</button>
              </div>
            </div>
          </div>
        </div>
        <div :class="timelineMembers.length > 0 ? 'border-t border-slate-200 pt-4' : ''">
          <p class="text-sm text-slate-500 mb-3">邀請成員加入「{{ timelineName }}」</p>
          <div class="flex gap-2">
            <input v-model="inputEmailModel" type="email" placeholder="輸入用戶 Email" class="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" @keyup.enter="$emit('search-user')" />
            <button @click="$emit('search-user')" class="px-4 py-2.5 bg-primary text-white font-medium rounded-xl hover:brightness-110 transition-all">搜尋</button>
          </div>
          <div v-if="searchError" class="mt-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">{{ searchError }}</div>
          <div v-if="searchResult" class="mt-2 p-4 bg-green-50 border border-green-200 rounded-xl">
            <div class="flex items-center justify-between">
              <div>
                <p class="font-medium text-slate-800">{{ searchResult.name }}</p>
              </div>
              <button @click="$emit('confirm-share')" class="px-4 py-2 bg-primary text-white text-sm font-medium rounded-xl hover:brightness-110 transition-all">邀請</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { SearchUserResult, TaskMember } from '../../types';

const props = defineProps<{
  open: boolean;
  timelineName: string;
  timelineMembers: TaskMember[];
  inputEmail: string;
  searchResult: SearchUserResult | null;
  searchError: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'search-user'): void;
  (e: 'confirm-share'): void;
  (e: 'kick-member', member: TaskMember): void;
  (e: 'update:inputEmail', value: string): void;
}>();

const inputEmailModel = computed({
  get: () => props.inputEmail,
  set: (value: string) => emit('update:inputEmail', value),
});
</script>
