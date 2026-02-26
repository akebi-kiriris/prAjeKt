<template>
  <div class="h-full w-full bg-gray-50 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-4xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-6xl mb-4 block animate-pulse-custom">✅</span>
      <h1 class="text-4xl font-bold mb-2 text-gray-800">任務管理</h1>
      <p class="text-lg text-gray-600">管理您的任務與進度</p>
      <button
        @click="showForm = true"
        class="mt-4 px-6 py-3 bg-primary text-white border-4 border-primary font-bold text-lg rounded-xl shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all inline-flex items-center gap-2"
      >
        <span>＋</span>
        <span>新增任務</span>
      </button>
    </div>

    <!-- Modal -->
    <Teleport to="body">
      <div
        v-if="showForm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="cancelEdit"
      >
        <div class="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-lg mx-4 animate-slideUp">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-2 text-primary font-semibold text-xl">
              <span>✏️</span>
              <span>{{ editingTask ? '編輯任務' : '新增任務' }}</span>
            </div>
            <button @click="cancelEdit" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">✕</button>
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
    </Teleport>
    
    <!-- 成員管理 Panel -->
    <Teleport to="body">
      <div
        v-if="isSharePanelOpen"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="isSharePanelOpen = false"
      >
        <div class="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md mx-4 animate-slideUp">
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-2 text-primary font-semibold text-xl">
              <span>👥</span>
              <span>成員管理 — {{ shareTask?.name }}</span>
            </div>
            <button @click="isSharePanelOpen = false" class="text-gray-400 hover:text-gray-600 text-2xl leading-none">✕</button>
          </div>

          <!-- 現有成員列表 -->
          <div class="space-y-2 mb-4">
            <p class="text-sm font-semibold text-gray-500 mb-2">目前成員</p>
            <div
              v-for="member in taskMembers"
              :key="member.user_id"
              class="flex items-center justify-between gap-3 py-2 px-3 rounded-xl hover:bg-gray-50"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-sm">
                  {{ member.name?.charAt(0) || '?' }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-800">{{ member.name }}</p>
                  <p class="text-xs text-gray-400">{{ member.email }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span
                  :class="member.role === 0 ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-500'"
                  class="text-xs px-2 py-0.5 rounded-full font-medium"
                >
                  {{ member.role === 0 ? '負責人' : '協作者' }}
                </span>
                <button
                  v-if="member.role !== 0"
                  @click="kickTaskMember(member)"
                  class="text-gray-300 hover:text-red-500 text-lg leading-none transition-colors"
                  title="移除成員"
                >✕</button>
              </div>
            </div>
          </div>

          <!-- 邀請新成員 -->
          <div class="border-t pt-4">
            <p class="text-sm font-semibold text-gray-500 mb-3">邀請協作者</p>
            <div class="flex gap-2">
              <input
                v-model="shareInputEmail"
                type="email"
                placeholder="輸入 Email 搜尋使用者"
                @keyup.enter="searchShareUser"
                class="flex-1 px-3 py-2 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
              />
              <button
                @click="searchShareUser"
                class="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-xl text-sm transition-colors"
              >搜尋</button>
            </div>
            <p v-if="shareSearchError" class="text-red-500 text-xs mt-2">{{ shareSearchError }}</p>

            <!-- 搜尋結果 -->
            <div v-if="shareSearchResult" class="mt-3 flex items-center justify-between gap-3 p-3 bg-gray-50 rounded-xl">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-sm">
                  {{ shareSearchResult.name?.charAt(0) || '?' }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-gray-800">{{ shareSearchResult.name }}</p>
                  <p class="text-xs text-gray-400">{{ shareSearchResult.email }}</p>
                </div>
              </div>
              <button
                @click="confirmShare"
                class="px-4 py-2 bg-primary text-white font-semibold rounded-xl text-sm hover:bg-primary/90 transition-colors"
              >邀請</button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

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
                v-if="task.is_owner"
                @click="openSharePanel(task)"
                class="w-10 h-10 rounded-full bg-indigo-500 hover:bg-indigo-600 text-white flex items-center justify-center transition-colors"
                title="成員管理"
              >
                👥
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
import { ref, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useTaskStore } from '../stores/tasks';
import { taskService } from '../services/taskService';

const store = useTaskStore();
const { tasks } = storeToRefs(store);

// UI state (stays in View)
const showForm = ref(false);
const editingTask = ref(null);
const taskForm = ref({
  name: '',
  start_date: '',
  end_date: '',
  task_remark: ''
});

const handleSubmit = async () => {
  try {
    if (editingTask.value) {
      await store.updateTask(editingTask.value.task_id, taskForm.value);
    } else {
      await store.addTask(taskForm.value);
    }
    resetForm();
  } catch (error) {
    console.error('儲存任務失敗:', error);
  }
};

const editTask = (task) => {
  editingTask.value = task;

  taskForm.value = {
    name: task.name,
    start_date: task.start_date ? task.start_date.slice(0, 10) : '',
    end_date: task.end_date ? task.end_date.slice(0, 10) : '',
    task_remark: task.task_remark || ''
  };
  showForm.value = true;
};

const cancelEdit = () => {
  resetForm();
};

const deleteTask = async (taskId) => {
  if (!confirm('確定要刪除此任務？')) return;
  try {
    await store.removeTask(taskId);
  } catch (error) {
    console.error('刪除任務失敗:', error);
  }
};

const toggleTask = async (task) => {
  try {
    await store.toggleTask(task.task_id);
  } catch (error) {
    console.error('更新任務狀態失敗:', error);
  }
};

const resetForm = () => {
  editingTask.value = null;
  showForm.value = false;
  taskForm.value = {
    name: '',
    start_date: '',
    end_date: '',
    task_remark: ''
  };
};

// ===== 成員管理 =====
const shareTask = ref(null);
const isSharePanelOpen = ref(false);
const taskMembers = ref([]);
const shareInputEmail = ref('');
const shareSearchResult = ref(null);
const shareSearchError = ref('');

const openSharePanel = async (task) => {
  shareTask.value = task;
  isSharePanelOpen.value = true;
};

watch(isSharePanelOpen, async (val) => {
  if (val && shareTask.value) {
    await loadTaskMembers();
  } else {
    shareInputEmail.value = '';
    shareSearchResult.value = null;
    shareSearchError.value = '';
  }
});

const loadTaskMembers = async () => {
  try {
    const res = await taskService.getMembers(shareTask.value.task_id);
    taskMembers.value = res.data;
  } catch (e) {
    console.error('載入成員失敗', e);
  }
};

const searchShareUser = async () => {
  shareSearchResult.value = null;
  shareSearchError.value = '';
  if (!shareInputEmail.value.trim()) return;
  try {
    const res = await taskService.searchUser(shareInputEmail.value.trim());
    const found = res.data.user;
    const alreadyIn = taskMembers.value.some(m => m.user_id === found.id);
    if (alreadyIn) { shareSearchError.value = '此使用者已是成員'; return; }
    shareSearchResult.value = found;
  } catch (e) {
    shareSearchError.value = e.response?.data?.error || '找不到使用者';
  }
};

const confirmShare = async () => {
  if (!shareSearchResult.value) return;
  try {
    await taskService.addMember(shareTask.value.task_id, shareSearchResult.value.id);
    shareInputEmail.value = '';
    shareSearchResult.value = null;
    await loadTaskMembers();
    await store.fetchTasks();
  } catch (e) {
    shareSearchError.value = e.response?.data?.error || '新增失敗';
  }
};

const kickTaskMember = async (member) => {
  if (!confirm(`確定要移除「${member.name}」？`)) return;
  try {
    await taskService.removeMember(shareTask.value.task_id, member.user_id);
    await loadTaskMembers();
    await store.fetchTasks();
  } catch (e) {
    alert(e.response?.data?.error || '移除失敗');
  }
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

onMounted(() => {
  store.fetchTasks();
});
</script>
