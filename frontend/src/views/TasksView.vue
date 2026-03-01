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
            <div class="flex-1 min-w-0">
              <h3
                class="text-xl font-semibold text-primary flex items-center gap-2 mb-2 cursor-pointer hover:underline"
                @click="openTaskDetail(task)"
              >
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
                @click="openTaskDetail(task)"
                class="w-10 h-10 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 flex items-center justify-center transition-colors"
                title="查看詳情"
              >
                📄
              </button>
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

    <!-- 任務詳情 Modal -->
    <Teleport to="body">
      <div
        v-if="showTaskDetail && detailTask"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showTaskDetail = false"
      >
        <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] mx-4 overflow-y-auto animate-slideUp">
          <!-- Header -->
          <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent sticky top-0 bg-white z-10">
            <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📌</span>
              {{ detailTask.name }}
            </h2>
            <button @click="showTaskDetail = false" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors">&times;</button>
          </div>
          <div class="p-6 space-y-6">
            <!-- 基本資訊 -->
            <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
              <div><p class="text-xs text-gray-500 mb-1">開始日期</p><p class="font-medium text-gray-800">{{ formatDate(detailTask.start_date) || '未設定' }}</p></div>
              <div><p class="text-xs text-gray-500 mb-1">截止日期</p><p class="font-medium text-gray-800">{{ formatDate(detailTask.end_date) || '未設定' }}</p></div>
            </div>
            <div v-if="detailTask.task_remark" class="p-4 bg-yellow-50 rounded-xl">
              <h4 class="font-semibold text-gray-700 mb-2">📝 備註</h4>
              <p class="text-gray-600 text-sm">{{ detailTask.task_remark }}</p>
            </div>

            <!-- ── 附件區 ── -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="font-semibold text-gray-700 flex items-center gap-2">
                  <span>📎</span> 附件
                  <span class="text-xs text-gray-400 font-normal">({{ detailFiles.length }})</span>
                </h4>
                <label class="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-lg hover:bg-primary/20 transition-colors">
                  <span>＋</span> 上傳檔案
                  <input ref="detailFileInput" type="file" class="hidden"
                    accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.csv,.mp4,.mov"
                    @change="handleDetailFileUpload" />
                </label>
              </div>
              <div v-if="detailFiles.length === 0" class="text-center py-6 text-gray-400 text-sm bg-gray-50 rounded-xl border border-dashed border-gray-200">
                尚無附件，點擊「上傳檔案」新增
              </div>
              <div v-else class="space-y-2">
                <div v-for="file in detailFiles" :key="file.id"
                  class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors group">
                  <img v-if="isImageFile(file.original_filename)"
                    :src="`${apiBase}/tasks/files/${file.filename}`"
                    class="w-12 h-12 object-cover rounded-lg border border-gray-200 shrink-0"
                    :alt="file.original_filename" />
                  <span v-else class="text-3xl shrink-0">{{ getFileIcon(file.original_filename) }}</span>
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-700 truncate">{{ file.original_filename }}</p>
                    <p class="text-xs text-gray-400">{{ formatFileSize(file.file_size) }} · {{ formatDateTime(file.uploaded_at) }}</p>
                  </div>
                  <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button @click="downloadFile(`${apiBase}/tasks/files/${file.filename}`, file.original_filename)"
                      class="w-8 h-8 flex items-center justify-center text-primary hover:bg-primary/10 rounded-lg transition-colors"
                      title="下載">⬇️</button>
                    <button @click="deleteDetailFile(file.id)"
                      class="w-8 h-8 flex items-center justify-center text-red-400 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
                      title="刪除">🗑️</button>
                  </div>
                </div>
              </div>
            </div>

            <!-- ── 留言區 ── -->
            <div>
              <h4 class="font-semibold text-gray-700 mb-4 flex items-center gap-2">
                <span>💬</span> 留言
                <span class="text-xs text-gray-400 font-normal">({{ detailComments.length }})</span>
              </h4>
              <div class="space-y-3 max-h-60 overflow-y-auto mb-4">
                <div v-for="comment in detailComments" :key="comment.comment_id" class="flex gap-3 p-3 bg-gray-50 rounded-xl group">
                  <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
                    {{ comment.user_name?.charAt(0)?.toUpperCase() }}
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-sm font-medium text-gray-700">{{ comment.user_name }}</span>
                      <span class="text-xs text-gray-400">{{ formatDateTime(comment.created_at) }}</span>
                    </div>
                    <p class="text-sm text-gray-600">{{ comment.task_message }}</p>
                  </div>
                  <button @click="deleteDetailComment(comment.comment_id)"
                    class="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all shrink-0"
                    title="刪除留言">✕</button>
                </div>
                <div v-if="detailComments.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無留言</div>
              </div>
              <div class="flex gap-2">
                <input v-model="detailNewComment" type="text" placeholder="新增留言..." @keyup.enter="addDetailComment"
                  class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
                <button @click="addDetailComment" :disabled="!detailNewComment.trim()"
                  class="px-4 py-2.5 bg-primary text-white font-medium rounded-xl hover:brightness-110 transition-all disabled:opacity-50">傳送</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
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

