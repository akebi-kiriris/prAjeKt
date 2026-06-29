<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <div class="mx-auto grid w-full max-w-6xl grid-cols-1 gap-6">
      <header
        class="overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-br from-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]"
      >
        <div class="relative px-5 py-5 md:px-6 md:py-6">
          <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
          <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />
          <div class="relative">
            <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
              PERSONAL TODO
            </p>
            <h1 class="text-[clamp(1.45rem,2.2vw,2rem)] font-black tracking-[0.01em] text-slate-900">待辦事項</h1>
            <p class="mt-2 text-sm leading-6 text-slate-600">追蹤您的計畫與進度。</p>
          </div>
        </div>
      </header>
    
    <!-- Add Button -->
    <div class="text-center">
      <button 
        @click="showAddForm = true"
        class="mx-auto flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)]"
      >
        <span>新增待辦</span>
      </button>
    </div>
    
    <!-- Add/Edit Modal -->
    <div v-if="showAddForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="cancelForm">
      <div class="w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
        <h3 class="mb-6 text-xl font-semibold text-slate-800">{{ editingTodo ? '編輯待辦事項' : '新增待辦事項' }}</h3>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">待辦事項名稱</label>
            <textarea
              v-model="todoForm.title"
              rows="1"
              placeholder="輸入待辦事項名稱"
              class="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              required
            ></textarea>
          </div>

          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">內容</label>
            <textarea
              v-model="todoForm.content"
              rows="4"
              placeholder="輸入待辦事項內容..."
              class="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              required
            ></textarea>
          </div>
          
          <div>
            <label class="mb-2 block text-sm font-semibold text-slate-600">截止日期</label>
            <input 
              v-model="todoForm.deadline" 
              type="datetime-local" 
              class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
            />
          </div>
          
          <div class="flex gap-3 pt-2 ">
            <button type="submit" class="flex-1 rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)]">
              <span>{{ editingTodo ? '更新' : '新增' }}</span>
            </button>
            <button 
              type="button"
              @click="cancelForm"
              class="flex-1 rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              <span>取消</span>
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Todo Lists -->
    <div class="pb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Incomplete -->
      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_26px_rgba(15,23,42,0.06)]">
        <div class="flex items-center justify-between border-b border-slate-200 p-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-slate-800">
            <span>⭕</span>
            未完成
          </h2>
          <span class="rounded-full bg-slate-100 px-3 py-1 text-sm font-semibold text-slate-600">{{ incompleteTodos.length }}</span>
        </div>
        
        <div class="p-4">
          <div v-if="incompleteTodos.length === 0" class="py-12 text-center text-slate-400">
            <span class="text-5xl block mb-4">🎉</span>
            <p>太棒了！沒有待辦事項</p>
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="todo in incompleteTodos" 
              :key="todo.id" 
              class="rounded-xl border border-slate-200 bg-slate-50/70 p-4 transition-all hover:bg-white hover:translate-x-1"
              :class="isOverdue(todo.deadline) ? 'border-red-500' : 'border-primary'"
            >
              <div class="flex items-start gap-3">
                <input 
                  type="checkbox"
                  :checked="todo.completed"
                  @change="toggleTodo(todo.id)"
                  class="mt-1 w-5 h-5 accent-primary cursor-pointer"
                />
                <div class="flex-1 min-w-0">
                  <p class="text-slate-800">{{ todo.title }}</p>
                  <div v-if="todo.deadline" class="mt-2 flex items-center gap-2 text-sm text-slate-500">
                    <span>⏰</span>
                    <span>{{ formatDeadline(todo.deadline) }}</span>
                    <span v-if="isOverdue(todo.deadline)" class="px-2 py-0.5 bg-red-100 text-red-600 rounded-full text-xs">已逾期</span>
                  </div>
                </div>
                <div class="flex gap-2 shrink-0">
                  <button 
                    @click="editTodo(todo)"
                    class="w-8 h-8 rounded-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center transition-colors text-sm"
                  >
                    ✏️
                  </button>
                  <button 
                    @click="deleteTodo(todo.id)"
                    class="w-8 h-8 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors text-sm"
                  >
                    🗑️
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Completed -->
      <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-[0_12px_26px_rgba(15,23,42,0.06)]">
        <div class="flex items-center justify-between border-b border-slate-200 p-4">
          <h2 class="flex items-center gap-2 text-lg font-semibold text-emerald-700">
            <span>✅</span>
            已完成
          </h2>
          <span class="rounded-full bg-emerald-100 px-3 py-1 text-sm font-semibold text-emerald-700">{{ completedTodos.length }}</span>
        </div>

        <div class="p-4">
          <div v-if="completedTodos.length === 0" class="py-12 text-center text-slate-400">
            <span class="text-5xl block mb-4">📋</span>
            <p>尚無已完成的項目</p>
          </div>
          <div v-else class="space-y-3">
            <div
              v-for="todo in completedTodos"
              :key="todo.id"
              class="rounded-xl border border-emerald-200 bg-emerald-50/50 p-4 opacity-80"
            >
              <div class="flex items-start gap-3">
                <input
                  type="checkbox"
                  :checked="todo.completed"
                  @change="toggleTodo(todo.id)"
                  class="mt-1 h-5 w-5 cursor-pointer accent-primary"
                />
                <div class="flex-1 min-w-0">
                  <p class="line-through text-slate-500">{{ todo.title }}</p>
                  <div v-if="todo.deadline" class="mt-2 flex items-center gap-2 text-sm text-slate-400">
                    <span>⏰</span>
                    <span>{{ formatDeadline(todo.deadline) }}</span>
                  </div>
                </div>
                <button
                  @click="deleteTodo(todo.id)"
                  class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-500 text-sm text-white transition-colors hover:bg-red-600"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { toast } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useTodoStore } from '../stores/todos';
