<template>
  <div class="h-full w-full bg-gray-50 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-6xl mb-4 block animate-pulse-custom">✅</span>
      <h1 class="text-4xl font-bold mb-2 text-gray-800">任務管理</h1>
      <p class="text-lg text-gray-600">管理您的任務與進度</p>
    </div>
    
    <!-- Task Form -->
    <div class="animate-slideUp">
      <div class="bg-white rounded-2xl shadow-xl p-6">
        <div class="flex items-center gap-2 text-primary font-semibold text-xl mb-6 ">
          <span>✏️</span>
          <span>{{ editingTask ? '編輯任務' : '新增任務' }}</span>
        </div>
        
        <form @submit.prevent="handleSubmit" class="space-y-4">
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">任務名稱 *</label>
              <input 
                v-model="taskForm.name" 
                type="text" 
                placeholder="請輸入任務名稱"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
            
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">快速筆記（選填）</label>
              <input 
                v-model="taskForm.assistant" 
                type="text" 
                placeholder="快速記錄協助者或相關資訊"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
              <p class="text-xs text-gray-500 mt-1">快速筆記，不會關聯實際使用者</p>
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">開始日期</label>
              <input 
                v-model="taskForm.start_date" 
                type="date" 
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
            </div>
            
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">截止日期 *</label>
              <input 
                v-model="taskForm.end_date" 
                type="date" 
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
          </div>

          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">備註</label>
            <textarea
              v-model="taskForm.task_remark"
              rows="3"
              placeholder="輸入任務備註..."
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
            ></textarea>
          </div>

          <div class="flex gap-3">
            <button 
              type="submit"
              class="px-6 py-3 bg-primary text-white border-4 border-primary font-bold text-lg rounded-xl shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center gap-2"
            >
              <span>✓</span>
              <span>{{ editingTask ? '更新任務' : '新增任務' }}</span>
            </button>
            <button 
              v-if="editingTask"
              type="button"
              @click="cancelEdit"
              class="px-6 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all flex items-center gap-2"
            >
              <span>✕</span>
              <span>取消</span>
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Task List -->
    <div class="pb-8">
      <div class="space-y-4">
        <div 
          v-for="task in tasks" 
          :key="task.task_id" 
          class="bg-white rounded-xl shadow-md hover:-translate-y-1 hover:shadow-xl transition-all animate-fadeIn"
          :class="{ 'opacity-70 bg-gray-50': task.completed }"
        >
          <div class="p-5 flex justify-between items-start gap-4">
            <div class="flex-1">
              <h3 class="text-xl font-semibold text-primary flex items-center gap-2 mb-2">
                <span v-if="task.completed" class="text-green-500 text-2xl">✓</span>
                {{ task.name }}
              </h3>
              <div class="flex flex-wrap gap-4 text-sm text-gray-600 mb-2">
                <span v-if="task.members && task.members.length" class="flex items-center gap-1">
                  <span>👥</span>
                  成員: {{ task.members.map(m => m.name || 'User').join(', ') }}
                </span>
                <span v-if="task.assistant" class="flex items-center gap-1">
                  <span>📝</span>
                  筆記: {{ Array.isArray(task.assistant) ? task.assistant.join(', ') : task.assistant }}
                </span>
                <span class="flex items-center gap-1">
                  <span>📅</span>
                  {{ formatDate(task.end_date) }}
                </span>
              </div>
              <p v-if="task.task_remark" class="text-gray-500 text-sm">{{ task.task_remark }}</p>
            </div>
            
            <div class="flex gap-2 shrink-0">
              <button 
                @click="toggleTask(task)"
                :class="task.completed ? 'bg-yellow-500 hover:bg-yellow-600' : 'bg-green-500 hover:bg-green-600'"
                class="w-10 h-10 rounded-full text-white flex items-center justify-center transition-colors"
                :title="task.completed ? '標記未完成' : '標記完成'"
              >
                ✓
              </button>
              <button 
                @click="editTask(task)"
                class="w-10 h-10 rounded-full bg-blue-500 hover:bg-blue-600 text-white flex items-center justify-center transition-colors"
                title="編輯"
              >
                ✏️
              </button>
              <button 
                @click="deleteTask(task.task_id)"
                class="w-10 h-10 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors"
                title="刪除"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
        
        <div v-if="tasks.length === 0" class="text-center py-16">
          <span class="text-6xl block mb-4">📋</span>
          <p class="text-xl text-gray-500">目前沒有任務</p>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const tasks = ref([]);
const editingTask = ref(null);
const taskForm = ref({
  name: '',
  assistant: '',
  start_date: '',
  end_date: '',
  task_remark: ''
});

const fetchTasks = async () => {
  try {
    const response = await api.get('/tasks');
    tasks.value = response.data;
  } catch (error) {
    console.error('取得任務失敗:', error);
  }
};

const handleSubmit = async () => {
  try {
    const assistantArray = taskForm.value.assistant 
      ? taskForm.value.assistant.split(',').map(s => s.trim()).filter(s => s)
      : [];
    
    const formData = {
      ...taskForm.value,
      assistant: assistantArray,
      start_date: taskForm.value.start_date || null,
      end_date: taskForm.value.end_date || null,
    };
    
    if (editingTask.value) {
      await api.put(`/tasks/${editingTask.value.task_id}`, formData);
    } else {
      await api.post('/tasks', formData);
    }
    await fetchTasks();
    resetForm();
  } catch (error) {
    console.error('儲存任務失敗:', error);
  }
};

const editTask = (task) => {
  editingTask.value = task;
  const assistantStr = task.assistant 
    ? (Array.isArray(task.assistant) ? task.assistant.join(', ') : task.assistant)
    : '';
  
  taskForm.value = {
    name: task.name,
    assistant: assistantStr,
    start_date: task.start_date || '',
    end_date: task.end_date || '',
    task_remark: task.task_remark || ''
  };
};

const cancelEdit = () => {
  resetForm();
};

const deleteTask = async (taskId) => {
  if (!confirm('確定要刪除此任務？')) return;
  try {
    await api.delete(`/tasks/${taskId}`);
    await fetchTasks();
  } catch (error) {
    console.error('刪除任務失敗:', error);
  }
};

const toggleTask = async (task) => {
  try {
    await api.patch(`/tasks/${task.task_id}/toggle`);
    await fetchTasks();
  } catch (error) {
    console.error('更新任務狀態失敗:', error);
  }
};

const resetForm = () => {
  editingTask.value = null;
  taskForm.value = {
    name: '',
    assistant: '',
    start_date: '',
    end_date: '',
    task_remark: ''
  };
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

onMounted(() => {
  fetchTasks();
});
</script>
