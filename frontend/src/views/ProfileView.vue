<template>
  <div class="h-full w-full bg-gray-50 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-6xl mb-4 block animate-pulse-custom">👤</span>
      <h1 class="text-4xl font-bold mb-2 text-gray-800">個人資料</h1>
      <p class="text-lg text-gray-600">管理您的個人資訊與設定</p>
    </div>
    
    <!-- Profile Container -->
    <div class="pb-8">
      <!-- Loading -->
      <div v-if="loading" class="bg-white rounded-2xl shadow-xl p-12 text-center animate-fadeIn">
        <span class="text-4xl block mb-4 animate-spin">⏳</span>
        <p class="text-gray-600">載入中...</p>
      </div>
      
      <!-- Profile Card -->
      <div v-else class="bg-white rounded-2xl shadow-xl overflow-hidden mb-8 animate-slideUp">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>👤</span>
            基本資料
          </h2>
          <button 
            v-if="!isEditing"
            @click="isEditing = true"
            class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors flex items-center gap-2"
          >
            <span>✏️</span>
            編輯資料
          </button>
        </div>
        
        <div class="p-6">
          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">姓名 *</label>
                <div>
                  <input 
                    v-model="profileForm.name" 
                    type="text" 
                    :disabled="!isEditing"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">用戶名（選填）</label>
                <div>
                  <input 
                    v-model="profileForm.username" 
                    type="text" 
                    :disabled="!isEditing"
                    placeholder="如：john_doe"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">電子郵件 *</label>
                <div>
                  <input 
                    v-model="profileForm.email" 
                    type="email" 
                    :disabled="!isEditing"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                    required
                  />
                </div>
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">電話</label>
                <div>
                  <input 
                    v-model="profileForm.phone" 
                    type="tel" 
                    :disabled="!isEditing"
                    class="w-full pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all disabled:bg-gray-100 disabled:cursor-not-allowed"
                  />
                </div>
              </div>
            </div>
            
            <!-- Password Section -->
            <template v-if="isEditing">
              <div class="flex items-center gap-2 my-6">
                <div class="flex-1 h-px bg-gray-200"></div>
                <span class="px-4 text-gray-400 text-sm flex items-center gap-2">
                  <span>🔒</span>
                  變更密碼（選填）
                </span>
                <div class="flex-1 h-px bg-gray-200"></div>
              </div>
              
              <div>
                <label class="block text-sm font-semibold text-gray-600 mb-2">目前密碼</label>
                <input 
                  v-model="profileForm.current_password" 
                  type="password" 
                  placeholder="如要變更密碼，請輸入目前密碼"
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                />
              </div>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-semibold text-gray-600 mb-2">新密碼</label>
                  <input 
                    v-model="profileForm.new_password" 
                    type="password" 
                    placeholder="請輸入新密碼"
                    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-semibold text-gray-600 mb-2">確認新密碼</label>
                  <input 
                    v-model="profileForm.confirm_password" 
                    type="password" 
                    placeholder="再次輸入新密碼"
                    class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                  />
                </div>
              </div>
            </template>
            
            <div v-if="isEditing" class="flex gap-3 pt-4">
              <button 
                type="submit"
                class="px-6 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center gap-2"
                style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
              >
                <span>✓</span>
                儲存變更
              </button>
              <button 
                type="button"
                @click="cancelEdit"
                class="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all flex items-center gap-2"
              >
                <span>✕</span>
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
      
      <!-- Stats Grid -->
      <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div 
          v-for="stat in statCards" 
          :key="stat.label"
          class="bg-white rounded-xl shadow-md hover:-translate-y-1 hover:shadow-xl transition-all animate-fadeIn p-6"
        >
          <div class="flex items-center gap-4">
            <span class="text-3xl animate-bounce-custom">{{ stat.icon }}</span>
            <div>
              <h4 class="text-sm text-gray-500 font-medium">{{ stat.label }}</h4>
              <p class="text-2xl font-bold gradient-text">{{ stat.value }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { toast } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useProfileStore } from '../stores/profile';
import { useAuthStore } from '../stores/auth';

const profileStore = useProfileStore();
const authStore = useAuthStore();

// ────────────── Store 狀態（響應式解構）──────────────
const { profile, loading, statCards } = storeToRefs(profileStore);

// ────────────── View-local UI 狀態 ──────────────
const isEditing = ref(false);
const profileForm = ref({
  name: '',
  username: '',
  email: '',
  phone: '',
  current_password: '',
  new_password: '',
  confirm_password: ''
});
const originalProfile = ref({});
// ────────────── 初始化表單（從 store profile 同步）──────────────
const syncFormFromStore = () => {
  profileForm.value = {
    name: profile.value.name || '',
    username: profile.value.username || '',
    email: profile.value.email || '',
    phone: profile.value.phone || '',
    current_password: '',
    new_password: '',
    confirm_password: ''
  };
  originalProfile.value = { ...profileForm.value };
};

// ────────────── CRUD ──────────────
const handleSubmit = async () => {
  if (profileForm.value.new_password) {
    if (!profileForm.value.current_password) { toast.warning('請輸入目前密碼'); return; }
    if (profileForm.value.new_password !== profileForm.value.confirm_password) { toast.warning('新密碼與確認密碼不一致'); return; }
    if (profileForm.value.new_password.length < 6) { toast.warning('新密碼至少需要 6 個字元'); return; }
  }

  try {
    const updateData = {
      name: profileForm.value.name,
      username: profileForm.value.username,
      email: profileForm.value.email,
      phone: profileForm.value.phone
    };
    if (profileForm.value.new_password) {
      updateData.current_password = profileForm.value.current_password;
      updateData.new_password = profileForm.value.new_password;
    }
    await profileStore.updateProfile(updateData);
    await authStore.fetchCurrentUser();
    toast.success('個人資料更新成功');
    isEditing.value = false;
    profileForm.value.current_password = '';
    profileForm.value.new_password = '';
    profileForm.value.confirm_password = '';
    originalProfile.value = { ...profileForm.value };
  } catch (error) {
    toast.error(error.response?.data?.error || '更新失敗');
  }
};

const cancelEdit = () => {
  profileForm.value = { ...originalProfile.value };
  profileForm.value.current_password = '';
  profileForm.value.new_password = '';
  profileForm.value.confirm_password = '';
  isEditing.value = false;
};

onMounted(async () => {
  await profileStore.fetchProfile();
  await profileStore.fetchStats();
  syncFormFromStore();
});
</script>
