<template>
  <div>
    <!-- 專案詳情 Dialog -->
    <div v-if="selectedTimeline" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" @click.self="$emit('close')">
      <div class="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-slate-200 bg-white shadow-[0_20px_40px_rgba(15,23,42,0.14)]">
        <div class="shrink-0 flex items-center justify-between border-b border-slate-200 bg-slate-50/80 p-5">
          <div>
            <h2 class="text-xl font-bold text-slate-800">{{ selectedTimeline.name }}</h2>
            <p class="text-sm text-slate-500 mt-1">{{ formatDate(selectedTimeline.startDate) }} - {{ formatDate(selectedTimeline.endDate) }}</p>
          </div>
          <div class="flex items-center gap-2">
            <button @click="showAiGenerateModal = true" class="flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white shadow-[0_8px_18px_rgba(37,99,235,0.24)] transition-all hover:brightness-110">
              <span>🤖</span> AI 生成任務
            </button>
            <button @click="showAddTaskModal = true" class="flex items-center gap-2 rounded-xl bg-primary px-4 py-2 text-sm font-medium text-white shadow-[0_8px_18px_rgba(37,99,235,0.24)] transition-all hover:brightness-110">
              <span>＋</span> 新增任務
            </button>
            <button v-if="selectedTimeline?.role === 0" @click="isSharePanelOpen = true" class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 text-slate-600 text-sm font-medium rounded-xl hover:bg-slate-50 transition-all shadow-sm">
              <span>👥</span> 成員管理
            </button>
            <button @click="$emit('close')" class="w-9 h-9 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-xl transition-colors text-xl">&times;</button>
          </div>
        </div>

        <div class="flex-1 overflow-y-auto p-5">
          <!-- 備註區域 -->
          <div v-if="!isEditingRemark && !timelineRemark" class="mb-4">
            <button @click="isEditingRemark = true" class="text-sm text-slate-400 hover:text-primary transition-colors flex items-center gap-1">
              <span>✏️</span> 新增備註
            </button>
          </div>
          <div v-if="!isEditingRemark && timelineRemark" class="mb-4 p-4 bg-yellow-50/70 border border-yellow-100 rounded-xl">
            <div class="flex items-start justify-between">
              <p class="text-sm text-slate-600">{{ timelineRemark }}</p>
              <button @click="startEditRemark" class="ml-2 text-slate-400 hover:text-primary transition-colors shrink-0">✏️</button>
            </div>
          </div>
          <div v-if="isEditingRemark" class="mb-4">
            <textarea v-model="localRemark" rows="3" placeholder="新增備註..." class="w-full px-4 py-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"></textarea>
            <div class="flex gap-2 mt-2">
              <button @click="saveRemark" class="px-4 py-1.5 bg-primary text-white text-sm font-medium rounded-lg hover:brightness-110 transition-all">儲存</button>
              <button @click="isEditingRemark = false" class="px-4 py-1.5 bg-slate-100 text-slate-600 text-sm font-medium rounded-lg hover:bg-slate-200 transition-all">取消</button>
            </div>
          </div>

          <TimelineWeeklyReportPanel
            :expanded="isWeeklyReportExpanded"
            :loading="weeklyReportLoading"
            :error="weeklyReportError"
            :weekly-report="weeklyReport"
            :weekly-report-range="weeklyReportRange"
            :format-date="formatDate"
            :get-ai-source-label="getWeeklyReportAiSummarySourceLabel"
            @toggle-expanded="toggleWeeklyReportExpanded"
            @refresh="fetchWeeklyReport"
            @update:weekly-report-range="weeklyReportRange = $event"
          />

          <TimelineRiskAnalysisPanel
            :expanded="isRiskAnalysisExpanded"
            :loading="riskAnalysisLoading"
            :error="riskAnalysisError"
            :risk-analysis="riskAnalysis"
            :is-risk-graph-visible="isRiskGraphVisible"
            :risk-graph-version="riskGraphVersion"
            :risk-graph-layout="riskGraphLayout"
            :node-width="RISK_GRAPH_NODE_WIDTH"
            :node-height="RISK_GRAPH_NODE_HEIGHT"
            :truncate-node-name="truncateRiskGraphNodeName"
            :get-node-fill="getRiskGraphNodeFill"
            :get-node-stroke="getRiskGraphNodeStroke"
            @toggle-expanded="toggleRiskAnalysisExpanded"
            @toggle-graph="toggleRiskGraph"
            @refresh="fetchRiskAnalysis"
            @rebuild-graph="rebuildRiskGraph"
          />

          <ProjectKnowledgePanel
            :documents="projectKnowledgeDocuments"
            :events="projectKnowledgeEvents"
            :loading="projectKnowledgeLoading"
            :uploading="projectKnowledgeUploading"
            :selected-ids="projectKnowledgeSelectedIds"
            :query="projectKnowledgeQuery"
            :sort="projectKnowledgeSort"
            :status="projectKnowledgeStatus"
            :error="projectKnowledgeError"
            :format-date-time="formatDateTime"
            @upload="handleProjectKnowledgeUpload"
            @refresh="fetchProjectKnowledgeDocuments"
            @batch-delete="batchDeleteProjectKnowledge"
            @batch-reindex="batchReindexProjectKnowledge"
            @toggle-selection="toggleKnowledgeSelection"
            @download="downloadProjectKnowledgeDocument"
            @preview="previewProjectKnowledgeDocument"
            @update:query="projectKnowledgeQuery = $event"
            @update:sort="projectKnowledgeSort = $event"
            @update:status="projectKnowledgeStatus = $event"
          />

          <!-- 任務列表 -->
          <div class="space-y-2">
            <div v-for="task in timelineTasks" :key="task.task_id" class="flex items-center gap-3 p-3 bg-slate-50 rounded-xl hover:bg-slate-100 transition-colors group">
              <input type="checkbox" :checked="task.completed" @change="$emit('toggle-task', task.task_id)" class="w-5 h-5 rounded border-slate-300 text-primary focus:ring-primary cursor-pointer" />
              <div class="flex-1 min-w-0">
                <span :class="['text-sm cursor-pointer', task.completed ? 'line-through text-slate-400' : 'text-slate-700']" @click="openTaskDetail(task)">{{ task.name }}</span>
                <p v-if="(task.depends_on_task_ids || []).length > 0" class="text-[11px] text-slate-400 mt-0.5 truncate">
                  前置：{{ (task.depends_on_task_ids || []).map(getTaskNameById).join('、') }}
                </p>
              </div>
              <span v-if="task.end_date" class="text-xs text-slate-400 hidden group-hover:inline">{{ formatDate(task.end_date) }}</span>
              <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', getPriorityBadgeClass(task.priority)]">{{ getPriorityLabel(task.priority) }}</span>
              <button v-if="canManageTaskMembers(task)" @click.stop="openTaskMemberPanel(task)" class="opacity-100 md:opacity-0 md:group-hover:opacity-100 text-indigo-400 hover:text-indigo-600 transition-all text-sm" title="指派成員">👥</button>
              <button @click="$emit('delete-task', task.task_id)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all text-sm">🗑️</button>
            </div>
            <div v-if="timelineTasks.length === 0" class="text-center py-10 text-slate-400">
              <span class="text-4xl block mb-2">📋</span>
              <p class="text-sm">尚無任務，點擊「新增任務」開始建立</p>
            </div>
          </div>
        </div>
      </div>
    </div>

    <TimelineAddTaskModal
      :open="showAddTaskModal"
      :task-form="taskForm"
      :timeline-members="timelineMembers"
      :add-task-assignee-ids="addTaskAssigneeIds"
      :add-task-dependency-ids="addTaskDependencyIds"
      :available-dependency-tasks="availableDependencyTasks"
      :add-task-conflict-summary="addTaskConflictSummary"
      :add-task-conflict-previews="addTaskConflictPreviews"
      :conflict-ai-suggestion-loading-key="conflictAiSuggestionLoadingKey"
      :get-timeline-member-name="getTimelineMemberName"
      :get-task-name-by-id="getTaskNameById"
      :format-date="formatDate"
      @close="showAddTaskModal = false; resetTaskForm()"
      @submit="handleAddTask"
      @request-ai-suggestion="requestAddTaskConflictAiSuggestion"
      @update:task-form="taskForm = $event"
      @update:add-task-assignee-ids="addTaskAssigneeIds = $event"
      @update:add-task-dependency-ids="addTaskDependencyIds = $event"
    />

    <TimelineSharePanel
      :open="isSharePanelOpen"
      :timeline-name="selectedTimeline?.name || ''"
      :timeline-members="timelineMembers"
      :input-email="inputEmail"
      :search-result="searchResult"
      :search-error="searchError"
      @close="isSharePanelOpen = false"
      @search-user="searchUser"
      @confirm-share="confirmShare"
      @kick-member="kickMember"
      @update:input-email="inputEmail = $event"
    />

    <TimelineTaskMemberPanel
      :open="isTaskMemberPanelOpen"
      :task-name="assignTask?.name || ''"
      :task-members-for-assign="taskMembersForAssign"
      :timeline-members="timelineMembers"
      @close="isTaskMemberPanelOpen = false"
      @quick-assign="quickAssignTaskMember"
      @kick-member="kickAssignedMember"
      @set-owner="setAssignedTaskOwner"
    />

    <!-- 任務詳情 Dialog -->
    <div v-if="showTaskDetail && selectedTask" class="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4" @click.self="showTaskDetail = false">
      <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-[0_20px_40px_rgba(15,23,42,0.14)]">
        <div class="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-slate-50/80 p-5">
          <h2 class="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📌</span>
            {{ selectedTask.name }}
          </h2>
          <button @click="showTaskDetail = false" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">&times;</button>
        </div>
        <TaskDetailPanel
          :selected-task="selectedTask"
          :selected-task-dependency-ids="selectedTaskDependencyIds"
          :selected-task-dependency-options="selectedTaskDependencyOptions"
          :is-saving-task-dependencies="isSavingTaskDependencies"
          :get-task-name-by-id="getTaskNameById"
          :can-manage-task-members="canManageTaskMembers"
          :task-members-for-assign="taskMembersForAssign"
          :timeline-members="timelineMembers"
          :task-subtasks="taskSubtasks"
          :subtask-progress="subtaskProgress"
          :new-subtask-name="newSubtaskName"
          :task-files="taskFiles"
          :api-base-url="apiBaseUrl"
          :task-comments="taskComments"
          :is-summarizing-comments="isSummarizingComments"
          :comment-summary="commentSummary"
          :comment-summary-meta="commentSummaryMeta"
          :new-comment="newComment"
          @update:selected-task-dependency-ids="selectedTaskDependencyIds = $event"
          @save-dependencies="saveSelectedTaskDependencies"
          @set-owner="setAssignedTaskOwner"
          @kick-member="kickAssignedMember"
          @quick-assign="quickAssignTaskMember"
          @toggle-subtask="toggleSubtask"
          @delete-subtask="deleteSubtask"
          @update:new-subtask-name="newSubtaskName = $event"
          @add-subtask="addSubtask"
          @file-upload="handleFileUpload"
          @download-file="(file) => downloadFile(`${apiBaseUrl}/tasks/files/${file.filename}`, file.original_filename)"
          @delete-file="deleteFile"
          @summarize-comments="summarizeComments"
          @delete-comment="deleteComment"
          @update:new-comment="newComment = $event"
          @add-comment="addComment"
        />
      </div>
    </div>

    <!-- AI 生成任務預覽 Modal -->
    <div v-if="showAiGenerateModal" class="fixed inset-0 z-60 flex items-center justify-center bg-black/50 p-4" @click.self="showAiGenerateModal = false">
      <div class="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-[0_20px_40px_rgba(15,23,42,0.14)]">
        <div class="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-slate-50/80 p-5">
          <h2 class="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center">🤖</span>
            AI 智能生成任務
          </h2>
          <button @click="showAiGenerateModal = false" class="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">&times;</button>
        </div>
        <AiTaskGeneratePanel
          :is-generating-ai="isGeneratingAi"
          :ai-generated-tasks="aiGeneratedTasks"
          :selected-ai-tasks="selectedAiTasks"
          :ai-prompt="aiPrompt"
          :use-rag-planning="useRagPlanning"
          :use-copilot-mcp="useCopilotMcp"
          :use-personal-knowledge="usePersonalKnowledge"
          :use-project-knowledge="useProjectKnowledge"
          :auto-create-after-generate="autoCreateAfterGenerate"
          :rag-error-message="ragErrorMessage"
          :rag-source-references="ragSourceReferences"
          :rag-summary="ragSummary"
          @close="showAiGenerateModal = false"
          @generate="generateTasksWithAi"
          @toggle-all="toggleAllAiTasks"
          @toggle-task="toggleAiTaskSelection"
          @reset-generated="aiGeneratedTasks = []; selectedAiTasks = []"
          @batch-create="batchCreateAiTasks"
          @touch-project-knowledge="useProjectKnowledgeTouched = true"
          @update:ai-prompt="aiPrompt = $event"
          @update:use-rag-planning="useRagPlanning = $event"
          @update:use-copilot-mcp="useCopilotMcp = $event"
          @update:use-personal-knowledge="usePersonalKnowledge = $event"
          @update:use-project-knowledge="useProjectKnowledge = $event"
          @update:auto-create-after-generate="autoCreateAfterGenerate = $event"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { toast } from 'vue-sonner';
