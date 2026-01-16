<template>
  <div class="h-full w-full bg-gray-50 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-6xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-8 pb-4 px-4 animate-slideDown">
      <span class="text-6xl mb-4 block animate-pulse-custom">📊</span>
      <h1 class="text-4xl font-bold mb-2 text-gray-800">專案管理</h1>
      <p class="text-lg text-gray-600">建立專案、分配任務、追蹤進度</p>
    </div>
    
    <!-- Action Bar -->
    <div class="text-center px-4 mb-6">
      <button 
        @click="showCreateModal = true"
        class="
              group relative w-full h-12 
              flex items-center justify-center gap-3 px-6 py-3 
              bg-linear-to-b from-primary to-primary-dark
              border border-white/10 
              text-white font-bold tracking-wide rounded-xl 
              shadow-[0_4px_10px_rgba(0,0,0,0.5)] 
              hover:shadow-black/40 
              hover:border-white/20
              hover:-translate-y-0.5 active:scale-95 
              transition-all duration-300 ease-out 
              overflow-hidden
            "
      >
    <div class="absolute inset-0 bg-white/10 translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out skew-x-12"></div>
    <span class="text-sm drop-shadow-md">➕</span>
    <span class="drop-shadow-md">新增專案</span>
      </button>
    </div>
    
    <!-- Create/Edit Project Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>📁</span>
            {{ editingTimeline ? '編輯專案' : '新增專案' }}
          </h2>
          <button @click="closeModal" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>
        
        <form @submit.prevent="handleSubmit" class="p-6 space-y-4">
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">專案名稱 *</label>
            <div class="relative">
              <input 
                v-model="timelineForm.name" 
                type="text" 
                placeholder="請輸入專案名稱"
                class="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">開始日期</label>
                <input 
                  v-model="timelineForm.start_date" 
                  type="date" 
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">結束日期</label>
                <input 
                  v-model="timelineForm.end_date" 
                  type="date" 
                  class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">顏色主題</label>
            <div class="flex items-center gap-4">
              <input 
                v-model="timelineForm.color" 
                type="color" 
                class="w-12 h-12 rounded-lg cursor-pointer border-0"
              />
              <span class="font-mono text-gray-600">{{ timelineForm.color }}</span>
            </div>
          </div>
          
          <div class="flex gap-3 pt-4">
            <button 
              type="submit"
              class="flex-1 py-3 font-bold text-lg rounded-xl border-4 shadow-xl hover:-translate-y-0.5 hover:shadow-2xl transition-all flex items-center justify-center gap-2"
              style="background: var(--color-primary); color: #fff; border-color: var(--color-primary);"
            >
              <span>✓</span>
              {{ editingTimeline ? '更新' : '新增' }}
            </button>
            <button 
              type="button"
              @click="closeModal"
              class="flex-1 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all flex items-center justify-center gap-2"
            >
              <span>✕</span>
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Timeline Grid -->
    <div class="pb-8">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div 
          v-for="timeline in timelines" 
          :key="timeline.id"
          @click="viewTimeline(timeline)"
          class="bg-white rounded-2xl shadow-lg hover:-translate-y-1 hover:shadow-xl transition-all cursor-pointer animate-fadeIn overflow-hidden"
        >
          <div class="p-6">
            <div class="flex justify-between items-start mb-4">
              <h3 class="text-lg font-semibold text-primary flex items-center gap-2 flex-1">
                <span class="text-2xl">📁</span>
                {{ timeline.name }}
              </h3>
              <div class="flex gap-2" @click.stop>
                <button 
                  @click="editTimeline(timeline)"
                  class="w-8 h-8 flex items-center justify-center text-primary hover:bg-primary/10 rounded-lg transition-colors"
                  title="編輯"
                >✏️</button>
                <button 
                  @click="deleteTimeline(timeline.id)"
                  class="w-8 h-8 flex items-center justify-center text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  title="刪除"
                >🗑️</button>
              </div>
            </div>
            
            <!-- Progress Bar -->
            <div class="mb-4">
              <div class="flex justify-between text-sm text-gray-500 mb-1">
                <span>進度</span>
                <span>{{ timeline.progress || 0 }}%</span>
              </div>
              <div class="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  class="h-full rounded-full transition-all duration-500"
                  :style="{ width: (timeline.progress || 0) + '%', backgroundColor: timeline.color || '#11998e' }"
                ></div>
              </div>
            </div>
            
            <div class="space-y-2 text-sm text-gray-600">
              <p class="flex items-center gap-2">
                <span>📅</span>
                {{ formatDate(timeline.startDate) }} ~ {{ formatDate(timeline.endDate) }}
              </p>
              <p class="flex items-center gap-2">
                <span>✅</span>
                {{ timeline.completedTasks || 0 }} / {{ timeline.totalTasks || 0 }} 任務完成
              </p>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-if="timelines.length === 0" class="text-center py-16">
        <span class="text-6xl block mb-4">📁</span>
        <p class="text-xl text-gray-600">目前尚無專案</p>
        <p class="text-sm text-gray-500 mt-2">點擊「新增專案」來建立您的第一個專案</p>
      </div>
    </div>
    
    <!-- Detail Dialog -->
    <div v-if="selectedTimeline" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>📁</span>
            {{ selectedTimeline.name }}
          </h2>
          <button @click="selectedTimeline = null" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>
        
        <div class="p-6">
          <!-- Project Actions -->
          <div class="flex flex-wrap gap-3 mb-6 justify-center">
            <button 
              @click="showAddTaskModal = true"
              class="px-4 py-2 bg-linear-to-r from-primary to-primary-light text-white rounded-lg hover:-translate-y-0.5 hover:shadow-lg transition-all flex items-center gap-2"
            >
              <span>➕</span>
              新增任務
            </button>
            <button 
              @click="isSharePanelOpen = true"
              class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <span>👤</span>
              邀請成員
            </button>
            <button 
              @click="isEditingRemark = !isEditingRemark"
              class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors flex items-center gap-2"
            >
              <span>✏️</span>
              {{ isEditingRemark ? '取消編輯' : '編輯備註' }}
            </button>
          </div>
          
          <!-- Remark Section -->
          <div v-if="isEditingRemark" class="mb-6">
            <textarea 
              v-model="newRemark"
              rows="3"
              placeholder="輸入專案備註..."
              @blur="updateRemark"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
            ></textarea>
          </div>
          <div v-else-if="selectedTimeline?.remark" class="mb-6 p-4 bg-gray-50 rounded-xl">
            <p><strong class="text-gray-700">備註：</strong>{{ selectedTimeline.remark }}</p>
          </div>
          
          <!-- Tasks Section -->
          <div>
            <h3 class="text-lg font-semibold text-primary flex items-center gap-2 mb-4">
              <span>📋</span>
              專案任務 ({{ timelineTasks.length }})
            </h3>
            
            <div class="space-y-3 max-h-[50vh] overflow-y-auto">
              <div 
                v-for="task in timelineTasks" 
                :key="task.task_id"
                @click="viewTaskDetail(task)"
                class="p-4 bg-gray-50 rounded-xl border-l-4 border-primary cursor-pointer hover:bg-gray-100 transition-colors"
              >
                <div class="flex items-start gap-3">
                  <input 
                    type="checkbox"
                    :checked="task.completed"
                    @click.stop="toggleTask(task.task_id)"
                    class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary mt-1 cursor-pointer"
                  />
                  <div class="flex-1">
                    <span :class="{ 'line-through text-gray-400': task.completed }" class="font-medium">
                      {{ task.isWork ? '🛠️' : '📌' }} {{ task.name }}
                    </span>
                    <div class="flex flex-wrap gap-4 mt-2 text-sm text-gray-500">
                      <span v-if="task.members && task.members.length" class="flex items-center gap-1">
                        <span>�</span>
                        成員: {{ task.members.map(m => m.name || 'User').join(', ') }}
                      </span>
                      <span v-if="task.assistant" class="flex items-center gap-1">
                        📝 筆記: {{ Array.isArray(task.assistant) ? task.assistant.join(', ') : task.assistant }}
                      </span>
                      <span class="flex items-center gap-1">
                        <span>📅</span>
                        {{ formatDate(task.end_date) }}
                      </span>
                    </div>
                  </div>
                  <button 
                    @click.stop="deleteTask(task.task_id)"
                    class="text-red-400 hover:text-red-600 transition-colors"
                    title="刪除任務"
                  >🗑️</button>
                </div>
              </div>
              
              <div v-if="timelineTasks.length === 0" class="text-center py-12 text-gray-400">
                <span class="text-4xl block mb-4">📋</span>
                <p>此專案尚無任務</p>
                <p class="text-sm mt-2">點擊「新增任務」來建立任務</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Add Task Modal -->
    <div v-if="showAddTaskModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>📌</span>
            新增任務
          </h2>
          <button @click="showAddTaskModal = false; resetTaskForm()" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>
        
        <form @submit.prevent="handleAddTask" class="p-6 space-y-4">
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
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">開始日期</label>
              <input 
                v-model="taskForm.start_date" 
                type="datetime-local" 
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">截止日期 *</label>
              <input 
                v-model="taskForm.end_date" 
                type="datetime-local" 
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">備註</label>
            <textarea 
              v-model="taskForm.task_remark" 
              rows="2"
              placeholder="任務備註..."
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none"
            ></textarea>
          </div>
          
          <div class="flex items-center gap-2">
            <input 
              type="checkbox" 
              v-model="taskForm.isWork" 
              id="isWork"
              class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
            />
            <label for="isWork" class="text-sm text-gray-600">標記為工作任務 🛠️</label>
          </div>
          
          <div class="flex gap-3 pt-4">
            <button 
              type="submit"
              class="flex-1 py-3 bg-linear-to-r from-primary to-primary-light text-white font-semibold rounded-xl hover:-translate-y-0.5 hover:shadow-lg transition-all flex items-center justify-center gap-2"
            >
              <span>✓</span>
              新增任務
            </button>
            <button 
              type="button"
              @click="showAddTaskModal = false; resetTaskForm()"
              class="flex-1 py-3 bg-gray-200 text-gray-700 font-semibold rounded-xl hover:bg-gray-300 transition-all flex items-center justify-center gap-2"
            >
              <span>✕</span>
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Share Panel -->
    <div v-if="isSharePanelOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md animate-slideUp">
        <div class="p-4 border-b flex justify-between items-center">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>👤</span>
            邀請成員
          </h2>
          <button @click="isSharePanelOpen = false" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>
        
        <div class="p-6">
          <div class="flex gap-2">
            <input 
              v-model="inputEmail"
              placeholder="請輸入使用者 Email"
              @keyup.enter="searchUser"
              class="flex-1 px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
            <button 
              @click="searchUser"
              class="px-4 py-3 bg-primary text-white rounded-xl hover:bg-primary-dark transition-colors"
            >查詢</button>
          </div>
          
          <div v-if="searchResult" class="mt-4 p-4 bg-blue-50 rounded-xl">
            <p class="font-semibold mb-2">查詢結果：</p>
            <p class="text-gray-600">ID: {{ searchResult.id }}</p>
            <p class="text-gray-600">姓名: {{ searchResult.name }}</p>
            <button 
              @click="confirmShare"
              class="mt-3 w-full py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
            >確認邀請</button>
          </div>
          
          <div v-if="searchError" class="mt-4 p-4 bg-red-50 text-red-600 rounded-xl">
            {{ searchError }}
          </div>
        </div>
      </div>
    </div>
    
    <!-- Task Detail Dialog -->
    <div v-if="showTaskDetail && selectedTask" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-4 border-b flex justify-between items-center sticky top-0 bg-white z-10">
          <h2 class="text-lg font-semibold text-primary flex items-center gap-2">
            <span>📌</span>
            {{ selectedTask.name }}
          </h2>
          <button @click="showTaskDetail = false" class="text-gray-400 hover:text-gray-600 text-2xl">&times;</button>
        </div>
        
        <div class="p-6">
          <!-- Task Info Grid -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6 p-4 bg-gray-50 rounded-xl">
            <div v-if="selectedTask.members && selectedTask.members.length"><strong class="text-gray-500">成員：</strong>{{ selectedTask.members.map(m => m.name || 'User').join(', ') }}</div>
            <div><strong class="text-gray-500">狀態：</strong>{{ selectedTask.completed ? '✅ 已完成' : '❌ 未完成' }}</div>
            <div><strong class="text-gray-500">開始日期：</strong>{{ formatDate(selectedTask.start_date) }}</div>
            <div><strong class="text-gray-500">截止日期：</strong>{{ formatDate(selectedTask.end_date) }}</div>
            <div v-if="selectedTask.assistant" class="sm:col-span-2">
              <strong class="text-gray-500">筆記：</strong>{{ Array.isArray(selectedTask.assistant) ? selectedTask.assistant.join(', ') : selectedTask.assistant }}
            </div>
            <div v-if="selectedTask.remark" class="sm:col-span-2">
              <strong class="text-gray-500">備註：</strong>{{ selectedTask.remark }}
            </div>
          </div>
          
          <!-- Comments Section -->
          <div class="mb-6 p-4 bg-gray-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <span>💬</span>
              留言
            </h4>
            <div v-if="selectedTask.comments && selectedTask.comments.length" class="space-y-2 max-h-60 overflow-y-auto mb-4">
              <div 
                v-for="comment in selectedTask.comments" 
                :key="comment.comment_id"
                class="p-3 bg-white rounded-lg border-l-4 border-primary"
              >
                <strong class="text-primary">{{ comment.user_name }}:</strong> {{ comment.task_message }}
              </div>
            </div>
            <div v-else class="text-center py-4 text-gray-400 mb-4">暫無留言</div>
            
            <div class="flex gap-2">
              <input 
                v-model="newComment"
                placeholder="輸入留言..."
                @keyup.enter="addComment"
                class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
              <button 
                @click="addComment"
                class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark transition-colors"
              >發送</button>
            </div>
          </div>
          
          <!-- Files Section -->
          <div class="p-4 bg-gray-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-4 flex items-center gap-2">
              <span>📎</span>
              檔案
            </h4>
            <div v-if="selectedTask.files && selectedTask.files.length" class="space-y-2">
              <a 
                v-for="file in selectedTask.files" 
                :key="file.id"
                :href="`http://localhost:5000/api/timelines/files/${file.filename}`"
                target="_blank"
                class="block p-3 bg-white rounded-lg hover:bg-blue-50 transition-colors text-primary"
              >
                📄 {{ file.original_filename }} ({{ (file.file_size / 1024).toFixed(2) }} KB)
              </a>
            </div>
            <div v-else class="text-center py-4 text-gray-400">暫無檔案</div>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import api from '../services/api';

