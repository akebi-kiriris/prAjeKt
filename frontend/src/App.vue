<template>
  <Toaster position="top-right" richColors />
  <ConfirmDialog />
  <div id="app" class="min-h-screen" :class="isAuthenticated ? 'bg-gray-100 grid grid-rows-[4rem_1fr]' : ''" :style="isAuthenticated ? gridTemplateColumns : {}">
    <!-- Header -->
    <Header v-if="isAuthenticated" :sidebarOpen="sidebarOpen" @logout="handleLogout" @toggle-sidebar="sidebarOpen = !sidebarOpen" class="row-start-1 row-end-2 col-start-1 col-end-3 z-50" />
    <!-- Sidebar（桌面左側 / 手機底部導航，皆為 fixed 不佔 grid 空間） -->
    <Sidebar v-if="isAuthenticated" :open="sidebarOpen" @close="sidebarOpen = false" />
    <!-- Main Content -->
    <!--<main :class="[mainClass, isMobile ? 'mb-20' : '']" :style="sidebarOpen && !isMobile ? '' : 'background: #f3f4f6;'">-->
    <main :class="mainClass" :style="sidebarOpen && !isMobile ? '' : 'background: #f3f4f6;'">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, watch, ref, onMounted, onUnmounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from './stores/auth';
import Header from './components/Header.vue';
import Sidebar from './components/Sidebar.vue';
import { Toaster } from 'vue-sonner';
import ConfirmDialog from './components/ConfirmDialog.vue';

// 手機/桌面偵測（以 768px 為分界，對應 Tailwind md:）
const isMobile = ref(window.innerWidth < 768)
const sidebarOpen = ref(!isMobile.value)

const handleResize = () => {
  isMobile.value = window.innerWidth < 768
  if (isMobile.value) sidebarOpen.value = false
}
onMounted(() => window.addEventListener('resize', handleResize))
onUnmounted(() => window.removeEventListener('resize', handleResize))

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const isAuthenticated = computed(() => authStore.isAuthenticated);

// Grid 欄寬：手機單欄 / 桌面雙欄（含側邊欄開關）
const gridTemplateColumns = computed(() => {
  if (isMobile.value) return { gridTemplateColumns: '1fr' }
  return sidebarOpen.value
    ? { gridTemplateColumns: '16rem 1fr' }
    : { gridTemplateColumns: '0 1fr' }
})

// main 欄位配置：手機佔滿單欄，桌面放在第 2 欄
const mainClass = computed(() => {
  if (!isAuthenticated.value) return 'w-full min-h-screen'
  return isMobile.value
    ? 'row-start-2 row-end-3 min-h-0'
    : 'row-start-2 row-end-3 col-start-2 col-end-3 min-h-0'
})

const handleLogout = async () => {
  await authStore.logout();
  router.push('/login');
};

// 每次路由切換時自動刷新 user 狀態，避免 Header 用戶名變回預設
watch(
  () => route.fullPath,
  async () => {
    if (authStore.isAuthenticated && !authStore.user) {
      await authStore.fetchCurrentUser();
    }
  },
  { immediate: true }
);
</script>
