<template>
  <header class="fixed top-0 left-0 right-0 h-16 bg-white shadow-md flex justify-between items-center z-50 px-8">
    <div class="flex items-center">
      <!-- 漢堡選單按鈕（所有螢幕尺寸都顯示，固定在 logo 左側） -->
      <button @click="$emit('toggle-sidebar')" class="mr-4 focus:outline-none">
        <svg class="w-8 h-8 text-gray-700" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <!-- prAjeKt 文字 logo -->
      <span class="text-2xl font-bold text-primary tracking-wider select-none ml-2">prAjeKt</span>
    </div>
    
    <div class="flex items-center gap-4">
      <div class="flex items-center gap-4">
        <span class="text-gray-600">{{ userName }}</span>
        <button 
          @click="$emit('logout')" 
          class="px-4 py-2 bg-red-500 text-white border-none rounded cursor-pointer text-sm hover:bg-red-600 transition-colors " 
        >
          登出
        </button>
      </div>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();

const userName = computed(() => authStore.currentUser?.name || '使用者');

const props = defineProps({ sidebarOpen: Boolean });
defineEmits(['logout', 'toggle-sidebar']);
</script>
