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
          <div v-if="!isEditingRemark && !timelineRemark" class="mb-4">
            <button @click="isEditingRemark = true" class="text-sm text-gray-400 hover:text-primary transition-colors flex items-center gap-1">
              <span>✏️</span> 新增備註
            </button>
          </div>
          <div v-if="!isEditingRemark && timelineRemark" class="mb-4 p-4 bg-yellow-50/70 border border-yellow-100 rounded-xl">
            <div class="flex items-start justify-between">
              <p class="text-sm text-gray-600">{{ timelineRemark }}</p>
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
              <button v-if="selectedTimeline?.role === 0" @click.stop="openTaskMemberPanel(task)" class="opacity-0 group-hover:opacity-100 text-indigo-400 hover:text-indigo-600 transition-all text-sm" title="指派成員">👥</button>
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

    <!-- 任務成員指派 Panel -->
    <div v-if="isTaskMemberPanelOpen" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-md animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center">
          <h3 class="text-lg font-semibold text-gray-800">👥 任務成員 — {{ assignTask?.name }}</h3>
          <button @click="isTaskMemberPanelOpen = false" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <div class="p-5 space-y-4">
          <!-- 現有任務成員 -->
          <div>
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">目前成員</p>
            <div v-if="taskMembersForAssign.length === 0" class="text-center py-3 text-gray-400 text-sm">尚無指派成員</div>
            <div v-else class="space-y-2">
              <div v-for="member in taskMembersForAssign" :key="member.user_id" class="flex items-center justify-between p-2.5 bg-gray-50 rounded-xl">
                <div class="flex items-center gap-2.5">
                  <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
                    {{ (member.name || '?')[0].toUpperCase() }}
                  </div>
                  <div>
                    <p class="text-sm font-medium text-gray-800">{{ member.name }}</p>
                    <p class="text-xs text-gray-500">{{ member.email }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-1.5">
                  <span :class="['px-2 py-0.5 text-xs font-medium rounded-full', member.role === 0 ? 'bg-primary/10 text-primary' : 'bg-gray-100 text-gray-500']">
                    {{ member.role === 0 ? '負責人' : '協作者' }}
                  </span>
                  <button
                    v-if="member.role !== 0"
                    @click="setAssignedTaskOwner(member)"
                    class="px-2 py-1 text-[11px] font-medium rounded-lg bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
                  >設為主責</button>
                  <button v-if="member.role !== 0" @click="kickAssignedMember(member)" class="w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors text-sm font-bold">✕</button>
                </div>
              </div>
            </div>
          </div>
          <!-- 快速指派：專案成員 -->
          <div class="border-t border-gray-100 pt-4">
            <p class="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">專案成員快速指派</p>
            <div v-if="timelineMembers.length === 0" class="text-center py-3 text-gray-400 text-sm">載入中...</div>
            <template v-else>
              <div v-if="timelineMembers.filter(m => !taskMembersForAssign.some(tm => tm.user_id === m.user_id)).length === 0" class="text-center py-3 text-gray-400 text-sm">所有專案成員皆已加入此任務</div>
              <div v-else class="space-y-2">
                <div
                  v-for="m in timelineMembers.filter(m => !taskMembersForAssign.some(tm => tm.user_id === m.user_id))"
                  :key="m.user_id"
                  class="flex items-center justify-between p-2.5 bg-indigo-50 rounded-xl"
                >
                  <div class="flex items-center gap-2.5">
                    <div class="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center text-sm font-bold text-indigo-600 shrink-0">
                      {{ (m.username || m.name || '?')[0].toUpperCase() }}
                    </div>
                    <div>
                      <p class="text-sm font-medium text-gray-800">{{ m.username || m.name }}</p>
                      <p class="text-xs text-gray-500">{{ m.email }}</p>
                    </div>
                  </div>
                  <button @click="quickAssignTaskMember(m)" class="px-3 py-1 bg-primary text-white text-xs font-medium rounded-lg hover:brightness-110 transition-all">指派</button>
                </div>
              </div>
            </template>
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
          <!-- 基本資訊 -->
          <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
            <div><p class="text-xs text-gray-500 mb-1">開始日期</p><p class="font-medium text-gray-800">{{ formatDate(selectedTask.start_date) || '未設定' }}</p></div>
            <div><p class="text-xs text-gray-500 mb-1">截止日期</p><p class="font-medium text-gray-800">{{ formatDate(selectedTask.end_date) || '未設定' }}</p></div>
          </div>
          <div v-if="selectedTask.task_remark" class="p-4 bg-yellow-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-2">📝 備註</h4>
            <p class="text-gray-600 text-sm">{{ selectedTask.task_remark }}</p>
          </div>

          <!-- ── 成員指派區 ── -->
          <div v-if="selectedTimeline?.role === 0" class="p-4 bg-indigo-50/60 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span>👥</span> 指派成員
            </h4>
            <!-- 已指派成員 -->
            <div v-if="taskMembersForAssign.length > 0" class="flex flex-wrap gap-2 mb-3">
              <div
                v-for="member in taskMembersForAssign"
                :key="member.user_id"
                class="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium"
                :class="member.role === 0 ? 'bg-primary/20 text-primary' : 'bg-white border border-gray-200 text-gray-700'"
              >
                <span>{{ member.name }}</span>
                <span class="text-gray-400 text-[10px]">{{ member.role === 0 ? '負責人' : '協作者' }}</span>
                <button
                  v-if="member.role !== 0"
                  @click="setAssignedTaskOwner(member)"
                  class="ml-0.5 px-1.5 py-0.5 text-[10px] rounded-md bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
                >主責</button>
                <button
                  v-if="member.role !== 0"
                  @click="kickAssignedMember(member)"
                  class="ml-0.5 text-gray-400 hover:text-red-500 transition-colors leading-none"
                >✕</button>
              </div>
            </div>
            <div v-else class="text-xs text-gray-400 mb-3">尚未指派任何成員</div>
            <!-- 專案成員快速指派 -->
            <div v-if="timelineMembers.length > 0">
              <p class="text-xs text-gray-500 mb-2">快速指派專案成員：</p>
              <div class="flex flex-wrap gap-2">
                <button
                  v-for="m in timelineMembers.filter(m => !taskMembersForAssign.some(tm => tm.user_id === m.user_id))"
                  :key="m.user_id"
                  @click="quickAssignTaskMember(m)"
                  class="flex items-center gap-1.5 px-3 py-1 bg-white border border-indigo-200 text-indigo-700 text-xs font-medium rounded-full hover:bg-indigo-100 transition-colors"
                >
                  <span class="w-5 h-5 bg-indigo-100 rounded-full flex items-center justify-center font-bold text-[10px]">{{ (m.username || m.name || '?')[0].toUpperCase() }}</span>
                  {{ m.username || m.name }}
                </button>
                <span v-if="timelineMembers.filter(m => !taskMembersForAssign.some(tm => tm.user_id === m.user_id)).length === 0" class="text-xs text-gray-400">所有成員已加入</span>
              </div>
            </div>
          </div>

          <!-- ── 子任務區 ── -->
          <div>
            <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span>📋</span> 子任務
              <span class="text-sm font-normal text-gray-500">({{ taskSubtasks.filter(s => s.completed).length }}/{{ taskSubtasks.length }})</span>
            </h4>
            <div v-if="taskSubtasks.length > 0" class="h-2 bg-gray-200 rounded-full overflow-hidden mb-4">
              <div class="h-full bg-primary rounded-full transition-all duration-300" :style="{ width: subtaskProgress + '%' }"></div>
            </div>
            <div class="space-y-2 mb-3">
              <div v-for="subtask in taskSubtasks" :key="subtask.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group hover:bg-gray-100 transition-colors">
                <input type="checkbox" :checked="subtask.completed" @change="toggleSubtask(subtask)" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" />
                <span :class="['flex-1 text-sm', subtask.completed ? 'line-through text-gray-400' : 'text-gray-700']">{{ subtask.name }}</span>
                <button @click="deleteSubtask(subtask)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all">🗑️</button>
              </div>
              <div v-if="taskSubtasks.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無子任務</div>
            </div>
            <div class="flex gap-2">
              <input v-model="newSubtaskName" type="text" placeholder="輸入子任務名稱..." @keyup.enter="addSubtask" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
              <button @click="addSubtask" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">新增</button>
            </div>
          </div>

          <!-- ── 附件區 ── -->
          <div>
            <div class="flex items-center justify-between mb-3">
              <h4 class="font-semibold text-gray-700 flex items-center gap-2">
                <span>📎</span> 附件
                <span class="text-xs text-gray-400 font-normal">({{ taskFiles.length }})</span>
              </h4>
              <label class="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-lg hover:bg-primary/20 transition-colors">
                <span>＋</span> 上傳檔案
                <input ref="fileInput" type="file" class="hidden"
                  accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.csv,.mp4,.mov"
                  @change="handleFileUpload" />
              </label>
            </div>
            <div v-if="taskFiles.length === 0" class="text-center py-6 text-gray-400 text-sm bg-gray-50 rounded-xl border border-dashed border-gray-200">
              尚無附件，點擊「上傳檔案」新增
            </div>
            <div v-else class="space-y-2">
              <div v-for="file in taskFiles" :key="file.id"
                class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors group">
                <img v-if="isImageFile(file.original_filename)"
                  :src="`${apiBaseUrl}/tasks/files/${file.filename}`"
                  class="w-12 h-12 object-cover rounded-lg border border-gray-200 shrink-0"
                  :alt="file.original_filename" />
                <span v-else class="text-3xl shrink-0">{{ getFileIcon(file.original_filename) }}</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-medium text-gray-700 truncate">{{ file.original_filename }}</p>
                  <p class="text-xs text-gray-400">{{ formatFileSize(file.file_size) }} · {{ formatDateTime(file.uploaded_at) }}</p>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click="downloadFile(`${apiBaseUrl}/tasks/files/${file.filename}`, file.original_filename)"
                    class="w-8 h-8 flex items-center justify-center text-primary hover:bg-primary/10 rounded-lg transition-colors"
                    title="下載">⬇️</button>
                  <button @click="deleteFile(file.id)"
                    class="w-8 h-8 flex items-center justify-center text-red-400 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
                    title="刪除">🗑️</button>
                </div>
              </div>
            </div>
          </div>

          <!-- ── 留言區 ── -->
          <div>
            <div class="mb-4 flex items-center justify-between gap-3">
              <h4 class="font-semibold text-gray-700 flex items-center gap-2">
                <span>💬</span> 留言
                <span class="text-xs text-gray-400 font-normal">({{ taskComments.length }})</span>
              </h4>
              <button
                @click="summarizeComments"
                :disabled="isSummarizingComments"
                class="px-3 py-1.5 bg-violet-100 text-violet-700 text-xs font-semibold rounded-lg hover:bg-violet-200 transition-colors disabled:opacity-50"
              >
                {{ isSummarizingComments ? '摘要中...' : '🤖 AI 摘要' }}
              </button>
            </div>

            <div v-if="commentSummary" class="mb-4 p-4 bg-violet-50 border border-violet-100 rounded-xl text-sm text-gray-700 space-y-3">
              <div>
                <p class="font-semibold text-violet-800 mb-1">決議</p>
                <ul v-if="commentSummary.decisions.length" class="list-disc list-inside space-y-1">
                  <li v-for="(item, idx) in commentSummary.decisions" :key="`d-${idx}`">{{ item }}</li>
                </ul>
                <p v-else class="text-gray-400">暫無</p>
              </div>
              <div>
                <p class="font-semibold text-violet-800 mb-1">風險</p>
                <ul v-if="commentSummary.risks.length" class="list-disc list-inside space-y-1">
                  <li v-for="(item, idx) in commentSummary.risks" :key="`r-${idx}`">{{ item }}</li>
                </ul>
                <p v-else class="text-gray-400">暫無</p>
              </div>
              <div>
                <p class="font-semibold text-violet-800 mb-1">下一步</p>
                <ul v-if="commentSummary.next_actions.length" class="list-disc list-inside space-y-1">
                  <li v-for="(item, idx) in commentSummary.next_actions" :key="`n-${idx}`">{{ item }}</li>
                </ul>
                <p v-else class="text-gray-400">暫無</p>
              </div>
              <p v-if="commentSummaryMeta?.truncated" class="text-xs text-violet-600">
                已自動截斷較舊留言，摘要以最近 {{ commentSummaryMeta.used_comments }} / {{ commentSummaryMeta.total_comments }} 筆為主。
              </p>
            </div>

            <div class="space-y-3 max-h-60 overflow-y-auto mb-4">
              <div v-for="comment in taskComments" :key="comment.comment_id" class="flex gap-3 p-3 bg-gray-50 rounded-xl group">
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
                <button @click="deleteComment(comment.comment_id)"
                  class="opacity-0 group-hover:opacity-100 w-7 h-7 flex items-center justify-center text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all shrink-0"
                  title="刪除留言">✕</button>
              </div>
              <div v-if="taskComments.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無留言</div>
            </div>
            <div class="flex gap-2">
              <input v-model="newComment" type="text" placeholder="新增留言..." @keyup.enter="addComment"
                class="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
              <button @click="addComment" :disabled="!newComment.trim()"
                class="px-4 py-2.5 bg-primary text-white font-medium rounded-xl hover:brightness-110 transition-all disabled:opacity-50">傳送</button>
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
          <div v-else-if="aiGeneratedTasks.length === 0" class="py-8">
            <p class="text-gray-500 mb-4 text-center">可輸入需求情境，讓 Copilot 透過 MCP 生成更貼近專案的任務建議</p>
            <div class="space-y-3 mb-5">
              <label class="block text-sm font-medium text-gray-700">需求描述（可選）</label>
              <textarea
                v-model="aiPrompt"
                rows="4"
                placeholder="例如：這個月要完成登入流程重構，請拆成後端 API、前端頁面、測試與上線準備"
                class="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"
              ></textarea>
              <div class="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                <label class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input v-model="useCopilotMcp" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                  優先使用 Copilot + MCP 工具路由
                </label>
                <label class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input v-model="autoCreateAfterGenerate" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                  生成後直接建立任務
                </label>
              </div>
            </div>
            <div class="text-center">
              <button @click="generateTasksWithAi" class="px-6 py-3 bg-linear-to-r from-purple-500 to-indigo-500 text-white font-semibold rounded-xl hover:brightness-110 transition-all shadow-lg shadow-purple-200">
                {{ useCopilotMcp ? '✨ Copilot 智慧生成' : '🤖 開始生成' }}
              </button>
            </div>
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

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { isAxiosError } from 'axios';
import { toast } from 'vue-sonner';
import { taskService } from '../../services/taskService';
import { timelineService } from '../../services/timelineService';
import { copilotService } from '../../services/copilotService';
import { formatDate, formatDateTime, formatFileSize, isImageFile, getFileIcon } from '../../utils/formatters';
import { downloadFileFromUrl, loadTaskDetailResourcesWithMembers } from '../../utils/taskDetails';
import { useConfirm } from '../../composables/useConfirm';
import { mapToCreateTaskPayload } from '../../utils/payloadMappers';
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
  ApiErrorPayload,
  GenerateTasksResponse,
  CopilotMcpExecuteResponse,
} from '../../types';

