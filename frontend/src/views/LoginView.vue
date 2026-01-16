<template>
  <div class="min-h-screen flex justify-center items-center p-8 bg-linear-to-br from-emerald-400 to-teal-600 relative overflow-hidden">
    <!-- 裝飾用圈圈 -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="absolute w-72 h-72 bg-white/10 rounded-full -top-24 -left-24 animate-float"></div>
      <div class="absolute w-48 h-48 bg-white/10 rounded-full -bottom-12 -right-12 animate-float" style="animation-delay: 5s"></div>
      <div class="absolute w-36 h-36 bg-white/10 rounded-full top-1/2 right-[10%] animate-float" style="animation-delay: 10s"></div>
    </div>
    
    <div class="w-full max-w-3xl relative z-10 bg-white/95 rounded-3xl shadow-2xl backdrop-blur-sm animate-slideUp" style="padding: 5px;">
      <div class="p-10">
        <div class="text-center mb-8">
          <h2 class="text-5xl font-bold gradient-text mb-2">歡迎回來</h2>
          <p class="text-gray-500">請登入您的 prAjeKt 帳號</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="space-y-6">
          <div>
            <label class="block text-lg font-semibold text-gray-600 mb-2">Email</label>
            <input 
              v-model="formData.email" 
              type="email" 
              placeholder="請輸入 email"
              class="w-full pr-4 py-3 border border-gray-300 rounded-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              required
            />
          </div>
          
          <div>
            <label class="block text-lg font-semibold text-gray-600 mb-2">密碼</label>
            <div class="relative">
              <input 
                v-model="formData.password" 
                :type="showPassword ? 'text' : 'password'" 
                placeholder="請輸入密碼"
                class="w-full pr-12 py-3 border border-gray-300 rounded-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
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
          
          <div v-if="errorMessage" class="p-3 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm">
            {{ errorMessage }}
          </div>
          
          <button 
            type="submit" 
            :disabled="loading"
            class="w-full py-4 font-bold text-lg rounded-lg border-4 shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
          >
            <span v-if="loading">登入中...</span>
            <span v-else class="flex items-center justify-center gap-2">
              ➡️ 立即登入
            </span>
          </button>
         </form>
        
        <div class="my-6 flex items-center">
          <div class="flex-1 h-px bg-gray-200"></div>
          <span class="px-4 text-gray-400 text-sm">還沒有帳號？</span>
          <div class="flex-1 h-px bg-gray-200"></div>
        </div>
        
        <div class="text-center mb-4">
          <router-link to="/register">
            <button class="w-full py-3 border-2 text-lg border-green-500 text-green-500 font-semibold rounded-lg hover:bg-green-500 hover:text-white transition-all">
              立即註冊
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
import { useAuthStore } from '../stores/auth';

const router = useRouter();
const authStore = useAuthStore();

const formData = ref({
  email: '',
  password: '',
});

const errorMessage = ref('');
const loading = ref(false);
const showPassword = ref(false);

const handleLogin = async () => {
  loading.value = true;
  errorMessage.value = '';
  
  const result = await authStore.login(formData.value.email, formData.value.password);
  
  if (result.success) {
    router.push('/');
  } else {
    errorMessage.value = result.error;
  }
  
  loading.value = false;
};
</script>