import { useConfirm } from '../composables/useConfirm';
import { getApiErrorMessage } from '../utils/apiError';
import type { CreateTodoPayload, UpdateTodoPayload, Todo, TodoForm } from '../types';

const { confirm } = useConfirm();

const store = useTodoStore();

const pad2 = (value: number): string => String(value).padStart(2, '0');

const toLocalDatetimeInputValue = (value: string | null): string => {
  if (!value) return '';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const year = date.getFullYear();
  const month = pad2(date.getMonth() + 1);
  const day = pad2(date.getDate());
  const hour = pad2(date.getHours());
  const minute = pad2(date.getMinutes());
  return `${year}-${month}-${day}T${hour}:${minute}`;
};

const toApiDeadlineValue = (value: string): string | null => {
  if (!value) return null;
  return `${value}:00`;
};

// UI 狀態（留在 View）
const showAddForm = ref(false);
const editingTodo = ref<Todo | null>(null);
const todoForm = ref<TodoForm>({
  title: '',
  content: '',
  deadline: ''
});

// 資料狀態全部來自 store（使用 storeToRefs 保持響應式）
const { incompleteTodos, completedTodos } = storeToRefs(store);

const handleSubmit = async () => {
  try {
    const deadline = toApiDeadlineValue(todoForm.value.deadline);

    const createPayload: CreateTodoPayload = {
      ...todoForm.value,
      deadline: deadline ?? undefined,
    };

    const updatePayload: UpdateTodoPayload = {
      ...todoForm.value,
      deadline,
    };

    if (editingTodo.value) {
      await store.updateTodo(editingTodo.value.id, updatePayload);
    } else {
      await store.addTodo(createPayload);
    }
    cancelForm();
  } catch (error: unknown) {
    console.error('操作失敗:', error);
    toast.error(getApiErrorMessage(error, '操作失敗'));
  }
};

const editTodo = (todo: Todo) => {
  editingTodo.value = todo;
  todoForm.value = {
    title: todo.title,
    content: todo.content,
    deadline: toLocalDatetimeInputValue(todo.deadline),
  };
  showAddForm.value = true;
};

const toggleTodo = async (id: number) => {
  try {
    await store.toggleTodo(id);
  } catch (error: unknown) {
    console.error('更新待辦狀態失敗:', error);
    toast.error(getApiErrorMessage(error, '更新待辦狀態失敗'));
  }
};

const deleteTodo = async (id: number) => {
  if (!await confirm({ title: '確定要刪除此待辦事項？', danger: true })) return;
  try {
    await store.removeTodo(id);
  } catch (error: unknown) {
    console.error('刪除待辦失敗:', error);
    toast.error(getApiErrorMessage(error, '刪除待辦失敗'));
  }
};

const cancelForm = () => {
  showAddForm.value = false;
  editingTodo.value = null;
  todoForm.value = { title: '', content: '', deadline: '' };
};

const formatDeadline = (deadline: string | null) => {
  if (!deadline) return '';
  return new Date(deadline).toLocaleString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
};

const isOverdue = (deadline: string | null) => {
  if (!deadline) return false;
  return new Date(deadline) < new Date();
};

onMounted(() => {
  void store.fetchTodos();
});
</script>
