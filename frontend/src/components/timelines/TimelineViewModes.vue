<template>
  <div>
    <!-- Kanban View -->
    <div v-if="viewMode === 'kanban'" class="px-4 pb-8">
      <div class="mb-6 flex flex-wrap items-center gap-4">
        <div class="flex-1 min-w-50">
          <label class="block text-sm font-medium text-gray-600 mb-2">選擇專案</label>
          <select 
            v-model="selectedKanbanTimeline"
            class="w-full px-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm"
          >
            <option :value="null">📁 全部專案</option>
            <option v-for="t in timelines" :key="t.id" :value="t.id">📋 {{ t.name }}</option>
          </select>
        </div>
        <div class="flex-1 min-w-50">
          <label class="block text-sm font-medium text-gray-600 mb-2">搜尋任務</label>
          <div class="relative">
            <input 
              v-model="searchQuery"
              type="text"
              placeholder="輸入任務名稱..."
              class="w-full pl-10 pr-4 py-2.5 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none shadow-sm"
            />
            <span class="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">🔍</span>
          </div>
        </div>
        <div class="flex items-end gap-2">
          <button 
            @click="showFilterPanel = !showFilterPanel"
            :class="[
              'px-4 py-2.5 rounded-xl border transition-all flex items-center gap-2 shadow-sm',
              hasActiveFilters ? 'bg-linear-to-r from-primary to-blue-600 text-white border-transparent' : 'bg-white border-gray-200 text-gray-600 hover:bg-gray-50 hover:border-gray-300'
            ]"
          >
            <span>🎯</span> 篩選
            <span v-if="hasActiveFilters" class="w-5 h-5 bg-white text-primary text-xs font-bold rounded-full flex items-center justify-center shadow">{{ activeFilterCount }}</span>
          </button>
        </div>
      </div>

      <div v-if="showFilterPanel" class="mb-6 p-5 bg-linear-to-r from-white to-gray-50/50 rounded-2xl border border-gray-200 shadow-lg">
        <h4 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
          <span class="w-6 h-6 bg-primary/10 rounded-lg flex items-center justify-center text-xs">🎯</span>
          進階篩選
        </h4>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">優先級</label>
            <select v-model="filterPriority" class="w-full px-3 py-2.5 border border-gray-200 rounded-xl bg-white shadow-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
              <option :value="null">全部優先級</option>
              <option :value="1">🔴 高優先</option>
              <option :value="2">🟡 中優先</option>
              <option :value="3">🟢 低優先</option>
            </select>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">標籤</label>
            <input 
              v-model="filterTag"
              type="text"
              placeholder="輸入標籤關鍵字..."
              class="w-full px-3 py-2.5 border border-gray-200 rounded-xl bg-white shadow-sm focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
            />
          </div>
          <div class="flex items-end">
            <button @click="clearFilters" class="px-4 py-2.5 text-gray-500 hover:text-red-500 hover:bg-red-50 rounded-xl transition-all flex items-center gap-2">
              <span>🗑️</span> 清除篩選
            </button>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <!-- 待辦欄 -->
        <div class="bg-linear-to-b from-slate-100 to-slate-50 rounded-2xl p-4 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-gray-700 flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-slate-400 animate-pulse"></span>
              待辦
              <span class="text-sm font-normal bg-slate-200 text-slate-600 px-2 py-0.5 rounded-full">{{ pendingTasks.length }}</span>
            </h3>
          </div>
          <draggable
            v-model="pendingTasksList"
            group="kanban"
            item-key="task_id"
            :animation="200"
            ghost-class="kanban-ghost"
            drag-class="kanban-drag"
            @start="isDragging = true"
            @end="isDragging = false"
            @change="onPendingChange"
            class="space-y-3 min-h-50"
          >
            <template #item="{ element: task }">
              <div 
                @click="viewKanbanTaskDetail(task)"
                class="kanban-card bg-white rounded-xl p-4 shadow-sm border-l-4 border-slate-300 cursor-grab hover:shadow-lg hover:-translate-y-1 active:cursor-grabbing transition-all duration-200"
              >
                <div class="flex items-start justify-between mb-2">
                  <span class="font-medium text-gray-800 text-sm line-clamp-2">{{ task.name }}</span>
                  <span :class="getPriorityBadgeClass(task.priority)" class="text-xs px-2 py-0.5 rounded-full shrink-0 ml-2 font-medium">
                    {{ getPriorityLabel(task.priority) }}
                  </span>
                </div>
                <div v-if="task.tags" class="flex flex-wrap gap-1 mb-2">
                  <span v-for="tag in task.tags.split(',').slice(0, 3)" :key="tag" class="text-xs px-2 py-0.5 bg-linear-to-r from-blue-100 to-indigo-100 text-blue-700 rounded-full">{{ tag.trim() }}</span>
                  <span v-if="task.tags.split(',').length > 3" class="text-xs text-gray-400">+{{ task.tags.split(',').length - 3 }}</span>
                </div>
                <div v-if="task.subtasks && task.subtasks.length > 0" class="mb-2">
                  <div class="flex items-center gap-2 text-xs text-gray-500">
                    <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div class="h-full bg-linear-to-r from-primary to-blue-400 rounded-full transition-all duration-300" :style="{ width: getSubtaskProgress(task) + '%' }"></div>
                    </div>
                    <span class="font-medium">{{ getCompletedSubtaskCount(task) }}/{{ task.subtasks.length }}</span>
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                  <span class="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded-md">📅 {{ formatDate(task.end_date) }}</span>
                  <span v-if="getTaskTimelineName(task)" class="truncate max-w-20 text-primary font-medium">📁 {{ getTaskTimelineName(task) }}</span>
                </div>
              </div>
            </template>
          </draggable>
          <div v-if="pendingTasks.length === 0 && !isDragging" class="text-center py-12 text-gray-400">
            <span class="text-3xl mb-2 block">📋</span>
            <span class="text-sm">拖曳任務到這裡</span>
          </div>
        </div>

        <!-- 進行中欄 -->
        <div class="bg-linear-to-b from-blue-100 to-blue-50 rounded-2xl p-4 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-blue-700 flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-blue-500 animate-pulse"></span>
              進行中
              <span class="text-sm font-normal bg-blue-200 text-blue-700 px-2 py-0.5 rounded-full">{{ inProgressTasks.length }}</span>
            </h3>
          </div>
          <draggable
            v-model="inProgressTasksList"
            group="kanban"
            item-key="task_id"
            :animation="200"
            ghost-class="kanban-ghost"
            drag-class="kanban-drag"
            @start="isDragging = true"
            @end="isDragging = false"
            @change="onInProgressChange"
            class="space-y-3 min-h-50"
          >
            <template #item="{ element: task }">
              <div 
                @click="viewKanbanTaskDetail(task)"
                class="kanban-card bg-white rounded-xl p-4 shadow-sm border-l-4 border-blue-400 cursor-grab hover:shadow-lg hover:-translate-y-1 active:cursor-grabbing transition-all duration-200"
              >
                <div class="flex items-start justify-between mb-2">
                  <span class="font-medium text-gray-800 text-sm line-clamp-2">{{ task.name }}</span>
                  <span :class="getPriorityBadgeClass(task.priority)" class="text-xs px-2 py-0.5 rounded-full shrink-0 ml-2 font-medium">
                    {{ getPriorityLabel(task.priority) }}
                  </span>
                </div>
                <div v-if="task.tags" class="flex flex-wrap gap-1 mb-2">
                  <span v-for="tag in task.tags.split(',').slice(0, 3)" :key="tag" class="text-xs px-2 py-0.5 bg-linear-to-r from-blue-100 to-indigo-100 text-blue-700 rounded-full">{{ tag.trim() }}</span>
                  <span v-if="task.tags.split(',').length > 3" class="text-xs text-gray-400">+{{ task.tags.split(',').length - 3 }}</span>
                </div>
                <div v-if="task.subtasks && task.subtasks.length > 0" class="mb-2">
                  <div class="flex items-center gap-2 text-xs text-gray-500">
                    <div class="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div class="h-full bg-linear-to-r from-primary to-blue-400 rounded-full transition-all duration-300" :style="{ width: getSubtaskProgress(task) + '%' }"></div>
                    </div>
                    <span class="font-medium">{{ getCompletedSubtaskCount(task) }}/{{ task.subtasks.length }}</span>
                  </div>
                </div>
                <div class="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                  <span class="flex items-center gap-1 bg-blue-100 px-2 py-1 rounded-md text-blue-600">📅 {{ formatDate(task.end_date) }}</span>
                  <span v-if="getTaskTimelineName(task)" class="truncate max-w-20 text-primary font-medium">📁 {{ getTaskTimelineName(task) }}</span>
                </div>
              </div>
            </template>
          </draggable>
          <div v-if="inProgressTasks.length === 0 && !isDragging" class="text-center py-12 text-gray-400">
            <span class="text-3xl mb-2 block">🚀</span>
            <span class="text-sm">拖曳任務到這裡</span>
          </div>
        </div>

        <!-- 已完成欄 -->
        <div class="bg-linear-to-b from-green-100 to-green-50 rounded-2xl p-4 shadow-sm">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-bold text-green-700 flex items-center gap-2">
              <span class="w-3 h-3 rounded-full bg-green-500"></span>
              已完成
              <span class="text-sm font-normal bg-green-200 text-green-700 px-2 py-0.5 rounded-full">{{ completedTasks.length }}</span>
            </h3>
          </div>
          <draggable
            v-model="completedTasksList"
            group="kanban"
            item-key="task_id"
            :animation="200"
            ghost-class="kanban-ghost"
            drag-class="kanban-drag"
            @start="isDragging = true"
            @end="isDragging = false"
            @change="onCompletedChange"
            class="space-y-3 min-h-50"
          >
            <template #item="{ element: task }">
              <div 
                @click="viewKanbanTaskDetail(task)"
                class="kanban-card bg-white/80 rounded-xl p-4 shadow-sm border-l-4 border-green-400 cursor-grab hover:shadow-lg hover:-translate-y-1 active:cursor-grabbing transition-all duration-200"
              >
                <div class="flex items-start justify-between mb-2">
                  <span class="font-medium text-gray-500 text-sm line-through line-clamp-2">{{ task.name }}</span>
                  <span class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 shrink-0 ml-2 font-medium">✓ 完成</span>
                </div>
                <div class="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-100">
                  <span class="flex items-center gap-1 bg-green-100 px-2 py-1 rounded-md text-green-600">📅 {{ formatDate(task.end_date) }}</span>
                  <span v-if="getTaskTimelineName(task)" class="truncate max-w-20 text-green-600 font-medium">📁 {{ getTaskTimelineName(task) }}</span>
                </div>
              </div>
            </template>
          </draggable>
          <div v-if="completedTasks.length === 0 && !isDragging" class="text-center py-12 text-gray-400">
            <span class="text-3xl mb-2 block">🎉</span>
            <span class="text-sm">完成的任務會出現在這裡</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Calendar View -->
    <div v-if="viewMode === 'calendar'" class="px-4 pb-8">
      <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden">
        <div class="p-5 border-b border-gray-100 bg-linear-to-r from-primary/5 via-blue-50 to-indigo-50">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <h3 class="font-bold text-gray-800 flex items-center gap-2 text-lg">
              <span class="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center">📅</span>
              專案月曆
            </h3>
            <div class="flex flex-wrap items-center gap-4 text-sm bg-white/80 backdrop-blur-sm px-4 py-2.5 rounded-xl shadow-sm">
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-green-400 to-green-500 shadow-sm"></span> 已完成</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-red-400 to-red-500 shadow-sm"></span> 已過期</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-orange-400 to-orange-500 shadow-sm"></span> 緊急</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-yellow-400 to-yellow-500 shadow-sm"></span> 即將到期</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-linear-to-r from-blue-400 to-blue-500 shadow-sm"></span> 進行中</span>
            </div>
          </div>
        </div>
        <div class="p-6">
          <FullCalendar ref="calendarRef" :options="calendarOptions" class="fc-custom" />
        </div>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div class="bg-white rounded-2xl p-5 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <h4 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
            <span class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">📌</span>
            本週截止
          </h4>
          <div class="space-y-2 max-h-36 overflow-y-auto">
            <div v-for="timeline in thisWeekTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="flex items-center justify-between p-3 bg-linear-to-r from-orange-50 to-amber-50 rounded-xl cursor-pointer hover:from-orange-100 hover:to-amber-100 transition-all border border-orange-100">
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs bg-orange-500 text-white px-2 py-1 rounded-full font-medium">{{ getDaysRemaining(timeline.endDate).text }}</span>
            </div>
            <p v-if="thisWeekTimelines.length === 0" class="text-sm text-gray-400 text-center py-4">📋 無專案</p>
          </div>
        </div>
        <div class="bg-white rounded-2xl p-5 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <h4 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
            <span class="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center">🔥</span>
            已過期專案
          </h4>
          <div class="space-y-2 max-h-36 overflow-y-auto">
            <div v-for="timeline in overdueTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="flex items-center justify-between p-3 bg-linear-to-r from-red-50 to-rose-50 rounded-xl cursor-pointer hover:from-red-100 hover:to-rose-100 transition-all border border-red-100">
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs bg-red-500 text-white px-2 py-1 rounded-full font-medium">{{ getDaysRemaining(timeline.endDate).text }}</span>
            </div>
            <p v-if="overdueTimelines.length === 0" class="text-sm text-gray-400 text-center py-4">👍 無過期專案</p>
          </div>
        </div>
        <div class="bg-white rounded-2xl p-5 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <h4 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
            <span class="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center">✅</span>
            近期完成
          </h4>
          <div class="space-y-2 max-h-36 overflow-y-auto">
            <div v-for="timeline in completedTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="flex items-center justify-between p-3 bg-linear-to-r from-green-50 to-emerald-50 rounded-xl cursor-pointer hover:from-green-100 hover:to-emerald-100 transition-all border border-green-100">
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs bg-green-500 text-white px-2 py-1 rounded-full font-medium">100%</span>
            </div>
            <p v-if="completedTimelines.length === 0" class="text-sm text-gray-400 text-center py-4">🎯 尚無完成專案</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Timeline (List) View -->
    <div v-if="viewMode === 'timeline'" class="px-4 pb-8">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-4 border-b border-gray-100 bg-gray-50/50">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-gray-700">📋 專案列表</h3>
            <span class="text-sm text-gray-500">依結束日期排序</span>
          </div>
        </div>
        <div class="divide-y divide-gray-100">
          <div v-for="timeline in sortedTimelines" :key="timeline.id" @click="$emit('view-timeline', timeline)" class="p-4 hover:bg-blue-50/50 cursor-pointer transition-colors">
            <div class="flex items-start gap-4">
              <div class="shrink-0 w-20 text-center">
                <div :class="['w-12 h-12 mx-auto rounded-xl flex flex-col items-center justify-center', getTimelineStatus(timeline).bgClass]">
                  <span class="text-xs font-medium" :class="getTimelineStatus(timeline).textClass">
                    {{ timeline.endDate ? new Date(timeline.endDate).getMonth() + 1 + '月' : '--' }}
                  </span>
                  <span class="text-lg font-bold -mt-1" :class="getTimelineStatus(timeline).textClass">
                    {{ timeline.endDate ? new Date(timeline.endDate).getDate() : '--' }}
                  </span>
                </div>
                <p class="text-xs text-gray-400 mt-1">{{ getDaysRemaining(timeline.endDate).text }}</p>
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2 mb-2">
                  <h4 class="font-semibold text-gray-800 truncate">{{ timeline.name }}</h4>
                  <span :class="['shrink-0 px-2 py-0.5 text-xs font-medium rounded-full', getTimelineStatus(timeline).badgeClass]">
                    {{ getTimelineStatus(timeline).label }}
                  </span>
                </div>
                <div class="mb-2">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div :class="['h-full rounded-full transition-all duration-500', getProgressBarColor(timeline)]" :style="{ width: getTaskProgress(timeline) + '%' }"></div>
                    </div>
                    <span class="text-xs font-medium text-gray-500 w-10 text-right">{{ getTaskProgress(timeline) }}%</span>
                  </div>
                </div>
                <div class="flex items-center gap-4 text-xs text-gray-500">
                  <span class="flex items-center gap-1"><span>📅</span> {{ formatDate(timeline.startDate) }} - {{ formatDate(timeline.endDate) }}</span>
                  <span class="flex items-center gap-1"><span>✅</span> {{ timeline.completedTasks || 0 }}/{{ timeline.totalTasks || 0 }}</span>
                </div>
              </div>
              <div class="shrink-0 flex items-center gap-1" @click.stop>
                <button v-if="timeline.role === 0" @click="$emit('edit-timeline', timeline)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors">✏️</button>
                <button v-if="timeline.role === 0" @click="$emit('delete-timeline', timeline.id)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">🗑️</button>
              </div>
            </div>
          </div>
        </div>
        <div v-if="timelines.length === 0" class="text-center py-16">
          <span class="text-5xl block mb-4">📅</span>
          <p class="text-lg text-gray-600">目前尚無專案</p>
          <p class="text-sm text-gray-400 mt-1">點擊「新增專案」來建立您的第一個專案</p>
        </div>
      </div>
    </div>

    <!-- Gantt View -->
    <div v-if="viewMode === 'gantt'" class="px-4 pb-8">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <div class="p-4 border-b border-gray-100 bg-linear-to-r from-sky-50 via-white to-cyan-50">
          <div class="flex flex-wrap items-end justify-between gap-3">
            <div>
              <h3 class="font-semibold text-gray-800 flex items-center gap-2">
                <span class="w-8 h-8 bg-white rounded-lg shadow-sm flex items-center justify-center">📈</span>
                任務甘特圖（frappe-gantt）
              </h3>
              <p class="text-xs text-gray-500 mt-1">支援拖曳調整日期；依賴關係為同專案任務自動串接（基礎版）。</p>
            </div>
            <div class="flex flex-wrap items-center gap-3 text-xs text-gray-600">
              <div>
                <label class="mr-2 text-gray-500">專案篩選</label>
                <select v-model="selectedGanttTimeline" class="px-3 py-1.5 border border-gray-200 rounded-lg bg-white">
                  <option value="all">全部專案</option>
                  <option v-for="timeline in props.timelines" :key="timeline.id" :value="String(timeline.id)">{{ timeline.name }}</option>
                </select>
              </div>
              <div>
                <label class="mr-2 text-gray-500">時間範圍</label>
                <select v-model="selectedGanttRange" class="px-3 py-1.5 border border-gray-200 rounded-lg bg-white">
                  <option value="all">全部</option>
                  <option value="90d">近 90 天</option>
                  <option value="30d">近 30 天</option>
                </select>
              </div>
              <div>
                <label class="mr-2 text-gray-500">縮放</label>
                <select v-model="selectedGanttViewMode" class="px-3 py-1.5 border border-gray-200 rounded-lg bg-white">
                  <option value="Day">日</option>
                  <option value="Week">週</option>
                  <option value="Month">月</option>
                </select>
              </div>
              <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded-full">任務 {{ ganttRenderableTasks.length }}</span>
              <span class="px-2 py-1 bg-amber-100 text-amber-700 rounded-full">缺日期 {{ missingGanttTaskDates }}</span>
            </div>
          </div>
        </div>

        <div v-if="ganttRenderableTasks.length === 0" class="text-center py-16">
          <span class="text-5xl block mb-3">🗓️</span>
          <p class="text-lg text-gray-700">目前沒有可繪製的任務</p>
          <p class="text-sm text-gray-400 mt-1">任務需同時有開始與結束日期才能顯示在甘特圖上。</p>
        </div>

        <div v-else class="p-4">
          <div ref="ganttContainerRef" class="frappe-gantt-container w-full overflow-x-auto"></div>
          <div class="mt-3 flex flex-wrap items-center gap-2 text-xs text-gray-500">
            <span class="px-2 py-1 bg-gray-100 rounded-full">提示：拖曳條形可調整任務時程</span>
            <span class="px-2 py-1 bg-gray-100 rounded-full">點擊任務可開啟所屬專案面板</span>
            <span class="px-2 py-1 bg-gray-100 rounded-full">滑鼠移入可檢視任務資訊</span>
            <span class="px-2 py-1 bg-sky-50 text-sky-700 rounded-full">主責人會用固定顏色區分</span>
            <span class="px-2 py-1 bg-amber-50 text-amber-700 rounded-full">有協作者的任務會顯示虛線外框</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Card View -->
    <div v-if="viewMode === 'card'" class="px-4 pb-24">
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        <div 
          v-for="timeline in sortedTimelines" :key="timeline.id"
          @click="$emit('view-timeline', timeline)"
          :class="['group bg-white rounded-2xl shadow-sm border hover:-translate-y-1 hover:shadow-lg transition-all cursor-pointer overflow-hidden', getTimelineStatus(timeline).borderClass]"
        >
          <div :class="['h-1.5', getTimelineStatus(timeline).barClass]"></div>
          <div class="p-5">
            <div class="flex justify-between items-start mb-4">
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-gray-800 truncate mb-1">{{ timeline.name }}</h3>
                <span :class="['inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full', getTimelineStatus(timeline).badgeClass]">
                  {{ getTimelineStatus(timeline).icon }} {{ getTimelineStatus(timeline).label }}
                </span>
              </div>
              <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
                <button v-if="timeline.role === 0" @click="$emit('edit-timeline', timeline)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors">✏️</button>
                <button v-if="timeline.role === 0" @click="$emit('delete-timeline', timeline.id)" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors">🗑️</button>
              </div>
            </div>
            <div class="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-xl">
              <div class="flex items-center gap-2">
                <span class="text-2xl">{{ getTimelineStatus(timeline).icon }}</span>
                <div>
                  <p class="text-xs text-gray-500">剩餘時間</p>
                  <p :class="['text-lg font-bold', getDaysRemaining(timeline.endDate).colorClass]">{{ getDaysRemaining(timeline.endDate).display }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-500">截止日期</p>
                <p class="text-sm font-medium text-gray-700">{{ formatDate(timeline.endDate) || '未設定' }}</p>
              </div>
            </div>
            <div class="mb-4" v-if="timeline.startDate && timeline.endDate">
              <div class="flex justify-between text-xs text-gray-400 mb-1">
                <span>{{ formatDate(timeline.startDate) }}</span>
                <span>{{ formatDate(timeline.endDate) }}</span>
              </div>
              <div class="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                <div class="absolute left-0 top-0 h-full bg-linear-to-r from-blue-400 to-blue-500 rounded-full transition-all duration-500" :style="{ width: getTimeProgress(timeline) + '%' }"></div>
                <div v-if="getTimeProgress(timeline) > 0 && getTimeProgress(timeline) < 100" class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-full shadow-sm" :style="{ left: getTimeProgress(timeline) + '%', transform: 'translate(-50%, -50%)' }"></div>
              </div>
              <p class="text-xs text-gray-400 text-center mt-1">時程進度 {{ getTimeProgress(timeline) }}%</p>
            </div>
            <div class="mb-4">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-500">任務完成度</span>
                <span class="font-semibold" :class="getProgressTextColor(timeline)">{{ timeline.completedTasks || 0 }} / {{ timeline.totalTasks || 0 }}</span>
              </div>
              <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div :class="['h-full rounded-full transition-all duration-500', getProgressBarColor(timeline)]" :style="{ width: getTaskProgress(timeline) + '%' }"></div>
              </div>
            </div>
            <div class="flex items-center justify-between pt-3 border-t border-gray-100">
              <div class="flex items-center gap-2 text-xs text-gray-400"><span>📅 {{ formatDate(timeline.startDate) || '未設定' }}</span></div>
              <span class="text-xs text-primary font-medium group-hover:underline">查看詳情 →</span>
            </div>
          </div>
        </div>
      </div>
      <div v-if="timelines.length === 0" class="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
        <span class="text-6xl block mb-4">📁</span>
        <p class="text-xl text-gray-600 mb-2">目前尚無專案</p>
        <p class="text-sm text-gray-400 mb-6">建立您的第一個專案來開始追蹤進度</p>
        <button @click="$emit('create-timeline')" class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:shadow-xl transition-all">
          <span>➕</span> 新增專案
        </button>
      </div>
    </div>

    <!-- 看板任務詳情 Modal -->
    <div v-if="showKanbanTaskModal && selectedKanbanTask" class="fixed inset-0 bg-black/50 flex items-center justify-center z-60 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto animate-slideUp">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent sticky top-0 bg-white z-10">
          <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📌</span>
            {{ selectedKanbanTask.name }}
          </h2>
          <button @click="showKanbanTaskModal = false" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        <div class="p-6 space-y-6">
          <div class="flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">狀態：</span>
              <span :class="['px-3 py-1 text-sm font-medium rounded-full', selectedKanbanTask.status === 'completed' ? 'bg-green-100 text-green-700' : selectedKanbanTask.status === 'in_progress' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700']">
                {{ selectedKanbanTask.status === 'completed' ? '✅ 已完成' : selectedKanbanTask.status === 'in_progress' ? '🔄 進行中' : '📋 待辦' }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">優先級：</span>
              <select :value="selectedKanbanTask.priority" @change="onPrioritySelect" class="px-3 py-1 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                <option :value="1">🔴 高優先</option>
                <option :value="2">🟡 中優先</option>
                <option :value="3">🟢 低優先</option>
              </select>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-xl">
            <div>
              <p class="text-xs text-gray-500 mb-1">開始日期</p>
              <p class="font-medium text-gray-800">{{ formatDate(selectedKanbanTask.start_date) || '未設定' }}</p>
            </div>
            <div>
              <p class="text-xs text-gray-500 mb-1">截止日期</p>
              <p class="font-medium text-gray-800">{{ formatDate(selectedKanbanTask.end_date) || '未設定' }}</p>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2"><span>🏷️</span> 標籤（逗號分隔）</label>
            <div class="flex gap-2">
              <input v-model="selectedKanbanTask.tags" type="text" placeholder="例如：前端, 重要, Bug" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
              <button @click="updateTaskTags" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">儲存</button>
            </div>
            <div v-if="selectedKanbanTask.tags" class="flex flex-wrap gap-2 mt-2">
              <span v-for="tag in selectedKanbanTask.tags.split(',')" :key="tag" class="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full">{{ tag.trim() }}</span>
            </div>
          </div>
          <div>
            <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span>📋</span> 子任務
              <span class="text-sm font-normal text-gray-500">({{ getCompletedSubtaskCount(selectedKanbanTask) }}/{{ selectedKanbanTask.subtasks?.length || 0 }})</span>
            </h4>
            <div v-if="selectedKanbanTask.subtasks && selectedKanbanTask.subtasks.length > 0" class="mb-4">
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div class="h-full bg-primary rounded-full transition-all duration-300" :style="{ width: getSubtaskProgress(selectedKanbanTask) + '%' }"></div>
              </div>
            </div>
            <div class="space-y-2 mb-4">
              <div v-for="subtask in selectedKanbanTask.subtasks" :key="subtask.id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group hover:bg-gray-100 transition-colors">
                <input type="checkbox" :checked="subtask.completed" @change="toggleSubtask(subtask)" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" />
                <span :class="['flex-1 text-sm', subtask.completed ? 'line-through text-gray-400' : 'text-gray-700']">{{ subtask.name }}</span>
                <button @click="deleteSubtask(subtask)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all">🗑️</button>
              </div>
              <div v-if="!selectedKanbanTask.subtasks || selectedKanbanTask.subtasks.length === 0" class="text-center py-4 text-gray-400 text-sm">尚無子任務</div>
            </div>
            <div class="flex gap-2">
              <input v-model="newSubtaskName" type="text" placeholder="輸入子任務名稱..." @keyup.enter="addSubtask" class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
              <button @click="addSubtask" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">新增</button>
            </div>
          </div>
          <div v-if="selectedKanbanTask.task_remark" class="p-4 bg-yellow-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-2 flex items-center gap-2"><span>📝</span> 備註</h4>
            <p class="text-gray-600 text-sm">{{ selectedKanbanTask.task_remark }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue';
import { toast } from 'vue-sonner';
import { formatDate } from '../../utils/formatters';
import draggable from 'vuedraggable';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import multiMonthPlugin from '@fullcalendar/multimonth';
import Gantt from 'frappe-gantt';
import '../../styles/frappe-gantt.css';
import type { CalendarOptions, EventClickArg, EventMountArg, DayCellMountArg } from '@fullcalendar/core';
import { taskService } from '../../services/taskService';
import type { Task, Timeline, Subtask, TaskUpdatePayload, TimelineViewModesProps, DaysRemainingResult } from '../../types';

const props = defineProps<TimelineViewModesProps>();

interface DraggableChangeEvent {
  added?: {
    element: Task;
  };
}

const emit = defineEmits<{
  (e: 'view-timeline', timeline: Timeline): void;
  (e: 'edit-timeline', timeline: Timeline): void;
  (e: 'delete-timeline', timelineId: number): void;
  (e: 'create-timeline'): void;
  (e: 'refresh-all'): void;
}>();

// 看板本地狀態
const selectedKanbanTimeline = ref<number | null>(null);
const searchQuery = ref('');
const showFilterPanel = ref(false);
const filterPriority = ref<number | null>(null);
const filterTag = ref('');
const isDragging = ref(false);
const showKanbanTaskModal = ref(false);
const selectedKanbanTask = ref<Task | null>(null);
const newSubtaskName = ref('');

type TaskStatus = Task['status'];

// 月曆 ref
const calendarRef = ref<InstanceType<typeof FullCalendar> | null>(null);

// ────────────── 篩選 computed ──────────────
const filteredTasks = computed(() => {
  let tasks = props.allTasks;
  if (selectedKanbanTimeline.value) tasks = tasks.filter(t => t.timeline_id === selectedKanbanTimeline.value);
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase();
    tasks = tasks.filter(t => t.name.toLowerCase().includes(q));
  }
  if (filterPriority.value) tasks = tasks.filter(t => t.priority === filterPriority.value);
  if (filterTag.value) {
    const tag = filterTag.value.toLowerCase();
    tasks = tasks.filter(t => t.tags && t.tags.toLowerCase().includes(tag));
  }
  return tasks;
});

const pendingTasks = computed(() => filteredTasks.value.filter(t => t.status === 'pending' && !t.completed));
const inProgressTasks = computed(() => filteredTasks.value.filter(t => t.status === 'in_progress' && !t.completed));
const completedTasks = computed(() => filteredTasks.value.filter(t => t.status === 'completed' || t.completed));

const pendingTasksList = computed({ get: () => pendingTasks.value, set: () => {} });
const inProgressTasksList = computed({ get: () => inProgressTasks.value, set: () => {} });
const completedTasksList = computed({ get: () => completedTasks.value, set: () => {} });

const hasActiveFilters = computed(() => filterPriority.value || filterTag.value);
const activeFilterCount = computed(() => (filterPriority.value ? 1 : 0) + (filterTag.value ? 1 : 0));

const clearFilters = () => { filterPriority.value = null; filterTag.value = ''; };

// ────────────── 甘特圖相關 ──────────────
const ganttContainerRef = ref<HTMLElement | null>(null);
const selectedGanttTimeline = ref<string>('all');
const selectedGanttRange = ref<'all' | '90d' | '30d'>('90d');
const selectedGanttViewMode = ref<'Day' | 'Week' | 'Month'>('Week');

type GanttRenderableTask = {
  task_id: number;
  name: string;
  timeline_id: number | null;
  start_date: string;
  end_date: string;
  progress: number;
};

type FrappeTask = {
  id: string;
  name: string;
  full_name: string;
  start: string;
  end: string;
  progress: number;
  dependencies: string;
  custom_class?: string;
};

let ganttInstance: Gantt | null = null;
const ganttSavingTaskIds = new Set<number>();
const ganttSaveTimers = new Map<number, ReturnType<typeof setTimeout>>();
const ganttClickLockedUntil = new Map<number, number>();
const SUPPRESS_CLICK_AFTER_DRAG_MS = 800;

const parseDateToDay = (raw: string | null | undefined): Date | null => {
  if (!raw) return null;
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return null;
  d.setHours(0, 0, 0, 0);
  return d;
};

const dayToIso = (date: Date): string => {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d.toISOString().split('T')[0];
};

const getDurationDays = (startDate: string, endDate: string): number => {
  const start = parseDateToDay(startDate);
  const end = parseDateToDay(endDate);
  if (!start || !end) return 1;
  return Math.max(1, Math.round((end.getTime() - start.getTime()) / (24 * 60 * 60 * 1000)) + 1);
};

const truncateWithEllipsis = (text: string, maxChars: number): string => {
  if (text.length <= maxChars) return text;
  if (maxChars <= 3) return `${text.slice(0, 1)}...`;
  return `${text.slice(0, maxChars - 3)}...`;
};

const getGanttLabelByView = (name: string, durationDays: number): string => {
  let maxChars = 12;
  if (selectedGanttViewMode.value === 'Day') {
    maxChars = Math.min(34, Math.max(7, Math.floor(durationDays * 1.4)));
  } else if (selectedGanttViewMode.value === 'Week') {
    maxChars = Math.min(18, Math.max(5, Math.floor(durationDays * 0.45)));
  } else {
    maxChars = Math.min(14, Math.max(4, Math.floor(durationDays * 0.25)));
  }

  return truncateWithEllipsis(name, maxChars);
};

const addDaysToDate = (date: Date, days: number): Date => {
  const d = new Date(date);
  d.setDate(d.getDate() + days);
  return d;
};

const ganttFilteredTasks = computed(() => {
  let tasks = props.allTasks;

  if (selectedGanttTimeline.value !== 'all') {
    const timelineId = Number(selectedGanttTimeline.value);
    tasks = tasks.filter(task => task.timeline_id === timelineId);
  }

  if (selectedGanttRange.value !== 'all') {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const rangeDays = selectedGanttRange.value === '30d' ? 30 : 90;
    const rangeStart = addDaysToDate(today, -rangeDays);
    const rangeEnd = addDaysToDate(today, rangeDays);

    tasks = tasks.filter(task => {
      const start = parseDateToDay(task.start_date);
      const end = parseDateToDay(task.end_date);
      if (!start || !end) return false;
      return end >= rangeStart && start <= rangeEnd;
    });
  }

  return tasks;
});

const ganttRenderableTasks = computed<GanttRenderableTask[]>(() => {
  return ganttFilteredTasks.value
    .map(task => {
      const start = parseDateToDay(task.start_date);
      const end = parseDateToDay(task.end_date);
      if (!start || !end) return null;

      const safeEnd = end < start ? start : end;

      return {
        task_id: task.task_id,
        name: task.name,
        timeline_id: task.timeline_id,
        start_date: dayToIso(start),
        end_date: dayToIso(safeEnd),
        progress: task.completed ? 100 : task.status === 'in_progress' ? 50 : 0
      };
    })
    .filter((task): task is GanttRenderableTask => task !== null)
    .sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());
});

const missingGanttTaskDates = computed(() => ganttFilteredTasks.value.length - ganttRenderableTasks.value.length);

const getTimelineNameById = (timelineId: number | null): string => {
  if (!timelineId) return '';
  const timeline = props.timelines.find(t => t.id === timelineId);
  return timeline?.name ?? '';
};

const getTaskStatusLabel = (status: Task['status']): string => {
  if (status === 'completed') return '已完成';
  if (status === 'in_progress') return '進行中';
  if (status === 'review') return '審核中';
  if (status === 'cancelled') return '已取消';
  return '待辦';
};

const buildDependencies = (tasks: GanttRenderableTask[]): Map<number, string> => {
  const grouped = new Map<number, GanttRenderableTask[]>();

  tasks.forEach(task => {
    if (!task.timeline_id) return;
    const group = grouped.get(task.timeline_id) ?? [];
    group.push(task);
    grouped.set(task.timeline_id, group);
  });

  const dependencyMap = new Map<number, string>();
  grouped.forEach(group => {
    group.sort((a, b) => new Date(a.start_date).getTime() - new Date(b.start_date).getTime());
    group.forEach((task, index) => {
      if (index > 0) dependencyMap.set(task.task_id, String(group[index - 1].task_id));
    });
  });

  return dependencyMap;
};

const GANTT_OWNER_COLOR_CLASS_COUNT = 8;

const getGanttOwnerColorClass = (ownerUserId: number | null): string => {
  if (ownerUserId === null) return 'gantt-owner-unknown';
  return `gantt-owner-${Math.abs(ownerUserId) % GANTT_OWNER_COLOR_CLASS_COUNT}`;
};

const getGanttTaskClass = (task: GanttRenderableTask): string => {
  const source = props.allTasks.find(t => t.task_id === task.task_id);
  const members = source?.members ?? [];
  const owner = members.find(m => m.role === 0);
  const hasCollaborator = members.some(m => m.role === 1);

  const ownerClass = getGanttOwnerColorClass(owner?.user_id ?? null);
  return hasCollaborator ? `${ownerClass}-collab` : ownerClass;
};

const frappeTasks = computed<FrappeTask[]>(() => {
  const dependencyMap = buildDependencies(ganttRenderableTasks.value);
  return ganttRenderableTasks.value.map(task => ({
    id: String(task.task_id),
    name: task.name,
    full_name: task.name,
    start: task.start_date,
    end: task.end_date,
    progress: task.progress,
    dependencies: dependencyMap.get(task.task_id) ?? '',
    custom_class: getGanttTaskClass(task)
  }));
});

const renderGantt = async () => {
  if (props.viewMode !== 'gantt') return;
  if (ganttSavingTaskIds.size > 0) return;
  await nextTick();

  if (!ganttContainerRef.value) return;
  if (!frappeTasks.value.length) {
    ganttContainerRef.value.innerHTML = '';
    return;
  }

  ganttContainerRef.value.innerHTML = '';

  ganttInstance = new Gantt(ganttContainerRef.value, frappeTasks.value, {
    view_mode: selectedGanttViewMode.value,
    language: 'zh',
    today_button: true,
    popup_on: 'hover',
    custom_popup_html: (task) => {
      const hit = props.allTasks.find(t => String(t.task_id) === String(task.id));
      const timelineName = getTimelineNameById(hit?.timeline_id ?? null) || '未分配專案';
      const statusLabel = hit ? getTaskStatusLabel(hit.status) : '待辦';
      const progress = `${Math.round(task.progress ?? 0)}%`;
      const fullName = (task as FrappeTask).full_name || hit?.name || task.name;
      return `
        <div class="details-container">
          <h5>${fullName}</h5>
          <p>專案：${timelineName}</p>
          <p>狀態：${statusLabel}</p>
          <p>日期：${task.start} ~ ${task.end}</p>
          <p>進度：${progress}</p>
        </div>
      `;
    },
    on_click: (task) => {
      const taskId = Number(task.id);
      const lockedUntil = ganttClickLockedUntil.get(taskId) ?? 0;
      if (Date.now() < lockedUntil) return;

      const hit = props.allTasks.find(t => String(t.task_id) === String(task.id));
      if (!hit) return;
      const timeline = props.timelines.find(t => t.id === hit.timeline_id);
      if (timeline) emit('view-timeline', timeline);
    },
    on_date_change: async (task, start, end) => {
      const taskId = Number(task.id);
      const startDate = dayToIso(start);
      const endDate = dayToIso(end);

      // Drag release often triggers a synthetic click on the same bar; temporarily ignore it.
      ganttClickLockedUntil.set(taskId, Date.now() + SUPPRESS_CLICK_AFTER_DRAG_MS);

      const prevTimer = ganttSaveTimers.get(taskId);
      if (prevTimer) clearTimeout(prevTimer);

      const timer = setTimeout(async () => {
        ganttSavingTaskIds.add(taskId);
        try {
          await taskService.update(taskId, { start_date: startDate, end_date: endDate });

          const local = props.allTasks.find(t => t.task_id === taskId);
          if (local) {
            local.start_date = startDate;
            local.end_date = endDate;
          }

          emit('refresh-all');
          toast.success('任務時程已更新');
        } catch {
          toast.error('更新任務時程失敗，已重新整理');
          emit('refresh-all');
        } finally {
          ganttSavingTaskIds.delete(taskId);
          ganttSaveTimers.delete(taskId);
          void renderGantt();
        }
      }, 650);

      ganttSaveTimers.set(taskId, timer);
    }
  });
};

watch(
  [() => props.viewMode, frappeTasks, selectedGanttTimeline, selectedGanttRange, selectedGanttViewMode],
  () => {
    void renderGantt();
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  ganttSaveTimers.forEach(timer => clearTimeout(timer));
  ganttSaveTimers.clear();
  ganttSavingTaskIds.clear();
  ganttClickLockedUntil.clear();
  if (ganttContainerRef.value) ganttContainerRef.value.innerHTML = '';
  ganttInstance = null;
});

// ────────────── 月曆相關 ──────────────
const thisWeekTimelines = computed(() => props.timelines.filter((t: Timeline) => {
  const days = getDaysRemaining(t.endDate).days;
  return days !== null && days >= 0 && days <= 7;
}));
const overdueTimelines = computed(() => props.timelines.filter((t: Timeline) => {
  const days = getDaysRemaining(t.endDate).days;
  return days !== null && days < 0;
}));
const completedTimelines = computed(() => props.timelines.filter((t: Timeline) => getTaskProgress(t) === 100));

const normalizeDateOnly = (raw: string | null | undefined): string | null => {
  if (!raw) return null;
  return raw.length >= 10 ? raw.slice(0, 10) : raw;
};

const parseDateOnlyLocal = (raw: string | null | undefined): Date | null => {
  const normalized = normalizeDateOnly(raw);
  if (!normalized) return null;
  const [y, m, d] = normalized.split('-').map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
};

const toDateOnlyString = (date: Date): string => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

const calendarEvents = computed(() => props.timelines.map((timeline: Timeline) => {
  const status = getTimelineStatus(timeline);
  const progress = getTaskProgress(timeline);
  let backgroundColor, borderColor, textColor;
  if (progress === 100) { backgroundColor = '#22c55e'; borderColor = '#15803d'; textColor = '#ffffff'; }
  else if (status.label === '已過期') { backgroundColor = '#ef4444'; borderColor = '#b91c1c'; textColor = '#ffffff'; }
  else if (status.label === '緊急') { backgroundColor = '#f97316'; borderColor = '#c2410c'; textColor = '#ffffff'; }
  else if (status.label === '即將到期') { backgroundColor = '#fbbf24'; borderColor = '#d97706'; textColor = '#78350f'; }
  else { backgroundColor = '#3b82f6'; borderColor = '#1d4ed8'; textColor = '#ffffff'; }
  return {
    id: String(timeline.id),
    title: `${status.icon} ${timeline.name} (${progress}%)`,
    start: normalizeDateOnly(timeline.startDate) || normalizeDateOnly(timeline.endDate) || undefined,
    end: timeline.endDate ? addDays(timeline.endDate, 1) ?? undefined : undefined,
    backgroundColor, borderColor, textColor,
    extendedProps: { timeline, status: status.label, progress }
  };
}));

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, interactionPlugin, multiMonthPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-tw',
  headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,multiMonthYear' },
  buttonText: { today: '今天', month: '月', year: '年度' },
  height: 'auto',
  events: calendarEvents.value,
  eventClick: (info: EventClickArg) => emit('view-timeline', info.event.extendedProps.timeline as Timeline),
  eventDidMount: (info: EventMountArg) => {
    const el = info.el;
    el.title = `${info.event.title}\n狀態：${info.event.extendedProps.status}\n進度：${info.event.extendedProps.progress}% 完成`;
    el.style.borderRadius = '8px'; el.style.padding = '4px 8px'; el.style.margin = '2px 4px';
    el.style.fontSize = '12px'; el.style.fontWeight = '500'; el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    el.style.border = 'none'; el.style.borderLeft = `4px solid ${info.event.borderColor}`; el.style.transition = 'all 0.2s ease';
    el.addEventListener('mouseenter', () => { el.style.transform = 'translateY(-2px)'; el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'; });
    el.addEventListener('mouseleave', () => { el.style.transform = 'translateY(0)'; el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'; });
  },
  dayCellDidMount: (info: DayCellMountArg) => {
    const today = new Date();
    if (info.date.toDateString() === today.toDateString()) { info.el.style.backgroundColor = 'rgba(59, 130, 246, 0.08)'; info.el.style.borderRadius = '8px'; }
    const day = info.date.getDay();
    if (day === 0 || day === 6) info.el.style.backgroundColor = 'rgba(100, 116, 139, 0.03)';
  },
  eventDisplay: 'block', displayEventTime: false,
  eventClassNames: 'cursor-pointer fc-event-custom',
  dayMaxEvents: 3, moreLinkClick: 'popover'
}));

const addDays = (dateStr: string | null, days: number) => {
  const date = parseDateOnlyLocal(dateStr);
  if (!date) return null;
  date.setDate(date.getDate() + days);
  return toDateOnlyString(date);
};

const getDaysRemaining = (endDate: string | null | undefined): DaysRemainingResult => {
  if (!endDate) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-gray-400' };
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const end = parseDateOnlyLocal(endDate);
  if (!end) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-gray-400' };
  end.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { days: diffDays, text: `已過期 ${Math.abs(diffDays)} 天`, display: `過期 ${Math.abs(diffDays)} 天`, colorClass: 'text-red-500' };
  if (diffDays === 0) return { days: 0, text: '今天到期', display: '今天到期', colorClass: 'text-red-500' };
  if (diffDays === 1) return { days: 1, text: '明天到期', display: '剩 1 天', colorClass: 'text-orange-500' };
  if (diffDays <= 3) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-orange-500' };
  if (diffDays <= 7) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-yellow-600' };
  if (diffDays <= 30) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-blue-500' };
  return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-green-500' };
};

const getTaskProgress = (timeline: Timeline): number => {
  if (!timeline.totalTasks || timeline.totalTasks === 0) return 0;
  return Math.round((timeline.completedTasks || 0) / timeline.totalTasks * 100);
};

const getTimeProgress = (timeline: Timeline): number => {
  if (!timeline.startDate || !timeline.endDate) return 0;
  const start = parseDateOnlyLocal(timeline.startDate);
  const end = parseDateOnlyLocal(timeline.endDate);
  if (!start || !end) return 0;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  if (today < start) return 0;
  if (today > end) return 100;

  const totalDuration = end.getTime() - start.getTime();
  if (totalDuration <= 0) {
    return today.getTime() >= end.getTime() ? 100 : 0;
  }

  const elapsed = today.getTime() - start.getTime();
  const progress = Math.round((elapsed / totalDuration) * 100);
  return Math.min(100, Math.max(0, progress));
};

const getTimelineStatus = (timeline: Timeline) => {
  const { days } = getDaysRemaining(timeline.endDate);
  const progress = getTaskProgress(timeline);
  if (progress === 100) return { label: '已完成', icon: '✅', bgClass: 'bg-green-100', textClass: 'text-green-600', badgeClass: 'bg-green-100 text-green-700', borderClass: 'border-green-200', barClass: 'bg-gradient-to-r from-green-400 to-green-500' };
  if (days === null) return { label: '進行中', icon: '📋', bgClass: 'bg-gray-100', textClass: 'text-gray-600', badgeClass: 'bg-gray-100 text-gray-600', borderClass: 'border-gray-200', barClass: 'bg-gradient-to-r from-gray-300 to-gray-400' };
  if (days < 0) return { label: '已過期', icon: '⚠️', bgClass: 'bg-red-100', textClass: 'text-red-600', badgeClass: 'bg-red-100 text-red-700', borderClass: 'border-red-200', barClass: 'bg-gradient-to-r from-red-400 to-red-500' };
  if (days <= 3) return { label: '緊急', icon: '🔥', bgClass: 'bg-orange-100', textClass: 'text-orange-600', badgeClass: 'bg-orange-100 text-orange-700', borderClass: 'border-orange-200', barClass: 'bg-gradient-to-r from-orange-400 to-orange-500' };
  if (days <= 7) return { label: '即將到期', icon: '⏰', bgClass: 'bg-yellow-100', textClass: 'text-yellow-600', badgeClass: 'bg-yellow-100 text-yellow-700', borderClass: 'border-yellow-200', barClass: 'bg-gradient-to-r from-yellow-400 to-yellow-500' };
  return { label: '進行中', icon: '📋', bgClass: 'bg-blue-100', textClass: 'text-blue-600', badgeClass: 'bg-blue-100 text-blue-700', borderClass: 'border-blue-200', barClass: 'bg-gradient-to-r from-blue-400 to-blue-500' };
};

const getProgressBarColor = (timeline: Timeline) => {
  const progress = getTaskProgress(timeline), status = getTimelineStatus(timeline);
  if (progress === 100) return 'bg-gradient-to-r from-green-400 to-green-500';
  if (status.label === '已過期') return 'bg-gradient-to-r from-red-400 to-red-500';
  if (status.label === '緊急') return 'bg-gradient-to-r from-orange-400 to-orange-500';
  return 'bg-gradient-to-r from-primary to-primary-light';
};

const getProgressTextColor = (timeline: Timeline) => {
  const progress = getTaskProgress(timeline);
  if (progress === 100) return 'text-green-600';
  if (progress >= 50) return 'text-blue-600';
  return 'text-gray-600';
};

const getPriorityLabel = (priority: number) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中');

const getPriorityBadgeClass = (priority: number) => ({
  1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
  2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
  3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
}[priority] || 'bg-gray-100 text-gray-700 border border-gray-200');

const getSubtaskProgress = (task: Task): number => {
  if (!task.subtasks || task.subtasks.length === 0) return 0;
  return Math.round((task.subtasks.filter((s: Subtask) => s.completed).length / task.subtasks.length) * 100);
};

const getCompletedSubtaskCount = (task: Task): number => {
  if (!task?.subtasks?.length) return 0;
  return task.subtasks.filter((s: Subtask) => s.completed).length;
};

const getTaskTimelineName = (task: Task): string => {
  if (!task.timeline_id) return '';
  const tl = props.timelines.find((t: Timeline) => t.id === task.timeline_id);
  return tl ? tl.name : '';
};

// ────────────── 看板操作 ──────────────
const onTaskMoved = async (evt: DraggableChangeEvent, newStatus: TaskStatus) => {
  if (!evt.added) return;
  const task = evt.added.element;
  try {
    await taskService.updateStatus(task.task_id, newStatus);
    const local = props.allTasks.find((t: Task) => t.task_id === task.task_id);
    if (local) { local.status = newStatus; local.completed = newStatus === 'completed'; }
  } catch {
    toast.error('更新狀態失敗');
    emit('refresh-all');
  }
};

const onPendingChange = (evt: DraggableChangeEvent) => {
  void onTaskMoved(evt, 'pending');
};

const onInProgressChange = (evt: DraggableChangeEvent) => {
  void onTaskMoved(evt, 'in_progress');
};

const onCompletedChange = (evt: DraggableChangeEvent) => {
  void onTaskMoved(evt, 'completed');
};

const viewKanbanTaskDetail = async (task: Task) => {
  selectedKanbanTask.value = { ...task };
  try {
    const res = await taskService.getSubtasks(task.task_id);
    selectedKanbanTask.value.subtasks = res.data;
  } catch {
    selectedKanbanTask.value.subtasks = [];
  }
  showKanbanTaskModal.value = true;
};

const addSubtask = async () => {
  if (!newSubtaskName.value.trim() || !selectedKanbanTask.value) return;
  try {
    const res = await taskService.createSubtask(selectedKanbanTask.value.task_id, { name: newSubtaskName.value.trim() });
    selectedKanbanTask.value.subtasks.push(res.data);
    newSubtaskName.value = '';
    emit('refresh-all');
  } catch { toast.error('新增子任務失敗'); }
};

const toggleSubtask = async (subtask: Subtask) => {
  if (!selectedKanbanTask.value) return;
  try {
    await taskService.toggleSubtask(selectedKanbanTask.value.task_id, subtask.id);
    subtask.completed = !subtask.completed;
    emit('refresh-all');
  } catch { toast.error('更新子任務失敗'); }
};

const deleteSubtask = async (subtask: Subtask) => {
  if (!selectedKanbanTask.value) return;
  try {
    await taskService.deleteSubtask(selectedKanbanTask.value.task_id, subtask.id);
    selectedKanbanTask.value.subtasks = selectedKanbanTask.value.subtasks.filter((s: Subtask) => s.id !== subtask.id);
    emit('refresh-all');
  } catch { toast.error('刪除子任務失敗'); }
};

const onPrioritySelect = (event: Event) => {
  const target = event.target as HTMLSelectElement | null;
  const priority = Number(target?.value);
  void updateTaskPriority(priority);
};

const updateTaskPriority = async (priority: number) => {
  if (!selectedKanbanTask.value) return;
  try {
    const payload: TaskUpdatePayload = { priority };
    await taskService.update(selectedKanbanTask.value.task_id, payload);
    selectedKanbanTask.value.priority = priority;
    emit('refresh-all');
  } catch { toast.error('更新優先級失敗'); }
};

const updateTaskTags = async () => {
  if (!selectedKanbanTask.value) return;
  try {
    const payload: TaskUpdatePayload = { tags: selectedKanbanTask.value.tags };
    await taskService.update(selectedKanbanTask.value.task_id, payload);
    emit('refresh-all');
  } catch { toast.error('更新標籤失敗'); }
};
</script>

<style>
.frappe-gantt-container .gantt .bar-label.big {
  display: none;
}

.frappe-gantt-container .popup-wrapper {
  max-width: 360px;
}

.frappe-gantt-container .popup-wrapper .details-container h5 {
  margin: 0 0 6px;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: clip !important;
  word-break: break-word;
  line-height: 1.3;
}

.frappe-gantt-container .popup-wrapper .details-container p {
  margin: 2px 0;
  white-space: normal;
  word-break: break-word;
}

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-unknown'] .bar { fill: #94a3b8; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-unknown'] .bar-progress { fill: #64748b; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-0'] .bar { fill: #3b82f6; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-0'] .bar-progress { fill: #1d4ed8; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-1'] .bar { fill: #10b981; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-1'] .bar-progress { fill: #047857; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-2'] .bar { fill: #f59e0b; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-2'] .bar-progress { fill: #b45309; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-3'] .bar { fill: #ef4444; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-3'] .bar-progress { fill: #b91c1c; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-4'] .bar { fill: #8b5cf6; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-4'] .bar-progress { fill: #6d28d9; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-5'] .bar { fill: #06b6d4; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-5'] .bar-progress { fill: #0e7490; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-6'] .bar { fill: #f97316; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-6'] .bar-progress { fill: #c2410c; }

.frappe-gantt-container .bar-wrapper[class*='gantt-owner-7'] .bar { fill: #84cc16; }
.frappe-gantt-container .bar-wrapper[class*='gantt-owner-7'] .bar-progress { fill: #3f6212; }

.frappe-gantt-container .bar-wrapper[class*='-collab'] .bar {
  stroke: #0f172a;
  stroke-width: 1.3;
  stroke-dasharray: 4 2;
}
</style>