const { confirm } = useConfirm();

const props = defineProps<TimelineDetailDialogProps>();

const getApiErrorMessage = (error: unknown, fallback: string) => {
  if (isAxiosError<ApiErrorPayload>(error)) {
    return error.response?.data?.error || fallback;
  }
  return fallback;
};

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
const fileInput = ref<HTMLInputElement | null>(null);

const subtaskProgress = computed(() => {
  if (!taskSubtasks.value.length) return 0;
  return Math.round(taskSubtasks.value.filter(s => s.completed).length / taskSubtasks.value.length * 100);
});
const showAiGenerateModal = ref(false);
const aiGeneratedTasks = ref<AiGeneratedTask[]>([]);
const selectedAiTasks = ref<number[]>([]);
const isGeneratingAi = ref(false);
const aiPrompt = ref('');
const useCopilotMcp = ref(true);
const autoCreateAfterGenerate = ref(false);
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

// 每次開啟新的 selectedTimeline 時重置 remark 狀態
watch(() => props.selectedTimeline, (val) => {
  if (val) {
    isEditingRemark.value = false;
    timelineRemark.value = val.remark || '';
    localRemark.value = timelineRemark.value;
  } else {
    timelineRemark.value = '';
    localRemark.value = '';
  }
}, { immediate: true });

