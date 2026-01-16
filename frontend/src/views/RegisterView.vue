<template>
  <div class="min-h-screen flex justify-center items-center p-8 bg-linear-to-br from-purple-500 to-purple-800 relative overflow-hidden">
    <!-- Decorative shapes -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute w-72 h-72 bg-white/10 rounded-full -top-24 -left-24 animate-float"></div>
      <div class="absolute w-48 h-48 bg-white/10 rounded-full -bottom-12 -right-12 animate-float" style="animation-delay: 5s"></div>
      <div class="absolute w-36 h-36 bg-white/10 rounded-full top-1/2 right-[10%] animate-float" style="animation-delay: 10s"></div>
    </div>
    
    <div class="w-full max-w-xl relative z-10 bg-white/95 rounded-3xl shadow-2xl backdrop-blur-sm animate-slideUp">
      <div class="p-10">
        <div class="text-center mb-8">
          <div class="mb-4">
            <span class="text-5xl animate-pulse-custom inline-block">🚀</span>
          </div>
          <h2 class="text-3xl font-bold gradient-text mb-2">創建帳號</h2>
          <p class="text-gray-500">加入 ProjectHub 開始專案管理</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="space-y-5">
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">姓名 *</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">👤</span>
              <input 
                v-model="formData.name" 
                type="text" 
                placeholder="請輸入姓名"
                class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">用戶名（選填）</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">@</span>
              <input 
                v-model="formData.username" 
                type="text" 
                placeholder="請輸入唯一用戶名，如：john_doe"
                class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
            </div>
            <p class="text-xs text-gray-500 mt-1">用戶名可用於搜尋和標註，留空則使用 Email</p>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">Email *</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">📧</span>
              <input 
                v-model="formData.email" 
                type="email" 
                placeholder="請輸入 email"
                class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">電話</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">📱</span>
              <input 
                v-model="formData.phone" 
                type="tel" 
                placeholder="請輸入電話"
                class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">密碼 *</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔒</span>
              <input 
                v-model="formData.password" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="請輸入密碼"
                class="w-full pl-12 pr-12 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
              <button 
                type="button"
                @click="showPassword = !showPassword"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {{ showPassword ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">確認密碼 *</label>
            <div class="relative">
              <span class="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">🔒</span>
              <input 
                v-model="confirmPassword" 
                :type="showConfirmPassword ? 'text' : 'password'" 
                placeholder="請再次輸入密碼"
                class="w-full pl-12 pr-12 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
              <button 
                type="button"
                @click="showConfirmPassword = !showConfirmPassword"
                class="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                {{ showConfirmPassword ? '👁️' : '👁️‍🗨️' }}
              </button>
            </div>
          </div>
          
          <div v-if="errorMessage" class="p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm">
            {{ errorMessage }}
          </div>
          
          <div v-if="successMessage" class="p-3 bg-green-50 border border-green-200 text-green-600 rounded-lg text-sm">
            {{ successMessage }}
          </div>
          
          <button 
            type="submit" 
            :disabled="loading"
            class="w-full py-4 font-bold text-lg rounded-full border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
          >
            <span v-if="loading">註冊中...</span>
            <span v-else class="flex items-center justify-center gap-2">
              ✓ 立即註冊
            </span>
          </button>
        </form>
        
        <div class="my-6 flex items-center">
          <div class="flex-1 h-px bg-gray-200"></div>
          <span class="px-4 text-gray-400 text-sm">已有帳號？</span>
          <div class="flex-1 h-px bg-gray-200"></div>
        </div>
        
        <div class="text-center">
          <router-link to="/login">
            <button class="w-full py-3 border-2 border-gray-400 text-gray-600 font-semibold rounded-full hover:bg-gray-100 transition-all">
              前往登入
            </button>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';

const router = useRouter();

const formData = ref({
  name: '',
  username: '',
  email: '',
  phone: '',
  password: ''
});

const confirmPassword = ref('');
const showPassword = ref(false);
const showConfirmPassword = ref(false);
const loading = ref(false);
const errorMessage = ref('');
const successMessage = ref('');

const handleRegister = async () => {
  errorMessage.value = '';
  successMessage.value = '';
  
  if (formData.value.password !== confirmPassword.value) {
    errorMessage.value = '兩次密碼輸入不一致';
    return;
  }
  
  if (formData.value.password.length < 6) {
    errorMessage.value = '密碼長度至少需要 6 個字元';
    return;
  }
  
  loading.value = true;
  
  try {
    await api.post('/auth/register', formData.value);
    successMessage.value = '註冊成功！即將跳轉到登入頁面...';
    setTimeout(() => {
      router.push('/login');
    }, 2000);
  } catch (error) {
    errorMessage.value = error.response?.data?.error || '註冊失敗，請稍後再試';
  } finally {
    loading.value = false;
  }
};
</script>