const timelines = ref([]);
const selectedTimeline = ref(null);
const selectedTask = ref(null);
const timelineTasks = ref([]);
const showCreateModal = ref(false);
const showTaskDetail = ref(false);
const showAddTaskModal = ref(false);
const editingTimeline = ref(null);
const newComment = ref('');
const isEditingRemark = ref(false);
const newRemark = ref('');
const isSharePanelOpen = ref(false);
const inputEmail = ref('');
const searchResult = ref(null);
const searchError = ref('');

const timelineForm = ref({
  name: '',
  start_date: '',
  end_date: '',
  color: '#11998e'
});

const taskForm = ref({
  name: '',
  assistant: '',
  start_date: '',
  end_date: '',
  task_remark: '',
  isWork: false
});

const resetTaskForm = () => {
  taskForm.value = {
    name: '',
    assistant: '',
    start_date: '',
    end_date: '',
    task_remark: '',
    isWork: false
  };
};

const fetchTimelines = async () => {
  try {
    const response = await api.get('/timelines');
    timelines.value = response.data;
  } catch (error) {
    console.error('取得專案失敗:', error);
    alert('取得專案失敗');
  }
};

const handleSubmit = async () => {
  if (!timelineForm.value.name || !timelineForm.value.name.trim()) {
    alert('請輸入專案名稱');
    return;
  }
  
  try {
    const formData = {
      name: timelineForm.value.name.trim(),
      start_date: timelineForm.value.start_date ? new Date(timelineForm.value.start_date).toISOString().split('T')[0] : '',
      end_date: timelineForm.value.end_date ? new Date(timelineForm.value.end_date).toISOString().split('T')[0] : '',
      color: timelineForm.value.color || '#11998e'
    };
    
    if (editingTimeline.value) {
      await api.put(`/timelines/${editingTimeline.value.id}`, formData);
      alert('專案更新成功');
    } else {
      await api.post('/timelines', formData);
      alert('專案新增成功');
    }
    await fetchTimelines();
    closeModal();
  } catch (error) {
    alert(error.response?.data?.error || '操作失敗');
  }
};

