<template>
  <div class="relative min-h-screen overflow-hidden bg-slate-100 px-4 py-8 sm:px-6">
    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div class="absolute -top-20 -left-16 h-56 w-56 rounded-full bg-primary/15 blur-3xl" />
      <div class="absolute -right-12 bottom-6 h-52 w-52 rounded-full bg-teal-200/35 blur-3xl" />
    </div>

    <div class="relative mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-5xl place-items-center">
      <div class="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-7 shadow-[0_24px_50px_rgba(15,23,42,0.12)] sm:p-8">
        <div class="mb-7">
          <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
            ACCOUNT ACCESS
          </p>
          <h2 class="text-3xl font-black tracking-[0.01em] text-slate-900">歡迎回來</h2>
          <p class="mt-2 text-sm text-slate-500">請登入您的 PrAjeKt 帳號</p>
        </div>

        <form @submit.prevent="handleLogin" class="space-y-5">
          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">Email</label>
            <input
              v-model="formData.email"
              type="email"
              placeholder="請輸入 email"
              class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              required
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">密碼</label>
            <div class="relative">
              <input
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="請輸入密碼"
                class="w-full rounded-xl border border-slate-300 px-4 py-3 pr-16 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                required
              />
              <button
                type="button"
                @click="showPassword = !showPassword"
                class="absolute top-1/2 right-3 -translate-y-1/2 rounded-lg px-2 py-1 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              >
                {{ showPassword ? '隱藏' : '顯示' }}
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600">
            {{ errorMessage }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="flex w-full items-center justify-center rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.26)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ loading ? '登入中...' : '立即登入' }}
          </button>

          <div class="my-5 flex items-center">
            <div class="h-px flex-1 bg-slate-200" />
            <span class="px-3 text-xs text-slate-400">還沒有帳號？</span>
            <div class="h-px flex-1 bg-slate-200" />
          </div>

          <router-link
            to="/register"
            class="flex w-full items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            立即註冊
          </router-link>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../stores/auth';
import type { LoginForm } from '../types';

const router = useRouter();
const authStore = useAuthStore();

const formData = ref<LoginForm>({
  email: '',
  password: '',
});

const errorMessage = ref<string>('');
const loading = ref<boolean>(false);
const showPassword = ref<boolean>(false);

const handleLogin = async (): Promise<void> => {
  loading.value = true;
  errorMessage.value = '';
  
  const result = await authStore.login(formData.value.email, formData.value.password);
  
  if (result.success) {
    router.push('/');
  } else {
    errorMessage.value = result.error || '登入失敗';
  }
  
  loading.value = false;
};
</script>
