<template>
  <div class="h-full w-full bg-gray-50 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-5xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-6xl mb-4 block animate-pulse-custom">📝</span>
      <h1 class="text-4xl font-bold mb-2 text-gray-800">待辦事項</h1>
      <p class="text-lg text-gray-600">追蹤您的計畫與進度</p>
    </div>
    
    <!-- Add Button -->
    <div class="text-center px-4 mb-6">
      <button 
        @click="showAddForm = true"
        class="px-8 py-4 bg-linear-to-r from-primary to-primary-light text-white font-semibold rounded-full shadow-lg hover:-translate-y-0.5 hover:shadow-xl transition-all flex items-center gap-2 mx-auto"
      >
        <span>➕</span>
        <span>新增待辦</span>
      </button>
    </div>
    
    <!-- Add/Edit Modal -->
    <div v-if="showAddForm" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="cancelForm">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 animate-slideUp">
        <h3 class="text-xl font-semibold text-primary mb-6">{{ editingTodo ? '編輯待辦事項' : '新增待辦事項' }}</h3>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">待辦事項名稱</label>
            <textarea
              v-model="todoForm.title"
              rows="1"
              placeholder="輸入待辦事項名稱"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
              required
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">內容</label>
            <textarea
              v-model="todoForm.content"
              rows="4"
              placeholder="輸入待辦事項內容..."
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
              required
            ></textarea>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">截止日期</label>
            <input 
              v-model="todoForm.deadline" 
              type="datetime-local" 
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
          </div>
          
          <div class="flex gap-3 pt-2 ">
            <button 
              type="submit"
              class="flex-1 px-6 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center justify-center gap-2"
              style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
            >
              <span>✓</span>
              <span>{{ editingTodo ? '更新' : '新增' }}</span>
            </button>
            <button 
              type="button"
              @click="cancelForm"
              class="flex-1 px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all flex items-center justify-center gap-2"
            >
              <span>✕</span>
              <span>取消</span>
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Todo Lists -->
    <div class="pb-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
      <!-- Incomplete -->
      <div class="bg-white rounded-2xl shadow-xl overflow-hidden animate-fadeIn">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>⭕</span>
            未完成
          </h2>
          <span class="px-3 py-1 bg-gray-100 text-gray-600 rounded-full text-sm font-semibold">{{ incompleteTodos.length }}</span>
        </div>
        
        <div class="p-4">
          <div v-if="incompleteTodos.length === 0" class="text-center py-12 text-gray-400">
            <span class="text-5xl block mb-4">🎉</span>
            <p>太棒了！沒有待辦事項</p>
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="todo in incompleteTodos" 
              :key="todo.id" 
              class="p-4 bg-gray-50 rounded-xl border-l-4 transition-all hover:bg-gray-100 hover:translate-x-1"
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
                  <p class="text-gray-800">{{ todo.title }}</p>
                  <div v-if="todo.deadline" class="flex items-center gap-2 mt-2 text-sm text-gray-500">
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
      <div class="bg-white rounded-2xl shadow-xl overflow-hidden animate-fadeIn">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-green-600 flex items-center gap-2">
            <span>✅</span>
            已完成
          </h2>
          <span class="px-3 py-1 bg-green-100 text-green-600 rounded-full text-sm font-semibold">{{ completedTodos.length }}</span>
        </div>
        
        <div class="p-4">
          <div v-if="completedTodos.length === 0" class="text-center py-12 text-gray-400">
            <span class="text-5xl block mb-4">📋</span>
            <p>尚無已完成的項目</p>
          </div>
          <div v-else class="space-y-3">
            <div 
              v-for="todo in completedTodos" 
              :key="todo.id" 
              class="p-4 bg-gray-50 rounded-xl border-l-4 border-green-500 opacity-75"
            >
              <div class="flex items-start gap-3">
                <input 
                  type="checkbox"
                  :checked="todo.completed"
                  @change="toggleTodo(todo.id)"
                  class="mt-1 w-5 h-5 accent-primary cursor-pointer"
                />
                <div class="flex-1 min-w-0">
                  <p class="text-gray-500 line-through">{{ todo.title }}</p>
                  <div v-if="todo.deadline" class="flex items-center gap-2 mt-2 text-sm text-gray-400">
                    <span>⏰</span>
                    <span>{{ formatDeadline(todo.deadline) }}</span>
                  </div>
                </div>
                <button 
                  @click="deleteTodo(todo.id)"
                  class="w-8 h-8 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors text-sm shrink-0"
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

<script setup>
import { ref, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useTodoStore } from '../stores/todos';
import { useConfirm } from '../composables/useConfirm';

const { confirm } = useConfirm();

const store = useTodoStore();

// UI 狀態（留在 View）
const showAddForm = ref(false);
const editingTodo = ref(null);
const todoForm = ref({
  title: '',
  content: '',
  deadline: ''
});

// 資料狀態全部來自 store（使用 storeToRefs 保持響應式）
const { incompleteTodos, completedTodos } = storeToRefs(store);

const handleSubmit = async () => {
  try {
    const formData = {
      ...todoForm.value,
      deadline: todoForm.value.deadline ? todoForm.value.deadline + ':00' : null
    };

    if (editingTodo.value) {
      await store.updateTodo(editingTodo.value.id, formData);
    } else {
      await store.addTodo(formData);
    }
    cancelForm();
  } catch (error) {
    console.error('操作失敗:', error);
  }
};

const editTodo = (todo) => {
  editingTodo.value = todo;
  todoForm.value = {
    title: todo.title,
    content: todo.content,
    deadline: todo.deadline ? new Date(todo.deadline).toISOString().slice(0, 16) : ''
  };
  showAddForm.value = true;
};

const toggleTodo = (id) => store.toggleTodo(id);

const deleteTodo = async (id) => {
  if (!await confirm({ title: '確定要刪除此待辦事項？', danger: true })) return;
  await store.removeTodo(id);
};

const cancelForm = () => {
  showAddForm.value = false;
  editingTodo.value = null;
  todoForm.value = { title: '', content: '', deadline: '' };
};

const formatDeadline = (deadline) => {
  if (!deadline) return '';
  return new Date(deadline).toLocaleString('zh-TW', {
    year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit'
  });
};

const isOverdue = (deadline) => {
  if (!deadline) return false;
  return new Date(deadline) < new Date();
};

onMounted(() => store.fetchTodos());
</script>
