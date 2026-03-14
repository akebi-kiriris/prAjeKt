<template>
  <div>
    <!-- 桌面版：左側 Sidebar -->
    <nav
      class="hidden md:block fixed left-0 top-16 bottom-0 w-64 bg-gray-100 shadow-lg overflow-y-auto z-40 transition-transform duration-300"
      :class="{ '-translate-x-full': !open, 'translate-x-0': open }"
    >
      <ul class="list-none py-4">
        <li v-for="item in navItems" :key="item.path">
          <router-link 
            :to="item.path" 
            class="flex items-center h-12 py-4 px-6 mb-2 m-2 text-gray-600 no-underline transition-all hover:bg-gray-100 hover:text-primary rounded-lg border-2"
            :class="{ 'bg-emerald-100 text-primary border-r-32 border-primary': $route.path === item.path }"
          >
            <span class="text-2xl mr-4 ml-2">{{ item.icon }}</span>
            <span class="text-xl font-bold font-sans tracking-wide">{{ item.text }}</span>
          </router-link>
        </li>
      </ul>
    </nav>

    <!-- 手機版：底部導航列 -->
    <nav class="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-9999 backdrop-blur-lg">
      <ul class="flex justify-around items-center list-none m-0 p-0">
        <li v-for="item in navItems" :key="item.path" class="flex-1">
          <router-link 
            :to="item.path" 
            class="flex flex-col items-center justify-center py-2 px-1 text-gray-600 no-underline transition-all"
            :class="{ 'text-emerald-600': $route.path === item.path }"
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
  { path: '/tasks', icon: '✅', text: '任務管理' },
  { path: '/todos', icon: '📝', text: '待辦事項' },
  { path: '/groups', icon: '💬', text: '群組訊息' },
  { path: '/profile', icon: '👤', text: '個人資料' },
  { path: '/trash', icon: '🗑️', text: '垃圾桶' },
];
</script>