const handleAddTask = async () => {
  if (!taskForm.value.name || !taskForm.value.name.trim()) {
    alert('請輸入任務名稱');
    return;
  }
  if (!taskForm.value.end_date) {
    alert('請選擇截止日期');
    return;
  }
  
  try {
    const assistantArray = taskForm.value.assistant 
      ? taskForm.value.assistant.split(',').map(s => s.trim()).filter(s => s)
      : [];
    
    const formData = {
      name: taskForm.value.name.trim(),
      assistant: assistantArray,
      timeline_id: selectedTimeline.value.id,
      start_date: taskForm.value.start_date || null,
      end_date: taskForm.value.end_date,
      task_remark: taskForm.value.task_remark || '',
      isWork: taskForm.value.isWork ? 1 : 0
    };
    
    await api.post('/tasks', formData);
    alert('任務新增成功');
    showAddTaskModal.value = false;
    resetTaskForm();
    await viewTimeline(selectedTimeline.value);
    await fetchTimelines();
  } catch (error) {
    alert(error.response?.data?.error || '新增任務失敗');
  }
};

const deleteTask = async (taskId) => {
  if (!confirm('確定要刪除此任務？')) return;
  
  try {
    await api.delete(`/tasks/${taskId}`);
    alert('任務刪除成功');
    await viewTimeline(selectedTimeline.value);
    await fetchTimelines();
  } catch (error) {
    alert(error.response?.data?.error || '刪除任務失敗');
  }
};

