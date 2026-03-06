<template>
  <TransitionRoot :show="dialogState !== null" as="template">
    <Dialog @close="handleCancel" class="relative z-9999">
      <!-- 背景遮罩 -->
      <TransitionChild
        enter="ease-out duration-200" enter-from="opacity-0" enter-to="opacity-100"
        leave="ease-in duration-150" leave-from="opacity-100" leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/40" />
      </TransitionChild>

      <!-- Modal 面板 -->
      <div class="fixed inset-0 flex items-center justify-center p-4">
        <TransitionChild
          enter="ease-out duration-200" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
          leave="ease-in duration-150" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95"
        >
          <DialogPanel class="w-full max-w-sm bg-white rounded-2xl shadow-xl p-6">
            <!-- 圖示 -->
            <div class="flex items-center gap-3 mb-3">
              <div
                class="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                :class="dialogState?.danger ? 'bg-red-100' : 'bg-yellow-100'"
              >
                <span class="text-lg">{{ dialogState?.danger ? '🗑️' : '❓' }}</span>
              </div>
              <DialogTitle class="text-base font-semibold text-gray-800">
                {{ dialogState?.title }}
              </DialogTitle>
            </div>

            <!-- 補充說明（選填）-->
            <p v-if="dialogState?.message" class="text-sm text-gray-500 mb-5 ml-13">
              {{ dialogState.message }}
            </p>
            <div v-else class="mb-5" />

            <!-- 按鈕列 -->
            <div class="flex justify-end gap-2">
              <button
                @click="handleCancel"
                class="px-4 py-2 text-sm rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
              >
                取消
              </button>
              <button
                @click="handleConfirm"
                class="px-4 py-2 text-sm rounded-lg text-white font-medium transition-colors"
                :class="dialogState?.danger
                  ? 'bg-red-500 hover:bg-red-600'
                  : 'bg-blue-500 hover:bg-blue-600'"
              >
                確認
              </button>
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup>
import {
  TransitionRoot, TransitionChild,
  Dialog, DialogPanel, DialogTitle,
} from '@headlessui/vue';
import { dialogState } from '../composables/useConfirm';

function handleConfirm() {
  dialogState.value?.resolve(true);
  dialogState.value = null;
}

function handleCancel() {
  dialogState.value?.resolve(false);
  dialogState.value = null;
}
</script>