import { taskService } from '../../services/taskService';
import { timelineService } from '../../services/timelineService';
import { knowledgeService } from '../../services/knowledgeService';
import { copilotService } from '../../services/copilotService';
import { formatDate, formatDateTime } from '../../utils/formatters';
import { downloadFileFromUrl, loadTaskDetailResourcesWithMembers } from '../../utils/taskDetails';
import { useConfirm } from '../../composables/useConfirm';
import { getApiErrorMessage } from '../../utils/apiError';
import { mapToCreateTaskPayload } from '../../utils/payloadMappers';
import ProjectKnowledgePanel from './ProjectKnowledgePanel.vue';
import AiTaskGeneratePanel from './AiTaskGeneratePanel.vue';
import TaskDetailPanel from './TaskDetailPanel.vue';
import TimelineAddTaskModal from './TimelineAddTaskModal.vue';
import TimelineWeeklyReportPanel from './TimelineWeeklyReportPanel.vue';
import TimelineRiskAnalysisPanel from './TimelineRiskAnalysisPanel.vue';
import TimelineSharePanel from './TimelineSharePanel.vue';
import TimelineTaskMemberPanel from './TimelineTaskMemberPanel.vue';
import {
  collectTasksWithPotentiallyDroppedDependencies,
  getDefaultWeeklyReportRange,
  getPriorityBadgeClass,
  getPriorityLabel,
  getWeeklyReportAiSummarySourceLabel,
  mapRagResponseToGeneratedTasks,
  normalizeGeneratedTasks,
  normalizeIdList,
  normalizeStringList,
  toDateOnly,
} from '../../utils/timelineDetailUtils';
import type {
  TimelineDetailDialogProps,
  Task,
  TaskComment,
  TaskCommentSummary,
  TaskFile,
  Subtask,
  TaskMember,
  SearchUserResult,
  AiGeneratedTask,
  CreateTaskPayload,
  TaskPriority,
  TimelineBatchCreateTasksResponse,
  TimelineBatchTaskPayload,
  GenerateTasksResponse,
  AIPlanSuggestionResponse,
  CopilotMcpExecuteResponse,
  CriticalPathAnalysisResponse,
  KnowledgeDocumentEventItem,
  KnowledgeDocumentItem,
  SourceReference,
  WeeklyReportResponse,
  ConflictCheckPayload,
  ResourceConflictResponse,
} from '../../types';