watch(showAiGenerateModal, (opened) => {
  if (!opened) return;
  selectedAiTasks.value = [];
  if (!aiPrompt.value.trim()) {
    aiPrompt.value = timelineRemark.value || '';
  }
});

const resetTaskForm = () => {
  taskForm.value = { name: '', start_date: '', end_date: '', priority: 2, tags: '', task_remark: '' };
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
    const data = mapToCreateTaskPayload({
      ...taskForm.value,
      timeline_id: props.selectedTimeline.id,
    });
    await taskService.create(data);
    showAddTaskModal.value = false;
    resetTaskForm();
    emit('refresh-all');
  } catch { toast.error('新增任務失敗'); }
};

const openTaskDetail = async (task: Task) => {
  selectedTask.value = { ...task };
  assignTask.value = { ...task };
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
  } finally {
    if (fileInput.value) fileInput.value.value = '';
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
  searchResult.value = null; searchError.value = '';
  try {
    const res = await timelineService.searchUser(inputEmail.value);
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
const normalizeGeneratedTasks = (payload: unknown): AiGeneratedTask[] => {
  if (Array.isArray(payload)) {
    return payload.filter((item): item is AiGeneratedTask => Boolean(item && typeof item === 'object'));
  }

  if (payload && typeof payload === 'object') {
    const candidate = (payload as Record<string, unknown>).tasks;
    if (Array.isArray(candidate)) {
      return candidate.filter((item): item is AiGeneratedTask => Boolean(item && typeof item === 'object'));
    }
  }

  return [];
};

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

  try {
    if (useCopilotMcp.value) {
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
        auto_create_generated_tasks: autoCreateAfterGenerate.value,
      });

      const payload: CopilotMcpExecuteResponse = res.data;
      aiGeneratedTasks.value = normalizeGeneratedTasks(payload.result);

      if (payload.auto_create_result) {
        const createdCount = Number(payload.auto_create_result.created || 0);
        if (createdCount > 0) {
          toast.success(payload.auto_create_result.message || 'Copilot 已自動建立任務');
          showAiGenerateModal.value = false;
          aiGeneratedTasks.value = [];
          selectedAiTasks.value = [];
          emit('refresh-all');
          return;
        }

        toast.info(payload.auto_create_result.message || '沒有可建立的新任務，請調整需求描述後再試。');
      }
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

    selectedAiTasks.value = aiGeneratedTasks.value.map((_, i) => i);
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, 'AI 生成失敗，請稍後再試'));
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
  const timelineId = props.selectedTimeline.id;
  const tasksToCreate: CreateTaskPayload[] = selectedAiTasks.value
    .map(i => aiGeneratedTasks.value[i])
    .filter((task): task is AiGeneratedTask => Boolean(task))
    .map(task => mapToCreateTaskPayload({
      name: task.name,
      start_date: task.start_date ?? null,
      end_date: task.end_date ?? null,
      priority: task.priority,
      tags: task.tags ?? null,
      task_remark: task.task_remark ?? task.remark ?? null,
      timeline_id: timelineId,
    }));
  try {
    await timelineService.batchCreateTasks(timelineId, tasksToCreate);
    showAiGenerateModal.value = false;
    aiGeneratedTasks.value = []; selectedAiTasks.value = [];
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

const getPriorityLabel = (priority: number) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中');

const getPriorityBadgeClass = (priority: number) => ({
  1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
  2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
  3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
}[priority] || 'bg-gray-100 text-gray-700 border border-gray-200');

const getAiPriorityClass = (priority: number) => ({
  1: 'bg-red-100 text-red-700', 2: 'bg-yellow-100 text-yellow-700', 3: 'bg-green-100 text-green-700'
}[priority] || 'bg-gray-100 text-gray-700');
</script>
