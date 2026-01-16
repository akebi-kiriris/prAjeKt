<template>
  <nav
    class="fixed left-0 top-16 bottom-0 w-64 bg-gray-100 shadow-lg overflow-y-auto z-40 transition-transform duration-300"
    :class="{ '-translate-x-full': !open, 'translate-x-0': open }"
  >
    <!-- 關閉按鈕移回 Header，這裡不顯示 -->
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
</template>

<script setup>
defineProps({ open: Boolean });

const navItems = [
  { path: '/', icon: '🏠', text: '主頁' },
  { path: '/timelines', icon: '📊', text: '專案管理' },
  { path: '/tasks', icon: '✅', text: '任務管理' },
  { path: '/todos', icon: '📝', text: '待辦事項' },
  { path: '/groups', icon: '💬', text: '群組訊息' },
  { path: '/profile', icon: '👤', text: '個人資料' },
];
</script>

<style scoped>
@media (max-width: 768px) {
  nav {
    transform: translateX(-100%);
    transition: transform 0.3s;
  }
  
  nav.open {
    transform: translateX(0);
  }
}
</style>