const { confirm } = useConfirm();

const props = defineProps<TimelineDetailDialogProps>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'toggle-task', taskId: number): void;
  (e: 'delete-task', taskId: number): void;
  (e: 'refresh-all'): void;
}>();

// 本元件管理的狀態
const showAddTaskModal = ref(false);
const isSharePanelOpen = ref(false);
const showTaskDetail = ref(false);
const selectedTask = ref<Task | null>(null);
const taskComments = ref<TaskComment[]>([]);
const taskFiles = ref<TaskFile[]>([]);
const taskSubtasks = ref<Subtask[]>([]);
const newSubtaskName = ref('');

const subtaskProgress = computed(() => {
  if (!taskSubtasks.value.length) return 0;
  return Math.round(taskSubtasks.value.filter(s => s.completed).length / taskSubtasks.value.length * 100);
});
const showAiGenerateModal = ref(false);
const aiGeneratedTasks = ref<AiGeneratedTask[]>([]);
const selectedAiTasks = ref<number[]>([]);
const isGeneratingAi = ref(false);
const aiPrompt = ref('');
const useRagPlanning = ref(false);
const useCopilotMcp = ref(true);
const usePersonalKnowledge = ref(true);
const useProjectKnowledge = ref(false);
const useProjectKnowledgeTouched = ref(false);
const autoCreateAfterGenerate = ref(false);
const ragSourceReferences = ref<SourceReference[]>([]);
const ragSummary = ref('');
const ragErrorMessage = ref('');
const projectKnowledgeDocuments = ref<KnowledgeDocumentItem[]>([]);
const projectKnowledgeEvents = ref<KnowledgeDocumentEventItem[]>([]);
const projectKnowledgeLoading = ref(false);
const projectKnowledgeUploading = ref(false);
const projectKnowledgeSelectedIds = ref<number[]>([]);
const projectKnowledgeQuery = ref('');
const projectKnowledgeSort = ref<'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc'>('created_desc');
const projectKnowledgeStatus = ref('');
const projectKnowledgeError = ref('');
const isEditingRemark = ref(false);
const timelineRemark = ref('');
const localRemark = ref('');
const newComment = ref('');
const isSummarizingComments = ref(false);
const commentSummary = ref<TaskCommentSummary | null>(null);
const commentSummaryMeta = ref<{ total_comments?: number; used_comments?: number; truncated?: boolean } | null>(null);
const inputEmail = ref('');
const searchResult = ref<SearchUserResult | null>(null);
const searchError = ref('');
const timelineMembers = ref<TaskMember[]>([]);
const isTaskMemberPanelOpen = ref(false);
const assignTask = ref<Task | null>(null);
const taskMembersForAssign = ref<TaskMember[]>([]);

const taskForm = ref<CreateTaskPayload>({ name: '', start_date: '', end_date: '', priority: 2, tags: '', task_remark: '' });
const addTaskAssigneeIds = ref<number[]>([]);
const addTaskDependencyIds = ref<number[]>([]);
const selectedTaskDependencyIds = ref<number[]>([]);
const isSavingTaskDependencies = ref(false);
const addTaskConflictPreviews = ref<Array<{
  assignee_user_id: number | null;
  assignee_label: string;
  preview: ResourceConflictResponse;
}>>([]);
const conflictAiSuggestionLoadingKey = ref<string | null>(null);
const addTaskConflictSummary = computed(() => {
  const conflicted = addTaskConflictPreviews.value.filter((item) => item.preview.has_conflict);
  const totalSignals = conflicted.reduce((sum, item) => sum + item.preview.conflict_count, 0);
  return {
    hasConflict: conflicted.length > 0,
    totalSignals,
  };
});
const weeklyReport = ref<WeeklyReportResponse | null>(null);
const weeklyReportLoading = ref(false);
const weeklyReportError = ref('');
const isWeeklyReportExpanded = ref(false);
const weeklyReportRange = ref<{ start_date: string; end_date: string }>({ start_date: '', end_date: '' });
const riskAnalysis = ref<CriticalPathAnalysisResponse | null>(null);
const riskAnalysisLoading = ref(false);
const riskAnalysisError = ref('');
const isRiskAnalysisExpanded = ref(false);
const isRiskGraphVisible = ref(false);
const riskGraphVersion = ref(0);

const RISK_GRAPH_NODE_WIDTH = 170;
const RISK_GRAPH_NODE_HEIGHT = 50;
const RISK_GRAPH_X_PADDING = 36;
const RISK_GRAPH_Y_PADDING = 28;
const RISK_GRAPH_COLUMN_GAP = 96;
const RISK_GRAPH_ROW_GAP = 30;

type RiskGraphLayoutNode = {
  task_id: number;
  name: string;
  x: number;
  y: number;
  is_critical: boolean;
  severity: 'high' | 'medium' | 'low' | null;
};

type RiskGraphLayoutEdge = {
  source_task_id: number;
  target_task_id: number;
  is_critical: boolean;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
};

type RiskGraphLayout = {
  width: number;
  height: number;
  nodes: RiskGraphLayoutNode[];
  edges: RiskGraphLayoutEdge[];
};

const toTaskPriority = (value: unknown, fallback: TaskPriority = 2): TaskPriority => {
  const parsed = Number(value);
  if (parsed === 1 || parsed === 2 || parsed === 3) {
    return parsed;
  }
  return fallback;
};

const availableDependencyTasks = computed(() => {
  return props.timelineTasks
    .filter((task) => !task.completed)
    .map((task) => ({
      task_id: task.task_id,
      name: task.name,
    }));
});

const selectedTaskDependencyOptions = computed(() => {
  const currentTaskId = selectedTask.value?.task_id;
  return props.timelineTasks
    .filter((task) => task.task_id !== currentTaskId)
    .map((task) => ({
      task_id: task.task_id,
      name: task.name,
    }));
});

const riskSeverityMap = computed(() => {
  const entries = riskAnalysis.value?.risk_items || [];
  const map = new Map<number, 'high' | 'medium' | 'low'>();

  for (const item of entries) {
    const taskId = Number(item.task_id);
    const severity = String(item.severity || '').toLowerCase();
    if (!Number.isInteger(taskId) || taskId <= 0) {
      continue;
    }
    if (severity === 'high' || severity === 'medium' || severity === 'low') {
      map.set(taskId, severity);
    }
  }

  return map;
});

