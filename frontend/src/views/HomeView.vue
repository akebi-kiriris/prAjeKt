<template>
  <div class="h-full w-full bg-gray-50 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-6xl mx-auto">
    <!-- Welcome Card -->
    <div class="mt-4 mb-8 bg-linear-to-r from-primary to-primary-light rounded-2xl shadow-lg animate-slideDown">
      <div class="p-12 text-center text-white">
        <div class="flex items-center justify-center gap-4 mb-4">
          <h1 class="text-4xl font-bold">ProjectHub 專案管理</h1>
        </div>
        <p class="text-xl opacity-95">高效團隊協作，輕鬆管理專案進度！</p>
      </div>
    </div>

    <!-- Navigation Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mt-8">
      <router-link 
        v-for="card in navCards" 
        :key="card.path"
        :to="card.path" 
        class="no-underline"
      >
        <div class="bg-white rounded-xl shadow-md hover:shadow-xl hover:-translate-y-1 transition-all cursor-pointer h-full animate-fadeIn">
          <div class="p-8 text-center">
            <span class="text-5xl mb-4 block">{{ card.icon }}</span>
            <h3 class="text-xl font-semibold text-gray-800 mb-2">{{ card.title }}</h3>
            <p class="text-gray-500">{{ card.description }}</p>
          </div>
        </div>
      </router-link>
    </div>
    </div>
  </div>
</template>

<script setup>
const navCards = [
  {
    path: '/timelines',
    icon: '📊',
    title: '專案管理',
    description: '建立專案、分配任務'
  },
  {
    path: '/tasks',
    icon: '✅',
    title: '任務管理',
    description: '管理您的任務與進度'
  },
  {
    path: '/todos',
    icon: '📝',
    title: '待辦事項',
    description: '記錄日常待辦事項'
  },
  {
    path: '/groups',
    icon: '💬',
    title: '群組訊息',
    description: '與團隊溝通協作'
  },
  {
    path: '/profile',
    icon: '👤',
    title: '個人資料',
    description: '管理個人資料'
  }
];
</script>
