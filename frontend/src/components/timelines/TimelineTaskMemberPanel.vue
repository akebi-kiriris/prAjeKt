<template>
  <div v-if="open" class="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4" @click.self="$emit('close')">
    <div class="w-full max-w-md rounded-2xl border border-slate-200 bg-white shadow-[0_20px_40px_rgba(15,23,42,0.14)]">
      <div class="p-5 border-b border-slate-200 flex justify-between items-center">
        <h3 class="text-lg font-semibold text-slate-800">👥 任務成員 — {{ taskName }}</h3>
        <button @click="$emit('close')" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">&times;</button>
      </div>
      <div class="p-5 space-y-4">
        <div>
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">目前成員</p>
          <div v-if="taskMembersForAssign.length === 0" class="text-center py-3 text-slate-400 text-sm">尚無指派成員</div>
          <div v-else class="space-y-2">
            <div v-for="member in taskMembersForAssign" :key="member.user_id" class="flex items-center justify-between p-2.5 bg-slate-50 rounded-xl">
              <div class="flex items-center gap-2.5">
                <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
                  {{ (member.name || '?')[0].toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-slate-800">{{ member.name }}</p>
                  <p class="text-xs text-slate-500">{{ member.email }}</p>
                </div>
              </div>
              <div class="flex items-center gap-1.5">
                <span :class="['px-2 py-0.5 text-xs font-medium rounded-full', member.role === 0 ? 'bg-primary/10 text-primary' : 'bg-slate-100 text-slate-500']">
                  {{ member.role === 0 ? '負責人' : '協作者' }}
                </span>
                <button
                  v-if="member.role !== 0"
                  @click="$emit('set-owner', member)"
                  class="px-2 py-1 text-[11px] font-medium rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
                >設為主責</button>
                <button v-if="member.role !== 0" @click="$emit('kick-member', member)" class="w-7 h-7 flex items-center justify-center text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors text-sm font-bold">✕</button>
              </div>
            </div>
          </div>
        </div>
        <div class="border-t border-slate-200 pt-4">
          <p class="text-xs font-medium text-slate-500 uppercase tracking-wide mb-2">專案成員快速指派</p>
          <div v-if="timelineMembers.length === 0" class="text-center py-3 text-slate-400 text-sm">載入中...</div>
          <template v-else>
            <div v-if="assignableMembers.length === 0" class="text-center py-3 text-slate-400 text-sm">所有專案成員皆已加入此任務</div>
            <div v-else class="space-y-2">
              <div
                v-for="member in assignableMembers"
                :key="member.user_id"
                class="flex items-center justify-between p-2.5 bg-indigo-50 rounded-xl"
              >
                <div class="flex items-center gap-2.5">
                  <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-sm font-bold text-indigo-600 shrink-0">
                    {{ (member.username || member.name || '?')[0].toUpperCase() }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-slate-800">{{ member.username || member.name }}</p>
                    <p class="text-xs text-slate-500">{{ member.email }}</p>
                  </div>
                </div>
                <button @click="$emit('quick-assign', member)" class="px-3 py-1 bg-primary text-white text-xs font-medium rounded-lg hover:brightness-110 transition-all">指派</button>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { TaskMember } from '../../types';

const props = defineProps<{
  open: boolean;
  taskName: string;
  taskMembersForAssign: TaskMember[];
  timelineMembers: TaskMember[];
}>();

defineEmits<{
  (e: 'close'): void;
  (e: 'quick-assign', member: TaskMember): void;
  (e: 'kick-member', member: TaskMember): void;
  (e: 'set-owner', member: TaskMember): void;
}>();

const assignableMembers = computed(() =>
  props.timelineMembers.filter((member) => !props.taskMembersForAssign.some((taskMember) => taskMember.user_id === member.user_id))
);
</script>