const riskGraphLayout = computed<RiskGraphLayout | null>(() => {
  const graphNodes = riskAnalysis.value?.graph?.nodes || [];
  const graphEdges = riskAnalysis.value?.graph?.edges || [];
  if (graphNodes.length === 0) {
    return null;
  }

  const nodeIds = new Set<number>(
    graphNodes
      .map((item) => Number(item.task_id))
      .filter((taskId) => Number.isInteger(taskId) && taskId > 0)
  );

  const incomingCount = new Map<number, number>();
  const adjacency = new Map<number, number[]>();
  const levelMap = new Map<number, number>();

  for (const taskId of nodeIds) {
    incomingCount.set(taskId, 0);
    adjacency.set(taskId, []);
    levelMap.set(taskId, 0);
  }

  const validEdges = graphEdges
    .map((edge) => ({
      source_task_id: Number(edge.source_task_id),
      target_task_id: Number(edge.target_task_id),
      is_critical: Boolean(edge.is_critical),
    }))
    .filter((edge) => nodeIds.has(edge.source_task_id) && nodeIds.has(edge.target_task_id));

  for (const edge of validEdges) {
    const children = adjacency.get(edge.source_task_id) || [];
    children.push(edge.target_task_id);
    adjacency.set(edge.source_task_id, children);
    incomingCount.set(edge.target_task_id, (incomingCount.get(edge.target_task_id) || 0) + 1);
  }

  const queue = Array.from(nodeIds)
    .filter((taskId) => (incomingCount.get(taskId) || 0) === 0)
    .sort((a, b) => a - b);
  const visited = new Set<number>();

  while (queue.length > 0) {
    const current = queue.shift() as number;
    visited.add(current);

    const currentLevel = levelMap.get(current) || 0;
    const children = adjacency.get(current) || [];
    for (const next of children) {
      const nextLevel = levelMap.get(next) || 0;
      if (currentLevel + 1 > nextLevel) {
        levelMap.set(next, currentLevel + 1);
      }

      const reducedIncoming = (incomingCount.get(next) || 0) - 1;
      incomingCount.set(next, reducedIncoming);
      if (reducedIncoming === 0) {
        queue.push(next);
      }
    }
  }

  // 若圖中含循環（或降級邊緣案例），仍強制給層級避免無法渲染。
  if (visited.size < nodeIds.size) {
    for (const taskId of nodeIds) {
      if (visited.has(taskId)) {
        continue;
      }
      levelMap.set(taskId, Math.max(levelMap.get(taskId) || 0, 1));
    }
  }

  const groupedByLevel = new Map<number, Array<{ task_id: number; name: string; is_critical: boolean }>>();
  for (const item of graphNodes) {
    const taskId = Number(item.task_id);
    if (!nodeIds.has(taskId)) {
      continue;
    }

    const level = levelMap.get(taskId) || 0;
    const group = groupedByLevel.get(level) || [];
    group.push({
      task_id: taskId,
      name: item.name,
      is_critical: Boolean(item.is_critical),
    });
    groupedByLevel.set(level, group);
  }

  const sortedLevels = Array.from(groupedByLevel.keys()).sort((a, b) => a - b);
  const layoutNodes: RiskGraphLayoutNode[] = [];
  const nodePositionMap = new Map<number, { x: number; y: number }>();
  let maxRows = 1;

  for (const level of sortedLevels) {
    const group = (groupedByLevel.get(level) || []).sort((a, b) => a.task_id - b.task_id);
    maxRows = Math.max(maxRows, group.length);

    group.forEach((node, index) => {
      const x = RISK_GRAPH_X_PADDING + level * (RISK_GRAPH_NODE_WIDTH + RISK_GRAPH_COLUMN_GAP);
      const y = RISK_GRAPH_Y_PADDING + index * (RISK_GRAPH_NODE_HEIGHT + RISK_GRAPH_ROW_GAP);
      const severity = riskSeverityMap.value.get(node.task_id) || null;

      layoutNodes.push({
        task_id: node.task_id,
        name: node.name,
        x,
        y,
        is_critical: node.is_critical,
        severity,
      });

      nodePositionMap.set(node.task_id, { x, y });
    });
  }

  const layoutEdges: RiskGraphLayoutEdge[] = [];
  for (const edge of validEdges) {
    const source = nodePositionMap.get(edge.source_task_id);
    const target = nodePositionMap.get(edge.target_task_id);
    if (!source || !target) {
      continue;
    }

    layoutEdges.push({
      source_task_id: edge.source_task_id,
      target_task_id: edge.target_task_id,
      is_critical: edge.is_critical,
      x1: source.x + RISK_GRAPH_NODE_WIDTH,
      y1: source.y + RISK_GRAPH_NODE_HEIGHT / 2,
      x2: target.x,
      y2: target.y + RISK_GRAPH_NODE_HEIGHT / 2,
    });
  }

  const maxLevel = sortedLevels.length > 0 ? Math.max(...sortedLevels) : 0;
  const width =
    RISK_GRAPH_X_PADDING * 2
    + (maxLevel + 1) * RISK_GRAPH_NODE_WIDTH
    + maxLevel * RISK_GRAPH_COLUMN_GAP;
  const height =
    RISK_GRAPH_Y_PADDING * 2
    + maxRows * RISK_GRAPH_NODE_HEIGHT
    + Math.max(maxRows - 1, 0) * RISK_GRAPH_ROW_GAP;

  return {
    width,
    height,
    nodes: layoutNodes,
    edges: layoutEdges,
  };
});

const getTaskNameById = (taskId: number): string => {
  const matchedTask = props.timelineTasks.find((task) => task.task_id === taskId);
  return matchedTask?.name || `任務 #${taskId}`;
};

const getTimelineMemberName = (memberId: number): string => {
  const member = timelineMembers.value.find((item) => item.user_id === memberId);
  return member?.username || member?.name || `使用者 #${memberId}`;
};


const canManageTaskMembers = (task: Task | null | undefined): boolean => {
  if (!task) return false;
  if (typeof task.can_manage_members === 'boolean') {
    return task.can_manage_members;
  }
  return props.selectedTimeline?.role === 0;
};

const getConflictPreviewKey = (assigneeUserId: number | null): string => {
  return assigneeUserId === null ? 'self' : String(assigneeUserId);
};

const buildConflictPayloadForAddTask = (
  data: CreateTaskPayload,
  target: { assignee_user_id: number | null },
  includeAiSuggestion: boolean,
): ConflictCheckPayload => {
  const payload: ConflictCheckPayload = {
    name: data.name,
    start_date: data.start_date ?? data.end_date,
    end_date: data.end_date,
    priority: data.priority,
    include_ai_suggestion: includeAiSuggestion,
  };

  if (target.assignee_user_id !== null) {
    payload.assignee_user_id = target.assignee_user_id;
  }

  return payload;
};

const buildAddTaskConflictTargets = () => {
  const uniqueIds = Array.from(
    new Set(addTaskAssigneeIds.value.map((id) => Number(id)).filter((id) => Number.isInteger(id) && id > 0))
  );

  if (uniqueIds.length === 0) {
    return [{ assignee_user_id: null, assignee_label: '我自己（預設）' }];
  }

  return uniqueIds.map((memberId) => ({
    assignee_user_id: memberId,
    assignee_label: getTimelineMemberName(memberId),
  }));
};


const fetchWeeklyReport = async () => {
  if (!props.selectedTimeline) return;

  weeklyReportLoading.value = true;
  weeklyReportError.value = '';

  try {
    const { start_date, end_date } = weeklyReportRange.value;
    const res = await timelineService.getWeeklyReport(props.selectedTimeline.id, {
      start_date,
      end_date,
    });
    weeklyReport.value = res.data;
  } catch (err: unknown) {
    weeklyReport.value = null;
    weeklyReportError.value = getApiErrorMessage(err, '取得週報失敗');
  } finally {
    weeklyReportLoading.value = false;
  }
};

