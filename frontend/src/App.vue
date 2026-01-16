<template>
  <div id="app" class="min-h-screen" :class="isAuthenticated ? 'bg-gray-100 grid grid-rows-[4rem_1fr]' : ''" :style="isAuthenticated ? gridTemplateColumns : {}">
    <!-- Header -->
    <Header v-if="isAuthenticated" :sidebarOpen="sidebarOpen" @logout="handleLogout" @toggle-sidebar="sidebarOpen = !sidebarOpen" class="row-start-1 row-end-2 col-start-1 col-end-3 z-50" />
    <!-- Sidebar -->
    <Sidebar v-if="isAuthenticated" :open="sidebarOpen" @close="sidebarOpen = false" class="row-start-2 row-end-3 col-start-1 col-end-2 z-40" />
    <!-- Main Content -->
    <main :class="isAuthenticated ? 'row-start-2 row-end-3 col-start-2 col-end-3 min-h-0' : 'w-full min-h-screen'" :style="sidebarOpen ? '' : 'background: #f3f4f6;'">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, watch, ref } from 'vue';
const sidebarOpen = ref(true); // 桌面預設開啟，手機預設可關閉
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from './stores/auth';
import Header from './components/Header.vue';
import Sidebar from './components/Sidebar.vue';

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();

const isAuthenticated = computed(() => authStore.isAuthenticated);

// 根據側邊欄狀態動態調整 grid 列寬
const gridTemplateColumns = computed(() => {
  return sidebarOpen.value
    ? { gridTemplateColumns: '16rem 1fr' }
    : { gridTemplateColumns: '0 1fr' };
});

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

<style>
@media (max-width: 768px) {
  .ml-64 {
    margin-left: 0 !important;
  }
}
</style>