const editTimeline = (timeline) => {
  editingTimeline.value = timeline;
  timelineForm.value = {
    name: timeline.name,
    start_date: timeline.startDate || '',
    end_date: timeline.endDate || '',
    color: timeline.color || '#11998e'
  };
  showCreateModal.value = true;
};

const deleteTimeline = async (id) => {
  if (!confirm('確定要刪除此專案？相關任務也會被刪除！')) return;
  
  try {
    await api.delete(`/timelines/${id}`);
    alert('專案刪除成功');
    await fetchTimelines();
  } catch (error) {
    alert(error.response?.data?.error || '刪除失敗');
  }
};

const viewTimeline = async (timeline) => {
  selectedTimeline.value = timeline;
  newRemark.value = timeline.remark || '';
  try {
    const response = await api.get(`/timelines/${timeline.id}/tasks`);
    timelineTasks.value = response.data;
  } catch (error) {
    console.error('取得任務失敗:', error);
  }
};

const viewTaskDetail = async (task) => {
  selectedTask.value = { ...task };
  
  try {
    const response = await api.get(`/timelines/tasks/${task.task_id}/comments`);
    selectedTask.value.comments = response.data;
  } catch (error) {
    console.error('獲取留言失敗:', error);
    selectedTask.value.comments = [];
  }
  
  try {
    const response = await api.get(`/timelines/tasks/${task.task_id}/files`);
    selectedTask.value.files = response.data;
  } catch (error) {
    console.error('獲取檔案失敗:', error);
    selectedTask.value.files = [];
  }
  
  showTaskDetail.value = true;
};