const fetchRiskAnalysis = async () => {
  if (!props.selectedTimeline) return;

  riskAnalysisLoading.value = true;
  riskAnalysisError.value = '';

  try {
    const res = await timelineService.getRiskAnalysis(props.selectedTimeline.id);
    riskAnalysis.value = res.data;
  } catch (err: unknown) {
    riskAnalysis.value = null;
    riskAnalysisError.value = getApiErrorMessage(err, '取得風險分析失敗');
  } finally {
    riskAnalysisLoading.value = false;
    riskGraphVersion.value += 1;
  }
};

const rebuildRiskGraph = () => {
  riskGraphVersion.value += 1;
};

const toggleRiskGraph = async () => {
  if (isRiskGraphVisible.value) {
    isRiskGraphVisible.value = false;
    return;
  }

  if (!isRiskAnalysisExpanded.value) {
    isRiskAnalysisExpanded.value = true;
  }

  if (!riskAnalysis.value && props.selectedTimeline) {
    await fetchRiskAnalysis();
  }

  if (!riskAnalysis.value) {
    toast.warning('目前無法載入依賴圖，請稍後再試');
    return;
  }

  isRiskGraphVisible.value = true;
  rebuildRiskGraph();
};

const truncateRiskGraphNodeName = (name: string): string => {
  if (!name) {
    return '未命名任務';
  }

  if (name.length <= 12) {
    return name;
  }
  return `${name.slice(0, 11)}…`;
};

const getRiskGraphNodeFill = (node: RiskGraphLayoutNode): string => {
  if (node.severity === 'high') {
    return '#fee2e2';
  }
  if (node.severity === 'medium') {
    return '#fef3c7';
  }
  if (node.is_critical) {
    return '#ffe4e6';
  }
  return '#f8fafc';
};

const getRiskGraphNodeStroke = (node: RiskGraphLayoutNode): string => {
  if (node.severity === 'high') {
    return '#ef4444';
  }
  if (node.severity === 'medium') {
    return '#f59e0b';
  }
  if (node.is_critical) {
    return '#e11d48';
  }
  return '#94a3b8';
};

const toggleWeeklyReportExpanded = async () => {
  isWeeklyReportExpanded.value = !isWeeklyReportExpanded.value;
  if (isWeeklyReportExpanded.value) {
    await fetchWeeklyReport();
  }
};

const toggleRiskAnalysisExpanded = async () => {
  isRiskAnalysisExpanded.value = !isRiskAnalysisExpanded.value;
  if (isRiskAnalysisExpanded.value) {
    await fetchRiskAnalysis();
  }
};

// 每次開啟新的 selectedTimeline 時重置 remark 狀態
watch(() => props.selectedTimeline, async (val) => {
  if (val) {
    isEditingRemark.value = false;
    timelineRemark.value = val.remark || '';
    localRemark.value = timelineRemark.value;
    isWeeklyReportExpanded.value = false;
    isRiskAnalysisExpanded.value = false;
    weeklyReportRange.value = getDefaultWeeklyReportRange();
    weeklyReport.value = null;
    weeklyReportError.value = '';
    riskAnalysis.value = null;
    riskAnalysisError.value = '';
    isRiskGraphVisible.value = false;
    riskGraphVersion.value = 0;
  } else {
    timelineRemark.value = '';
    localRemark.value = '';
    weeklyReport.value = null;
    weeklyReportError.value = '';
    riskAnalysis.value = null;
    riskAnalysisError.value = '';
    isRiskGraphVisible.value = false;
    riskGraphVersion.value = 0;
  }
}, { immediate: true });

watch(showAiGenerateModal, (opened) => {
  if (!opened) return;
  selectedAiTasks.value = [];
  ragSourceReferences.value = [];
  ragSummary.value = '';
  if (!aiPrompt.value.trim()) {
    aiPrompt.value = timelineRemark.value || '';
  }
});

watch(showAddTaskModal, async (opened) => {
  if (opened && timelineMembers.value.length === 0) {
    await loadMembers();
  }
});

const resetTaskForm = () => {
  taskForm.value = { name: '', start_date: '', end_date: '', priority: 2, tags: '', task_remark: '' };
  addTaskAssigneeIds.value = [];
  addTaskDependencyIds.value = [];
  addTaskConflictPreviews.value = [];
  conflictAiSuggestionLoadingKey.value = null;
};

const runConflictPrecheckForAddTask = async (timelineId: number, data: CreateTaskPayload): Promise<boolean> => {
  if (!data.end_date) {
    addTaskConflictPreviews.value = [];
    return true;
  }

  const targets = buildAddTaskConflictTargets();
  const previews = await Promise.all(
    targets.map(async (target) => {
      const conflictRes = await timelineService.conflictCheck(
        timelineId,
        buildConflictPayloadForAddTask(data, target, false),
      );

      return {
        assignee_user_id: target.assignee_user_id,
        assignee_label: target.assignee_label,
        preview: conflictRes.data,
      };
    })
  );

  addTaskConflictPreviews.value = previews;
  const conflictedPreviews = previews.filter((item) => item.preview.has_conflict);
  if (conflictedPreviews.length === 0) {
    return true;
  }

  const totalSignals = conflictedPreviews.reduce((sum, item) => sum + item.preview.conflict_count, 0);
  const lines = conflictedPreviews
    .slice(0, 3)
    .map((item) => `• ${item.assignee_label}：${item.preview.conflict_count} 個訊號`)
    .join('\n');

  const firstSuggestion = conflictedPreviews.find((item) => item.preview.suggestion)?.preview.suggestion;
  const suggestion = firstSuggestion
    ? `\n\n建議改期：${firstSuggestion.start_date} ~ ${firstSuggestion.end_date}`
    : '';

  return await confirm({
    title: `偵測到 ${totalSignals} 個衝突訊號，仍要新增？`,
    message: `${lines}${suggestion}`,
  });
};

const requestAddTaskConflictAiSuggestion = async (assigneeUserId: number | null) => {
  if (!props.selectedTimeline) return;

  if (!taskForm.value.end_date) {
    toast.warning('請先填寫截止日期再產生 AI 衝突建議');
    return;
  }

  const payloadData = mapToCreateTaskPayload({
    ...taskForm.value,
    timeline_id: props.selectedTimeline.id,
    assignee_user_ids: normalizeIdList(addTaskAssigneeIds.value),
    depends_on_task_ids: normalizeIdList(addTaskDependencyIds.value),
  });

  const key = getConflictPreviewKey(assigneeUserId);
  conflictAiSuggestionLoadingKey.value = key;

  try {
    const target = {
      assignee_user_id: assigneeUserId,
      assignee_label: assigneeUserId === null ? '我自己（預設）' : getTimelineMemberName(assigneeUserId),
    };

    const conflictRes = await timelineService.conflictCheck(
      props.selectedTimeline.id,
      buildConflictPayloadForAddTask(payloadData, target, true),
    );

    addTaskConflictPreviews.value = addTaskConflictPreviews.value.map((item) => {
      if (item.assignee_user_id !== assigneeUserId) {
        return item;
      }
      return {
        ...item,
        preview: conflictRes.data,
      };
    });

    if (conflictRes.data.ai_suggestion) {
      toast.success('AI 衝突建議已更新');
    } else {
      toast.info('目前沒有可生成的 AI 衝突建議');
    }
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '取得 AI 衝突建議失敗'));
  } finally {
    conflictAiSuggestionLoadingKey.value = null;
  }
};

