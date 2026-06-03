<template>
  <div>
    <!-- 桌面版：左側 Sidebar -->
    <nav
      class="fixed top-16 bottom-0 left-0 z-40 hidden w-64 overflow-y-auto border-r border-slate-200 bg-white md:block transition-transform duration-300"
      :class="{ '-translate-x-full': !open, 'translate-x-0': open }"
    >
      <ul class="list-none py-4">
        <li v-for="item in navItems" :key="item.path">
          <router-link
            :to="item.path"
            class="mx-2 mb-2 flex h-12 items-center rounded-xl border border-transparent px-4 py-3 text-slate-600 no-underline transition-all hover:border-slate-200 hover:bg-slate-50 hover:text-primary"
            :class="{ 'border-primary/30 bg-primary/10 text-primary shadow-sm': $route.path === item.path }"
          >
            <span class="mr-3 text-xl">{{ item.icon }}</span>
            <span class="text-base font-semibold tracking-wide">{{ item.text }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- 手機版：底部導航列 -->
    <nav class="fixed right-0 bottom-0 left-0 z-70 border-t border-slate-200 bg-white/95 backdrop-blur md:hidden">
      <ul class="flex justify-around items-center list-none m-0 p-0">
        <li v-for="item in navItems" :key="item.path" class="flex-1">
          <router-link
            :to="item.path"
            class="flex flex-col items-center justify-center px-1 py-2 text-slate-600 no-underline transition-all"
            :class="{ 'text-primary': $route.path === item.path }"
          >
            <span class="text-2xl mb-1">{{ item.icon }}</span>
            <span class="text-xs font-medium">{{ item.text }}</span>
          </router-link>
        </li>
      </ul>
    </nav>
  </div>
</template>

<script setup lang="ts">
import type { SidebarNavItem } from '../types';

defineProps<{
  open: boolean;
}>();

defineEmits<{
  (e: 'close'): void;
}>();

const navItems: SidebarNavItem[] = [
  { path: '/', icon: '🏠', text: '主頁' },
  { path: '/timelines', icon: '📊', text: '專案管理' },
  { path: '/knowledge', icon: '📚', text: '知識庫' },
  { path: '/tasks', icon: '✅', text: '任務管理' },
  { path: '/todos', icon: '📝', text: '待辦事項' },
  { path: '/groups', icon: '💬', text: '群組訊息' },
  { path: '/profile', icon: '👤', text: '個人資料' },
  { path: '/trash', icon: '🗑️', text: '垃圾桶' },
];
</script>