const addComment = async () => {
  if (!newComment.value.trim() || !selectedTask.value) return;
  
  try {
    await api.post(`/timelines/tasks/${selectedTask.value.task_id}/comments`, {
      task_message: newComment.value
    });
    alert('留言成功');
    newComment.value = '';
    await viewTaskDetail(selectedTask.value);
  } catch (error) {
    alert('留言失敗');
  }
};

const updateRemark = async () => {
  if (!selectedTimeline.value) return;
  
  try {
    await api.put(`/timelines/${selectedTimeline.value.id}/remark`, {
      remark: newRemark.value
    });
    selectedTimeline.value.remark = newRemark.value;
    alert('備註更新成功');
    isEditingRemark.value = false;
  } catch (error) {
    alert('備註更新失敗');
  }
};

const searchUser = async () => {
  if (!inputEmail.value.trim()) {
    searchError.value = '請輸入 Email';
    return;
  }
  
  try {
    const response = await api.post('/timelines/search_user', {
      email: inputEmail.value
    });
    searchResult.value = response.data;
    searchError.value = '';
  } catch (error) {
    searchError.value = error.response?.data?.error || '查詢失敗';
    searchResult.value = null;
  }
};

const confirmShare = async () => {
  if (!searchResult.value || !selectedTimeline.value) return;
  
  try {
    await api.post(`/timelines/${selectedTimeline.value.id}/members`, {
      user_id: searchResult.value.id,
      role: 1
    });
    alert('邀請成功');
    isSharePanelOpen.value = false;
    inputEmail.value = '';
    searchResult.value = null;
  } catch (error) {
    alert(error.response?.data?.error || '邀請失敗');
  }
};

const toggleTask = async (taskId) => {
  try {
    await api.patch(`/tasks/${taskId}/toggle`);
    await viewTimeline(selectedTimeline.value);
    await fetchTimelines();
  } catch (error) {
    console.error('更新任務狀態失敗:', error);
    alert('更新任務狀態失敗');
  }
};

const closeModal = () => {
  showCreateModal.value = false;
  editingTimeline.value = null;
  timelineForm.value = {
    name: '',
    start_date: '',
    end_date: '',
    color: '#11998e'
  };
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

onMounted(() => {
  fetchTimelines();
});
</script>