const runConflictPrecheckForTaskMemberAssignment = async (task: Task, member: TaskMember): Promise<boolean> => {
  if (!props.selectedTimeline) return true;

  const endDate = toDateOnly(task.end_date);
  if (!endDate) return true;

  try {
    const res = await timelineService.conflictCheck(props.selectedTimeline.id, {
      task_id: task.task_id,
      name: task.name,
      start_date: toDateOnly(task.start_date) ?? endDate,
      end_date: endDate,
      assignee_user_id: member.user_id,
      priority: task.priority,
      include_ai_suggestion: false,
    });

    if (!res.data.has_conflict) {
      return true;
    }

    const lines = [
      `日期衝突：${res.data.conflicts.length} 個`,
      `跨專案衝突：${res.data.cross_project_conflict_count ?? 0} 個`,
      `過載日：${res.data.workload_overload_count ?? 0} 天`,
    ].join('\n');

    const suggestion = res.data.suggestion
      ? `\n\n建議改期：${res.data.suggestion.start_date} ~ ${res.data.suggestion.end_date}`
      : '';

    return await confirm({
      title: `指派給 ${member.name} 前偵測到衝突，仍要指派？`,
      message: `${lines}${suggestion}`,
    });
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '檢查衝突失敗'));
    return false;
  }
};

// ────────────── 備註 ──────────────
const startEditRemark = () => {
  localRemark.value = timelineRemark.value;
  isEditingRemark.value = true;
};

const saveRemark = async () => {
  if (!props.selectedTimeline) return;
  try {
    await timelineService.updateRemark(props.selectedTimeline.id, localRemark.value);
    timelineRemark.value = localRemark.value;
    isEditingRemark.value = false;
    emit('refresh-all');
  } catch { toast.error('更新備註失敗'); }
};

// ────────────── 任務 ──────────────
const handleAddTask = async () => {
  if (!props.selectedTimeline) return;
  try {
    const selectedAssigneeIds = normalizeIdList(addTaskAssigneeIds.value);
    const dependencyIds = normalizeIdList(addTaskDependencyIds.value);

    const data = mapToCreateTaskPayload({
      ...taskForm.value,
      timeline_id: props.selectedTimeline.id,
      assignee_user_ids: selectedAssigneeIds.length > 0 ? selectedAssigneeIds : undefined,
      depends_on_task_ids: dependencyIds,
    });

    const shouldProceed = await runConflictPrecheckForAddTask(props.selectedTimeline.id, data);
    if (!shouldProceed) {
      return;
    }

    await taskService.create(data);
    showAddTaskModal.value = false;
    resetTaskForm();
    emit('refresh-all');
    if (isWeeklyReportExpanded.value) {
      void fetchWeeklyReport();
    }
    if (isRiskAnalysisExpanded.value) {
      void fetchRiskAnalysis();
    }
  } catch { toast.error('新增任務失敗'); }
};

const openTaskDetail = async (task: Task) => {
  selectedTask.value = { ...task };
  assignTask.value = { ...task };
  selectedTaskDependencyIds.value = normalizeIdList(task.depends_on_task_ids || []);
  taskComments.value = [];
  commentSummary.value = null;
  commentSummaryMeta.value = null;
  taskFiles.value = [];
  taskSubtasks.value = [];
  taskMembersForAssign.value = [];
  showTaskDetail.value = true;
  try {
    const resources = await loadTaskDetailResourcesWithMembers(task.task_id);
    taskComments.value = resources.comments;
    taskFiles.value = resources.files;
    taskSubtasks.value = resources.subtasks;
    taskMembersForAssign.value = resources.members;
  } catch (err) {
    console.error('取得任務詳情失敗:', err);
  }
  // 載入專案成員供快速指派
  if (timelineMembers.value.length === 0) await loadMembers();
};

const saveSelectedTaskDependencies = async () => {
  if (!selectedTask.value) return;

  const dependencyIds = normalizeIdList(selectedTaskDependencyIds.value).filter(
    (taskId) => taskId !== selectedTask.value?.task_id,
  );

  isSavingTaskDependencies.value = true;
  try {
    await taskService.update(selectedTask.value.task_id, {
      depends_on_task_ids: dependencyIds,
    });

    if (selectedTask.value) {
      selectedTask.value.depends_on_task_ids = dependencyIds;
    }
    selectedTaskDependencyIds.value = dependencyIds;

    emit('refresh-all');
    if (isRiskAnalysisExpanded.value) {
      void fetchRiskAnalysis();
    }
    toast.success('前置依賴已更新');
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '更新前置依賴失敗'));
  } finally {
    isSavingTaskDependencies.value = false;
  }
};

const addSubtask = async () => {
  if (!newSubtaskName.value.trim() || !selectedTask.value) return;
  try {
    await taskService.createSubtask(selectedTask.value.task_id, { name: newSubtaskName.value.trim() });
    newSubtaskName.value = '';
    const res = await taskService.getSubtasks(selectedTask.value.task_id);
    taskSubtasks.value = res.data || [];
  } catch { toast.error('新增子任務失敗'); }
};

const toggleSubtask = async (subtask: Subtask) => {
  if (!selectedTask.value) return;
  try {
    await taskService.toggleSubtask(selectedTask.value.task_id, subtask.id);
    const res = await taskService.getSubtasks(selectedTask.value.task_id);
    taskSubtasks.value = res.data || [];
  } catch { toast.error('更新子任務狀態失敗'); }
};

const deleteSubtask = async (subtask: Subtask) => {
  if (!selectedTask.value) return;
  if (!await confirm({ title: '確定要刪除此子任務？', danger: true })) return;
  try {
    await taskService.deleteSubtask(selectedTask.value.task_id, subtask.id);
    taskSubtasks.value = taskSubtasks.value.filter(s => s.id !== subtask.id);
  } catch { toast.error('刪除子任務失敗'); }
};

const addComment = async () => {
  if (!newComment.value.trim() || !selectedTask.value) return;
  try {
    await taskService.addComment(selectedTask.value.task_id, newComment.value.trim());
    newComment.value = '';
    const res = await taskService.getComments(selectedTask.value.task_id);
    taskComments.value = res.data || [];
    commentSummary.value = null;
    commentSummaryMeta.value = null;
  } catch { toast.error('新增留言失敗'); }
};

const deleteComment = async (commentId: number) => {
  if (!selectedTask.value) return;
  if (!await confirm({ title: '確定要刪除此留言？', danger: true })) return;
  try {
    await taskService.deleteComment(selectedTask.value.task_id, commentId);
    taskComments.value = taskComments.value.filter(c => c.comment_id !== commentId);
    commentSummary.value = null;
    commentSummaryMeta.value = null;
  } catch { toast.error('刪除留言失敗'); }
};

const summarizeComments = async () => {
  if (!selectedTask.value) return;
  isSummarizingComments.value = true;
  try {
    const res = await taskService.summarizeComments(selectedTask.value.task_id);
    commentSummary.value = res.data.summary;
    commentSummaryMeta.value = res.data.meta;
    if (res.data.message) {
      toast.info(res.data.message);
    } else {
      toast.success('AI 摘要完成');
    }
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, 'AI 摘要失敗'));
  } finally {
    isSummarizingComments.value = false;
  }
};

const handleFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement | null;
  const file = target?.files?.[0];
  if (!file || !selectedTask.value) return;
  if (file.size > 10 * 1024 * 1024) { toast.warning('檔案大小不可超過 10MB'); return; }
  const formData = new FormData();
  formData.append('file', file);
  try {
    await taskService.uploadFile(selectedTask.value.task_id, formData);
    const res = await taskService.getFiles(selectedTask.value.task_id);
    taskFiles.value = res.data || [];
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '上傳失敗'));
  }
};

