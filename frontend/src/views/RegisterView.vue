<template>
  <div class="relative min-h-screen overflow-hidden bg-slate-100 px-4 py-8 sm:px-6">
    <div class="pointer-events-none absolute inset-0 overflow-hidden">
      <div class="absolute -top-24 -left-14 h-60 w-60 rounded-full bg-primary/15 blur-3xl" />
      <div class="absolute -right-14 bottom-4 h-64 w-64 rounded-full bg-cyan-200/35 blur-3xl" />
    </div>

    <div class="relative mx-auto grid min-h-[calc(100vh-4rem)] w-full max-w-5xl place-items-center">
      <div class="w-full max-w-xl rounded-3xl border border-slate-200 bg-white p-7 shadow-[0_24px_50px_rgba(15,23,42,0.12)] sm:p-8">
        <div class="mb-7">
          <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
            ACCOUNT CREATE
          </p>
          <h2 class="text-3xl font-black tracking-[0.01em] text-slate-900">建立新帳號</h2>
          <p class="mt-2 text-sm text-slate-500">加入 PrAjeKt 開始專案管理</p>
        </div>

        <form @submit.prevent="handleRegister" class="space-y-5">
          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">姓名 *</label>
            <input
              v-model="formData.name"
              type="text"
              placeholder="請輸入姓名"
              class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              required
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">用戶名（選填）</label>
            <input
              v-model="formData.username"
              type="text"
              placeholder="請輸入唯一用戶名，如：john_doe"
              class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
            />
            <p class="mt-1 text-xs text-slate-500">用戶名可用於搜尋和標註，留空則使用 Email</p>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">Email *</label>
            <input
              v-model="formData.email"
              type="email"
              placeholder="請輸入 email"
              class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              required
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">電話</label>
            <input
              v-model="formData.phone"
              type="tel"
              placeholder="請輸入電話"
              class="w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
            />
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">密碼 *</label>
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

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">確認密碼 *</label>
            <div class="relative">
              <input
                v-model="confirmPassword"
                :type="showConfirmPassword ? 'text' : 'password'"
                placeholder="請再次輸入密碼"
                class="w-full rounded-xl border border-slate-300 px-4 py-3 pr-16 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                required
              />
              <button
                type="button"
                @click="showConfirmPassword = !showConfirmPassword"
                class="absolute top-1/2 right-3 -translate-y-1/2 rounded-lg px-2 py-1 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
              >
                {{ showConfirmPassword ? '隱藏' : '顯示' }}
              </button>
            </div>
          </div>

          <div v-if="errorMessage" class="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-600">
            {{ errorMessage }}
          </div>

          <div v-if="successMessage" class="rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">
            {{ successMessage }}
          </div>

          <button
            type="submit"
            :disabled="loading"
            class="flex w-full items-center justify-center rounded-xl bg-primary px-4 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.26)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {{ loading ? '註冊中...' : '立即註冊' }}
          </button>

          <div class="my-5 flex items-center">
            <div class="h-px flex-1 bg-slate-200" />
            <span class="px-3 text-xs text-slate-400">已有帳號？</span>
            <div class="h-px flex-1 bg-slate-200" />
          </div>

          <router-link
            to="/login"
            class="flex w-full items-center justify-center rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            前往登入
          </router-link>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/api';
import { getApiErrorMessage } from '../utils/apiError';
import type { RegisterForm } from '../types';

const router = useRouter();

const formData = ref<RegisterForm>({
  name: '',
  username: '',
  email: '',
  phone: '',
  password: ''
});

const confirmPassword = ref<string>('');
const showPassword = ref<boolean>(false);
const showConfirmPassword = ref<boolean>(false);
const loading = ref<boolean>(false);
const errorMessage = ref<string>('');
const successMessage = ref<string>('');

const handleRegister = async (): Promise<void> => {
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
  } catch (error: unknown) {
    errorMessage.value = getApiErrorMessage(error, '註冊失敗，請稍後再試');
  } finally {
    loading.value = false;
  }
};
</script>