// 檔案下載基礎 URL（僅用於 <img> src 與下載連結）
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// ── 新增/編輯任務 ──
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

const cancelEdit = () => { resetForm(); };

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
  taskForm.value = { name: '', start_date: '', end_date: '', task_remark: '' };
};

// ── 任務詳情 Modal ──
const showTaskDetail = ref(false);
const detailTask = ref(null);
const detailComments = ref([]);
const detailFiles = ref([]);
const detailNewComment = ref('');
const detailFileInput = ref(null);

const openTaskDetail = async (task) => {
  detailTask.value = { ...task };
  detailComments.value = [];
  detailFiles.value = [];
  showTaskDetail.value = true;
  try {
    const [cRes, fRes] = await Promise.allSettled([
      taskService.getComments(task.task_id),
      taskService.getFiles(task.task_id)
    ]);
    if (cRes.status === 'fulfilled') detailComments.value = cRes.value.data || [];
    if (fRes.status === 'fulfilled') detailFiles.value = fRes.value.data || [];
  } catch (err) {
    console.error('取得任務詳情失敗:', err);
  }
};

const addDetailComment = async () => {
  if (!detailNewComment.value.trim() || !detailTask.value) return;
  try {
    await taskService.addComment(detailTask.value.task_id, detailNewComment.value.trim());
    detailNewComment.value = '';
    const res = await taskService.getComments(detailTask.value.task_id);
    detailComments.value = res.data || [];
  } catch { alert('新增留言失敗'); }
};

const deleteDetailComment = async (commentId) => {
  if (!confirm('確定要刪除此留言？')) return;
  try {
    await taskService.deleteComment(detailTask.value.task_id, commentId);
    detailComments.value = detailComments.value.filter(c => c.comment_id !== commentId);
  } catch { alert('刪除留言失敗'); }
};

const handleDetailFileUpload = async (event) => {
  const file = event.target.files?.[0];
  if (!file || !detailTask.value) return;
  if (file.size > 10 * 1024 * 1024) { alert('檔案大小不可超過 10MB'); return; }
  const formData = new FormData();
  formData.append('file', file);
  try {
    await taskService.uploadFile(detailTask.value.task_id, formData);
    const res = await taskService.getFiles(detailTask.value.task_id);
    detailFiles.value = res.data || [];
  } catch (err) {
    alert(err.response?.data?.error || '上傳失敗');
  } finally {
    if (detailFileInput.value) detailFileInput.value.value = '';
  }
};

const deleteDetailFile = async (fileId) => {
  if (!confirm('確定要刪除此附件？')) return;
  try {
    await taskService.deleteFile(detailTask.value.task_id, fileId);
    detailFiles.value = detailFiles.value.filter(f => f.id !== fileId);
  } catch { alert('刪除附件失敗'); }
};

// ── 成員管理 ──
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

// ── 工具函式 ──
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString('zh-TW', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
};

const isImageFile = (filename) => /\.(jpg|jpeg|png|gif|webp)$/i.test(filename || '');

const getFileIcon = (filename) => {
  if (!filename) return '📄';
  const ext = filename.split('.').pop()?.toLowerCase();
  return ({ pdf: '📕', doc: '📝', docx: '📝', xls: '📊', xlsx: '📊', ppt: '📋', pptx: '📋', zip: '🗜️', csv: '📊', mp4: '🎬', mov: '🎬', txt: '📃' })[ext] || '📄';
};

const formatFileSize = (bytes) => {
  if (!bytes) return '';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
};

const downloadFile = async (url, originalFilename) => {
  try {
    const res = await fetch(url);
    if (!res.ok) throw new Error('下載失敗');
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = blobUrl;
    a.download = originalFilename || 'download';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  } catch {
    alert('下載失敗，請稍後再試');
  }
};

onMounted(() => { store.fetchTasks(); });
</script>