const deleteFile = async (fileId: number) => {
  if (!selectedTask.value) return;
  if (!await confirm({ title: '確定要刪除此附件？', danger: true })) return;
  try {
    await taskService.deleteFile(selectedTask.value.task_id, fileId);
    taskFiles.value = taskFiles.value.filter(f => f.id !== fileId);
  } catch { toast.error('刪除附件失敗'); }
};

// ────────────── 任務成員指派 ──────────────
const openTaskMemberPanel = async (task: Task) => {
  if (!canManageTaskMembers(task)) {
    toast.error('你沒有管理此任務成員的權限');
    return;
  }

  assignTask.value = task;
  isTaskMemberPanelOpen.value = true;
};

watch(isTaskMemberPanelOpen, async (val: boolean) => {
  if (val && assignTask.value) {
    await loadTaskMembersForAssign();
    if (timelineMembers.value.length === 0) await loadMembers();
  } else {
    taskMembersForAssign.value = [];
  }
});

const loadTaskMembersForAssign = async () => {
  if (!assignTask.value) return;
  try {
    const res = await taskService.getMembers(assignTask.value.task_id);
    taskMembersForAssign.value = res.data || [];
  } catch { taskMembersForAssign.value = []; }
};

const quickAssignTaskMember = async (member: TaskMember) => {
  if (!assignTask.value) return;
  if (!canManageTaskMembers(assignTask.value)) {
    toast.error('你沒有管理此任務成員的權限');
    return;
  }

  const canAssign = await runConflictPrecheckForTaskMemberAssignment(assignTask.value, member);
  if (!canAssign) {
    return;
  }

  try {
    await taskService.addMember(assignTask.value.task_id, member.user_id);
    await loadTaskMembersForAssign();
    toast.success(`已指派 ${member.username || member.name}`);
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '指派失敗'));
  }
};

const kickAssignedMember = async (member: TaskMember) => {
  if (!assignTask.value) return;
  if (!canManageTaskMembers(assignTask.value)) {
    toast.error('你沒有管理此任務成員的權限');
    return;
  }

  if (!await confirm({ title: `確定要將「${member.name}」從此任務移除？`, danger: true })) return;
  try {
    await taskService.removeMember(assignTask.value.task_id, member.user_id);
    await loadTaskMembersForAssign();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '移除失敗'));
  }
};

const setAssignedTaskOwner = async (member: TaskMember) => {
  if (!assignTask.value) return;
  if (!canManageTaskMembers(assignTask.value)) {
    toast.error('你沒有管理此任務成員的權限');
    return;
  }

  if (!await confirm({ title: `將「${member.name}」設為主責人？`, message: '原主責人會自動改為協作者。' })) return;

  try {
    await taskService.updateMemberRole(assignTask.value.task_id, member.user_id, 0);
    await loadTaskMembersForAssign();
    emit('refresh-all');
    toast.success(`已將 ${member.name} 設為主責人`);
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '設定主責人失敗'));
  }
};

// ────────────── 成員管理 ──────────────
const loadMembers = async () => {
  if (!props.selectedTimeline) return;
  try {
    const res = await timelineService.getMembers(props.selectedTimeline.id);
    timelineMembers.value = res.data;
  } catch { timelineMembers.value = []; }
};

watch(isSharePanelOpen, (val: boolean) => {
  if (val) loadMembers();
  else { inputEmail.value = ''; searchResult.value = null; searchError.value = ''; }
});

const searchUser = async () => {
  if (!inputEmail.value.trim()) return;
  if (!props.selectedTimeline) {
    searchError.value = '請先選擇專案';
    return;
  }
  searchResult.value = null; searchError.value = '';
  try {
    const res = await timelineService.searchUser(props.selectedTimeline.id, inputEmail.value);
    searchResult.value = res.data;
  } catch (err: unknown) {
    searchError.value = getApiErrorMessage(err, '找不到用戶');
  }
};

const confirmShare = async () => {
  if (!searchResult.value || !props.selectedTimeline) return;
  try {
    await timelineService.addMember(props.selectedTimeline.id, searchResult.value.id);
    inputEmail.value = ''; searchResult.value = null;
    await loadMembers();
    toast.success('邀請成功！');
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '邀請失敗'));
  }
};

const kickMember = async (member: TaskMember) => {
  if (!props.selectedTimeline) return;
  if (!await confirm({ title: `確定要將「${member.username || member.name}」移出此專案？`, danger: true })) return;
  try {
    await timelineService.removeMember(props.selectedTimeline.id, member.user_id);
    await loadMembers();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '移除成員失敗'));
  }
};

// ────────────── AI 生成 ──────────────
const buildAiDescription = (): string => {
  const prompt = aiPrompt.value.trim();
  if (prompt) return prompt;

  const remark = timelineRemark.value.trim();
  if (remark) return remark;

  return `請為「${props.selectedTimeline?.name || '此專案'}」生成可執行的任務拆解，含優先順序。`;
};


const generateTasksWithAi = async () => {
  if (!props.selectedTimeline) return;

  const description = buildAiDescription();
  isGeneratingAi.value = true;
  ragSourceReferences.value = [];
  ragSummary.value = '';
  ragErrorMessage.value = '';

  try {
    if (useRagPlanning.value) {
      const ragPayload = {
        request: description,
        use_personal_knowledge: usePersonalKnowledge.value,
        use_project_knowledge: useProjectKnowledge.value,
        project_id: props.selectedTimeline.id,
        max_sources: 8,
      };
      const res = await timelineService.suggestPlan(ragPayload);
      const payload: AIPlanSuggestionResponse = res.data;
      aiGeneratedTasks.value = mapRagResponseToGeneratedTasks(payload);
      ragSourceReferences.value = Array.isArray(payload.source_references) ? payload.source_references : [];
      ragSummary.value = payload.summary || '';
    } else if (useCopilotMcp.value) {
      const res = await copilotService.executeMcp({
        message: description,
        context: {
          timeline_id: props.selectedTimeline.id,
          timeline_name: props.selectedTimeline.name,
        },
        preferred_tool: 'timeline_generate_tasks',
        tool_arguments: {
          timeline_id: props.selectedTimeline.id,
          project_name: props.selectedTimeline.name,
          description,
        },
        // 改進：永遠不在後端自動建立，改由前端顯示預覽讓用戶確認
        auto_create_generated_tasks: false,
      });

      const payload: CopilotMcpExecuteResponse = res.data;
      aiGeneratedTasks.value = normalizeGeneratedTasks(payload.result);
    } else {
      const res = await timelineService.generateTasks(props.selectedTimeline.id, {
        name: props.selectedTimeline.name,
        description,
      });
      const payload: GenerateTasksResponse = res.data;
      aiGeneratedTasks.value = normalizeGeneratedTasks(payload);
    }

    if (aiGeneratedTasks.value.length === 0) {
      toast.info('目前沒有可新增的任務建議，可調整需求描述後再試。');
      return;
    }

    // 改進：如果勾選「生成後直接建立」，預設全選；否則清空選擇，讓用戶手動選
    selectedAiTasks.value = autoCreateAfterGenerate.value 
      ? aiGeneratedTasks.value.map((_, i) => i)  // 全選
      : [];  // 空選，用戶手動選
  } catch (err: unknown) {
    const message = getApiErrorMessage(err, 'AI 生成失敗，請稍後再試');
    if (useRagPlanning.value) {
      ragErrorMessage.value = message;
    }
    toast.error(message);
  } finally {
    isGeneratingAi.value = false;
  }
};

