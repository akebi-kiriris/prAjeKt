<template>
  <div>
    <!-- 專案詳情 Dialog -->
    <div v-if="selectedTimeline" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent shrink-0">
          <div>
            <h2 class="text-xl font-bold text-gray-800">{{ selectedTimeline.name }}</h2>
            <p class="text-sm text-gray-500 mt-1">{{ formatDate(selectedTimeline.startDate) }} - {{ formatDate(selectedTimeline.endDate) }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button @click="showAiGenerateModal = true" class="flex items-center gap-2 px-4 py-2 bg-linear-to-r from-purple-500 to-indigo-500 text-white text-sm font-medium rounded-xl hover:brightness-110 transition-all shadow">
              <span>🤖</span> AI 生成任務
            </button>
            <button @click="showAddTaskModal = true" class="flex items-center gap-2 px-4 py-2 bg-primary text-white text-sm font-medium rounded-xl hover:brightness-110 transition-all shadow">
              <span>＋</span> 新增任務
            </button>
            <button v-if="selectedTimeline?.role === 0" @click="isSharePanelOpen = true" class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-600 text-sm font-medium rounded-xl hover:bg-gray-50 transition-all shadow-sm">
              <span>👥</span> 成員管理
            </button>
            <button @click="$emit('close')" class="w-9 h-9 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-xl transition-colors text-xl">&times;</button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-5">
          <!-- 備註區域 -->
          <div v-if="!isEditingRemark && !selectedTimeline.remark" class="mb-4">
            <button @click="isEditingRemark = true" class="text-sm text-gray-400 hover:text-primary transition-colors flex items-center gap-1">
              <span>✏️</span> 新增備註
            </button>
          </div>
          <div v-if="!isEditingRemark && selectedTimeline.remark" class="mb-4 p-4 bg-yellow-50/70 border border-yellow-100 rounded-xl">
            <div class="flex items-start justify-between">
              <p class="text-sm text-gray-600">{{ selectedTimeline.remark }}</p>
              <button @click="startEditRemark" class="ml-2 text-gray-400 hover:text-primary transition-colors shrink-0">✏️</button>
            </div>
          </div>
          <div v-if="isEditingRemark" class="mb-4">
            <textarea v-model="localRemark" rows="3" placeholder="新增備註..." class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"></textarea>
            <div class="flex gap-2 mt-2">
              <button @click="saveRemark" class="px-4 py-1.5 bg-primary text-white text-sm font-medium rounded-lg hover:brightness-110 transition-all">儲存</button>
              <button @click="isEditingRemark = false" class="px-4 py-1.5 bg-gray-100 text-gray-600 text-sm font-medium rounded-lg hover:bg-gray-200 transition-all">取消</button>
            </div>
          </div>

          <!-- 任務列表 -->
          <div class="space-y-2">
            <div v-for="task in timelineTasks" :key="task.task_id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group">
              <input type="checkbox" :checked="task.completed" @change="$emit('toggle-task', task.task_id)" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" />
              <span :class="['flex-1 text-sm cursor-pointer', task.completed ? 'line-through text-gray-400' : 'text-gray-700']" @click="openTaskDetail(task)">{{ task.name }}</span>
              <span v-if="task.end_date" class="text-xs text-gray-400 hidden group-hover:inline">{{ formatDate(task.end_date) }}</span>
              <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', getPriorityBadgeClass(task.priority)]">{{ getPriorityLabel(task.priority) }}</span>
              <button @click="$emit('delete-task', task.task_id)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all text-sm">🗑️</button>
            </div>
            <div v-if="timelineTasks.length === 0" class="text-center py-10 text-gray-400">
              <span class="text-4xl block mb-2">📋</span>
              <p class="text-sm">尚無任務，點擊「新增任務」開始建立</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新增任務 Modal -->
    <div v-if="showAddTaskModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-800">新增任務</h3>
          <button @click="showAddTaskModal = false; resetTaskForm()" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <form @submit.prevent="handleAddTask" class="p-5 space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">任務名稱 <span class="text-red-500">*</span></label>
            <input v-model="taskForm.name" type="text" required placeholder="輸入任務名稱" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">開始日期</label>
              <input v-model="taskForm.start_date" type="date" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1.5">截止日期</label>
              <input v-model="taskForm.end_date" type="date" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">優先級</label>
            <select v-model="taskForm.priority" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white">
              <option :value="1">🔴 高優先</option>
              <option :value="2">🟡 中優先</option>
              <option :value="3">🟢 低優先</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">標籤（逗號分隔）</label>
            <input v-model="taskForm.tags" type="text" placeholder="例如：前端, 重要, Bug" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">備註</label>
            <textarea v-model="taskForm.task_remark" rows="3" placeholder="任務備註（可選）" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"></textarea>
          </div>
          <div class="flex gap-3 pt-2">
            <button type="button" @click="showAddTaskModal = false; resetTaskForm()" class="flex-1 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-xl hover:bg-gray-50 transition-colors">取消</button>
            <button type="submit" class="flex-1 py-2.5 bg-primary text-white font-semibold rounded-xl hover:brightness-110 transition-all shadow-md shadow-primary/25">新增</button>
          </div>
        </form>
      </div>
    </div>

    <!-- 成員管理 Panel -->
    <div v-if="isSharePanelOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-800">👥 成員管理</h3>
          <button @click="isSharePanelOpen = false" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <div class="p-5 space-y-4">
          <!-- 現有成員列表 -->
          <div v-if="timelineMembers.length > 0">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">目前成員</p>
            <div class="space-y-2">
              <div v-for="member in timelineMembers" :key="member.user_id" class="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-2.5">
                  <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
                    {{ (member.username || member.name || '?')[0].toUpperCase() }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-800">{{ member.username || member.name }}</p>
                    <p class="text-xs text-gray-500">{{ member.email }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-1.5">
                  <span :class="['px-2 py-0.5 text-xs font-medium rounded-full', member.role === 0 ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-500']">
                    {{ member.role === 0 ? '負責人' : '協作者' }}
                  </span>
                  <button v-if="member.role !== 0" @click="kickMember(member)" class="w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors text-sm font-bold">✕</button>
                </div>
              </div>
            </div>
          </div>
          <!-- 邀請新成員 -->
          <div :class="timelineMembers.length > 0 ? 'border-t border-gray-100 pt-4' : ''">
            <p class="text-sm text-gray-500 mb-3">邀請成員加入「{{ selectedTimeline?.name }}」</p>
            <div class="flex gap-2">
              <input v-model="inputEmail" type="email" placeholder="輸入用戶 Email" class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" @keyup.enter="searchUser" />
              <button @click="searchUser" class="px-4 py-2.5 bg-primary text-white font-medium rounded-xl hover:brightness-110 transition-all">搜尋</button>
            </div>
            <div v-if="searchError" class="mt-2 p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">{{ searchError }}</div>
            <div v-if="searchResult" class="mt-2 p-4 bg-green-50 border border-green-200 rounded-xl">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-gray-800">{{ searchResult.username }}</p>
                  <p class="text-sm text-gray-500">{{ searchResult.email }}</p>
                </div>
                <button @click="confirmShare" class="px-4 py-2 bg-primary text-white text-sm font-medium rounded-xl hover:brightness-110 transition-all">邀請</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 任務詳情 Dialog -->
    <div v-if="showTaskDetail && selectedTask" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent sticky top-0 bg-white z-10">
          <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📌</span>
            {{ selectedTask.name }}
          </h2>
          <button @click="showTaskDetail = false" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <div class="p-6 space-y-6">
          <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
            <div><p class="text-xs text-gray-500 mb-1">開始日期</p><p class="font-medium text-gray-800">{{ formatDate(selectedTask.start_date) || '未設定' }}</p></div>
            <div><p class="text-xs text-gray-500 mb-1">截止日期</p><p class="font-medium text-gray-800">{{ formatDate(selectedTask.end_date) || '未設定' }}</p></div>
          </div>
          <div v-if="selectedTask.task_remark" class="p-4 bg-yellow-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-2">📝 備註</h4>
            <p class="text-gray-600 text-sm">{{ selectedTask.task_remark }}</p>
          </div>
          <!-- 附件 -->
          <div v-if="selectedTask.files && selectedTask.files.length > 0">
            <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2"><span>📎</span> 附件</h4>
            <div class="grid grid-cols-2 gap-3">
              <div v-for="file in selectedTask.files" :key="file.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors">
                <span class="text-2xl">{{ file.file_name?.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? '🖼️' : '📄' }}</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-700 truncate">{{ file.file_name }}</p>
                  <a :href="`${apiBaseUrl}/timelines/tasks/${selectedTask.task_id}/files/${file.id}`" target="_blank" class="text-xs text-primary hover:underline">下載</a>
                </div>
              </div>
            </div>
          </div>
          <!-- 留言 -->
          <div>
            <h4 class="font-semibold text-gray-700 mb-4 flex items-center gap-2"><span>💬</span> 留言</h4>
            <div class="space-y-3 max-h-60 overflow-y-auto mb-4">
              <div v-for="comment in selectedTask.comments" :key="comment.id" class="flex gap-3 p-3 bg-gray-50 rounded-xl">
                <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">{{ comment.username?.charAt(0).toUpperCase() }}</div>
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-sm font-medium text-gray-700">{{ comment.username }}</span>
                    <span class="text-xs text-gray-400">{{ comment.created_at ? new Date(comment.created_at).toLocaleString('zh-TW') : '' }}</span>
                  </div>
                  <p class="text-sm text-gray-600">{{ comment.content }}</p>
                </div>
              </div>
              <div v-if="!selectedTask.comments || selectedTask.comments.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無留言</div>
            </div>
            <div class="flex gap-2">
              <input v-model="newComment" type="text" placeholder="新增留言..." @keyup.enter="addComment" class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
              <button @click="addComment" class="px-4 py-2.5 bg-primary text-white font-medium rounded-xl hover:brightness-110 transition-all">傳送</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- AI 生成任務預覽 Modal -->
    <div v-if="showAiGenerateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-purple-50 to-indigo-50 sticky top-0 bg-white z-10">
          <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">🤖</span>
            AI 智能生成任務
          </h2>
          <button @click="showAiGenerateModal = false" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <div class="p-6">
          <div v-if="isGeneratingAi" class="text-center py-12">
            <div class="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-spin">
              <span class="text-2xl">🤖</span>
            </div>
            <p class="text-gray-600 font-medium">AI 正在生成任務建議...</p>
            <p class="text-gray-400 text-sm mt-2">請稍候，正在分析專案內容</p>
          </div>
          <div v-else-if="aiGeneratedTasks.length === 0" class="text-center py-8">
            <p class="text-gray-500 mb-4">AI 將根據專案名稱自動生成任務建議</p>
            <button @click="generateTasksWithAi" class="px-6 py-3 bg-linear-to-r from-purple-500 to-indigo-500 text-white font-semibold rounded-xl hover:brightness-110 transition-all shadow-lg shadow-purple-200">
              🤖 開始生成
            </button>
          </div>
          <div v-else class="space-y-4">
            <div class="flex items-center justify-between mb-4">
              <p class="text-sm text-gray-600">共 {{ aiGeneratedTasks.length }} 個建議任務，已選 {{ selectedAiTasks.length }} 個</p>
              <div class="flex gap-2">
                <button @click="toggleAllAiTasks" class="text-sm text-primary hover:underline">{{ selectedAiTasks.length === aiGeneratedTasks.length ? '全部取消' : '全部選取' }}</button>
                <button @click="aiGeneratedTasks = []; selectedAiTasks = []" class="text-sm text-gray-400 hover:text-gray-600">重新生成</button>
              </div>
            </div>
            <div class="space-y-3 max-h-80 overflow-y-auto">
              <div v-for="(task, index) in aiGeneratedTasks" :key="index"
                @click="toggleAiTaskSelection(index)"
                :class="['p-4 rounded-xl border-2 cursor-pointer transition-all', selectedAiTasks.includes(index) ? 'border-purple-400 bg-purple-50' : 'border-gray-200 hover:border-gray-300']"
              >
                <div class="flex items-start gap-3">
                  <div :class="['w-6 h-6 rounded-full border-2 flex items-center justify-center shrink-0 mt-0.5', selectedAiTasks.includes(index) ? 'border-purple-500 bg-purple-500' : 'border-gray-300']">
                    <span v-if="selectedAiTasks.includes(index)" class="text-white text-xs">✓</span>
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="font-medium text-gray-800">{{ task.name }}</span>
                      <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', getAiPriorityClass(task.priority)]">{{ getPriorityLabel(task.priority) }}</span>
                    </div>
                    <div class="flex items-center gap-3 text-xs text-gray-500">
                      <span>📅 {{ formatDate(task.start_date) }} - {{ formatDate(task.end_date) }}</span>
                      <span v-if="task.tags">🏷️ {{ task.tags }}</span>
                    </div>
                    <p v-if="task.remark" class="text-sm text-gray-500 mt-1">{{ task.remark }}</p>
                  </div>
                </div>
              </div>
            </div>
            <div class="flex gap-3 pt-2">
              <button @click="showAiGenerateModal = false" class="flex-1 py-2.5 border border-gray-200 text-gray-600 font-medium rounded-xl hover:bg-gray-50 transition-colors">取消</button>
              <button @click="batchCreateAiTasks" :disabled="selectedAiTasks.length === 0" :class="['flex-1 py-2.5 font-semibold rounded-xl transition-all', selectedAiTasks.length > 0 ? 'bg-linear-to-r from-purple-500 to-indigo-500 text-white hover:brightness-110 shadow-lg shadow-purple-200' : 'bg-gray-100 text-gray-400 cursor-not-allowed']">
                新增選取任務 ({{ selectedAiTasks.length }})
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { taskService } from '../../services/taskService';
import { timelineService } from '../../services/timelineService';

const props = defineProps({
  selectedTimeline: Object,
  timelineTasks: Array,
  apiBaseUrl: String,
});

const emit = defineEmits(['close', 'toggle-task', 'delete-task', 'refresh-all']);

// 本元件管理的狀態
const showAddTaskModal = ref(false);
const isSharePanelOpen = ref(false);
const showTaskDetail = ref(false);
const selectedTask = ref(null);
const showAiGenerateModal = ref(false);
const aiGeneratedTasks = ref([]);
const selectedAiTasks = ref([]);
const isGeneratingAi = ref(false);
const isEditingRemark = ref(false);
const localRemark = ref('');
const newComment = ref('');
const inputEmail = ref('');
const searchResult = ref(null);
const searchError = ref('');
const timelineMembers = ref([]);

const taskForm = ref({ name: '', start_date: '', end_date: '', priority: 2, tags: '', task_remark: '' });

// 每次開啟新的 selectedTimeline 時重置 remark 狀態
watch(() => props.selectedTimeline, (val) => {
  if (val) {
    isEditingRemark.value = false;
    localRemark.value = val.remark || '';
  }
}, { immediate: true });

const resetTaskForm = () => {
  taskForm.value = { name: '', start_date: '', end_date: '', priority: 2, tags: '', task_remark: '' };
};

// ────────────── 備註 ──────────────
const startEditRemark = () => {
  localRemark.value = props.selectedTimeline?.remark || '';
  isEditingRemark.value = true;
};

const saveRemark = async () => {
  try {
    await timelineService.updateRemark(props.selectedTimeline.id, localRemark.value);
    props.selectedTimeline.remark = localRemark.value;
    isEditingRemark.value = false;
    emit('refresh-all');
  } catch { alert('更新備註失敗'); }
};

// ────────────── 任務 ──────────────
const handleAddTask = async () => {
  if (!props.selectedTimeline) return;
  try {
    const data = { ...taskForm.value, timeline_id: props.selectedTimeline.id };
    await taskService.create(data);
    showAddTaskModal.value = false;
    resetTaskForm();
    emit('refresh-all');
  } catch { alert('新增任務失敗'); }
};

const openTaskDetail = async (task) => {
  selectedTask.value = { ...task, comments: [], files: [] };
  try {
    const [commentsRes, filesRes] = await Promise.allSettled([
      timelineService.getComments(task.task_id),
      timelineService.getFiles(task.task_id)
    ]);
    if (commentsRes.status === 'fulfilled') selectedTask.value.comments = commentsRes.value.data;
    if (filesRes.status === 'fulfilled') selectedTask.value.files = filesRes.value.data;
  } catch (err) {
    console.error('取得任務詳情失敗:', err);
  }
  showTaskDetail.value = true;
};

const addComment = async () => {
  if (!newComment.value.trim() || !selectedTask.value) return;
  try {
    await timelineService.addComment(selectedTask.value.task_id, newComment.value);
    newComment.value = '';
    // 重新取得留言列表
    const res = await timelineService.getComments(selectedTask.value.task_id);
    selectedTask.value.comments = res.data;
  } catch { alert('新增留言失敗'); }
};

// ────────────── 成員管理 ──────────────
const loadMembers = async () => {
  if (!props.selectedTimeline) return;
  try {
    const res = await timelineService.getMembers(props.selectedTimeline.id);
    timelineMembers.value = res.data;
  } catch { timelineMembers.value = []; }
};

watch(isSharePanelOpen, (val) => {
  if (val) loadMembers();
  else { inputEmail.value = ''; searchResult.value = null; searchError.value = ''; }
});

const searchUser = async () => {
  if (!inputEmail.value.trim()) return;
  searchResult.value = null; searchError.value = '';
  try {
    const res = await timelineService.searchUser(inputEmail.value);
    searchResult.value = res.data;
  } catch (err) {
    searchError.value = err.response?.data?.error || '找不到用戶';
  }
};

const confirmShare = async () => {
  if (!searchResult.value || !props.selectedTimeline) return;
  try {
    await timelineService.addMember(props.selectedTimeline.id, searchResult.value.id);
    inputEmail.value = ''; searchResult.value = null;
    await loadMembers();
    alert('邀請成功！');
  } catch (err) {
    alert(err.response?.data?.error || '邀請失敗');
  }
};

const kickMember = async (member) => {
  if (!confirm(`確定要將「${member.username || member.name}」移出此專案？`)) return;
  try {
    await timelineService.removeMember(props.selectedTimeline.id, member.user_id);
    await loadMembers();
  } catch (err) {
    alert(err.response?.data?.error || '移除成員失敗');
  }
};

// ────────────── AI 生成 ──────────────
const generateTasksWithAi = async () => {
  if (!props.selectedTimeline) return;
  isGeneratingAi.value = true;
  try {
    const res = await timelineService.generateTasks(props.selectedTimeline.id);
    aiGeneratedTasks.value = res.data.tasks || [];
    selectedAiTasks.value = aiGeneratedTasks.value.map((_, i) => i);
  } catch (err) { alert(err.response?.data?.error || 'AI 生成失敗，請稍後再試'); }
  finally { isGeneratingAi.value = false; }
};

const toggleAiTaskSelection = (index) => {
  const pos = selectedAiTasks.value.indexOf(index);
  if (pos === -1) selectedAiTasks.value.push(index);
  else selectedAiTasks.value.splice(pos, 1);
};

const toggleAllAiTasks = () => {
  if (selectedAiTasks.value.length === aiGeneratedTasks.value.length) selectedAiTasks.value = [];
  else selectedAiTasks.value = aiGeneratedTasks.value.map((_, i) => i);
};

const batchCreateAiTasks = async () => {
  if (!props.selectedTimeline || selectedAiTasks.value.length === 0) return;
  const tasksToCreate = selectedAiTasks.value.map(i => ({ ...aiGeneratedTasks.value[i], timeline_id: props.selectedTimeline.id }));
  try {
    await timelineService.batchCreateTasks(props.selectedTimeline.id, tasksToCreate);
    showAiGenerateModal.value = false;
    aiGeneratedTasks.value = []; selectedAiTasks.value = [];
    emit('refresh-all');
  } catch (err) { alert(err.response?.data?.error || '批量新增失敗'); }
};

// ────────────── 工具函式 ──────────────
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

const getPriorityLabel = (priority) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中');

const getPriorityBadgeClass = (priority) => ({
  1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
  2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
  3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
}[priority] || 'bg-gray-100 text-gray-700 border border-gray-200');

const getAiPriorityClass = (priority) => ({
  1: 'bg-red-100 text-red-700', 2: 'bg-yellow-100 text-yellow-700', 3: 'bg-green-100 text-green-700'
}[priority] || 'bg-gray-100 text-gray-700');
</script>