const toggleAiTaskSelection = (index: number) => {
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
  
  // 最後確認：讓用戶再次確認要建立的任務數量
  if (!await confirm({ 
    title: `確定要新增 ${selectedAiTasks.value.length} 個任務？`,
    message: '建立後可在任務列表中編輯或刪除。'
  })) {
    return;
  }
  
  const timelineId = props.selectedTimeline.id;
  const tasksToCreate: TimelineBatchTaskPayload[] = selectedAiTasks.value
    .map(i => aiGeneratedTasks.value[i])
    .filter((task): task is AiGeneratedTask => Boolean(task))
    .map(task => {
      const estimatedDays = Number(task.estimated_days);
      return {
        task_id: task.task_id,
        isExisting: Boolean(task.isExisting),
        name: task.name,
        start_date: task.start_date ?? null,
        end_date: task.end_date ?? null,
        priority: toTaskPriority(task.priority),
        status: task.status || 'pending',
        estimated_days: Number.isFinite(estimatedDays) && estimatedDays > 0 ? estimatedDays : 3,
        tags: task.tags ?? null,
        task_remark: task.task_remark ?? task.remark ?? null,
        timeline_id: timelineId,
        depends_on_task_ids: normalizeIdList(task.depends_on_task_ids || []),
        depends_on_task_refs: normalizeStringList(task.depends_on_task_refs),
      };
    });

  const affectedTaskNames = collectTasksWithPotentiallyDroppedDependencies(tasksToCreate);

  try {
    const res = await timelineService.batchCreateTasks(timelineId, tasksToCreate);
    const payload: TimelineBatchCreateTasksResponse = res.data;
    const ignoredDependencyRefs = Number(payload.ignored_dependency_refs || 0);
    const ignoredDependencyIds = Number(payload.ignored_dependency_ids || 0);

    if (ignoredDependencyRefs + ignoredDependencyIds > 0) {
      const previewNames = affectedTaskNames.slice(0, 5);
      const remainingCount = Math.max(0, affectedTaskNames.length - previewNames.length);

      if (previewNames.length > 0) {
        const remainingText = remainingCount > 0 ? `（另 ${remainingCount} 項）` : '';
        toast.info(`小提示：以下任務有前置依賴未帶入，可於任務介面補設定：${previewNames.join('、')}${remainingText}`);
      } else {
        toast.info('小提示：部分任務前置依賴未帶入，可於任務介面補設定。');
      }
    }

    showAiGenerateModal.value = false;
    aiGeneratedTasks.value = [];
    selectedAiTasks.value = [];
    ragSourceReferences.value = [];
    ragSummary.value = '';
    emit('refresh-all');
  } catch (err: unknown) { toast.error(getApiErrorMessage(err, '批量新增失敗')); }
};

const downloadFile = async (url: string, originalFilename: string) => {
  try {
    await downloadFileFromUrl(url, originalFilename);
  } catch {
    toast.error('下載失敗，請稍後再試');
  }
};

const fetchProjectKnowledgeDocuments = async () => {
  if (!props.selectedTimeline) return;
  projectKnowledgeLoading.value = true;
  projectKnowledgeError.value = '';
  try {
    const res = await knowledgeService.listDocuments({
      project_id: props.selectedTimeline.id,
      q: projectKnowledgeQuery.value || undefined,
      sort: projectKnowledgeSort.value,
      status: projectKnowledgeStatus.value || undefined,
      limit: 50,
      offset: 0,
    });
    projectKnowledgeDocuments.value = res.data.documents || [];
    if (!useProjectKnowledgeTouched.value && projectKnowledgeDocuments.value.some(doc => doc.status === 'ready')) {
      useProjectKnowledge.value = true;
    }
  } catch (err: unknown) {
    projectKnowledgeError.value = getApiErrorMessage(err, '讀取專案檔案失敗');
  } finally {
    projectKnowledgeLoading.value = false;
  }
};

const fetchProjectKnowledgeEvents = async () => {
  if (!props.selectedTimeline) return;
  try {
    const res = await knowledgeService.listDocumentEvents({
      project_id: props.selectedTimeline.id,
      limit: 10,
      offset: 0,
    });
    projectKnowledgeEvents.value = res.data.events || [];
  } catch {
    projectKnowledgeEvents.value = [];
  }
};

const toggleKnowledgeSelection = (documentId: number) => {
  const idx = projectKnowledgeSelectedIds.value.indexOf(documentId);
  if (idx >= 0) projectKnowledgeSelectedIds.value.splice(idx, 1);
  else projectKnowledgeSelectedIds.value.push(documentId);
};

const handleProjectKnowledgeUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement | null;
  const file = target?.files?.[0];
  if (!file || !props.selectedTimeline) return;
  projectKnowledgeUploading.value = true;
  try {
    await knowledgeService.uploadDocument(file, props.selectedTimeline.id);
    toast.success('檔案已上傳');
    await fetchProjectKnowledgeDocuments();
    await fetchProjectKnowledgeEvents();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '上傳失敗'));
  } finally {
    projectKnowledgeUploading.value = false;
  }
};

const batchDeleteProjectKnowledge = async () => {
  if (!props.selectedTimeline || projectKnowledgeSelectedIds.value.length === 0) return;
  if (!await confirm({ title: `確定刪除 ${projectKnowledgeSelectedIds.value.length} 份檔案？`, danger: true })) return;
  try {
    await knowledgeService.batchDeleteDocuments(props.selectedTimeline.id, projectKnowledgeSelectedIds.value);
    projectKnowledgeSelectedIds.value = [];
    await fetchProjectKnowledgeDocuments();
    await fetchProjectKnowledgeEvents();
    toast.success('批次刪除完成');
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '批次刪除失敗'));
  }
};

const batchReindexProjectKnowledge = async () => {
  if (!props.selectedTimeline || projectKnowledgeSelectedIds.value.length === 0) return;
  try {
    await knowledgeService.batchReindexDocuments(props.selectedTimeline.id, projectKnowledgeSelectedIds.value);
    await fetchProjectKnowledgeDocuments();
    await fetchProjectKnowledgeEvents();
    toast.success('批次重建完成');
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '批次重建失敗'));
  }
};

const createKnowledgeBlobUrl = (blob: Blob) => URL.createObjectURL(blob);

const downloadProjectKnowledgeDocument = async (document: KnowledgeDocumentItem) => {
  if (!props.selectedTimeline) return;
  try {
    const res = await knowledgeService.downloadDocumentFile(document.id, props.selectedTimeline.id);
    const blobUrl = createKnowledgeBlobUrl(res.data);
    const anchor = window.document.createElement('a');
    anchor.href = blobUrl;
    anchor.download = document.original_filename || document.filename || `knowledge-${document.id}`;
    window.document.body.appendChild(anchor);
    anchor.click();
    window.document.body.removeChild(anchor);
    URL.revokeObjectURL(blobUrl);
    await fetchProjectKnowledgeEvents();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '下載檔案失敗'));
  }
};

const previewProjectKnowledgeDocument = async (document: KnowledgeDocumentItem) => {
  if (!props.selectedTimeline) return;
  try {
    const res = await knowledgeService.previewDocumentFile(document.id, props.selectedTimeline.id);
    const blobUrl = createKnowledgeBlobUrl(res.data);
    window.open(blobUrl, '_blank', 'noopener,noreferrer');
    window.setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
    await fetchProjectKnowledgeEvents();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '預覽檔案失敗'));
  }
};

watch(
  () => props.selectedTimeline?.id,
  async (timelineId) => {
    if (!timelineId) return;
    projectKnowledgeSelectedIds.value = [];
    await fetchProjectKnowledgeDocuments();
    await fetchProjectKnowledgeEvents();
  },
  { immediate: true },
);
</script>
