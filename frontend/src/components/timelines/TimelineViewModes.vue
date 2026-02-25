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
            @change="(evt) => onTaskMoved(evt, 'pending')"
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
                    <span class="font-medium">{{ task.subtasks.filter(s => s.completed).length }}/{{ task.subtasks.length }}</span>
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
            @change="(evt) => onTaskMoved(evt, 'in_progress')"
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
                    <span class="font-medium">{{ task.subtasks.filter(s => s.completed).length }}/{{ task.subtasks.length }}</span>
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
            @change="(evt) => onTaskMoved(evt, 'completed')"
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

    <!-- Card View -->
    <div v-if="viewMode === 'card'" class="px-4 pb-8">
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
              <select :value="selectedKanbanTask.priority" @change="updateTaskPriority(Number($event.target.value))" class="px-3 py-1 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
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
              <span class="text-sm font-normal text-gray-500">({{ selectedKanbanTask.subtasks?.filter(s => s.completed).length || 0 }}/{{ selectedKanbanTask.subtasks?.length || 0 }})</span>
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

<script setup>
import { ref, computed } from 'vue';
import draggable from 'vuedraggable';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import multiMonthPlugin from '@fullcalendar/multimonth';
import { taskService } from '../../services/taskService';

const props = defineProps({
  viewMode: String,
  timelines: Array,
  sortedTimelines: Array,
  allTasks: Array,
});

const emit = defineEmits(['view-timeline', 'edit-timeline', 'delete-timeline', 'create-timeline', 'refresh-all']);

// 看板本地狀態
const selectedKanbanTimeline = ref(null);
const searchQuery = ref('');
const showFilterPanel = ref(false);
const filterPriority = ref(null);
const filterTag = ref('');
const isDragging = ref(false);
const showKanbanTaskModal = ref(false);
const selectedKanbanTask = ref(null);
const newSubtaskName = ref('');

// 月曆 ref
const calendarRef = ref(null);

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

// ────────────── 月曆相關 ──────────────
const thisWeekTimelines = computed(() => props.timelines.filter(t => {
  const days = getDaysRemaining(t.endDate).days;
  return days !== null && days >= 0 && days <= 7;
}));
const overdueTimelines = computed(() => props.timelines.filter(t => {
  const days = getDaysRemaining(t.endDate).days;
  return days !== null && days < 0;
}));
const completedTimelines = computed(() => props.timelines.filter(t => getTaskProgress(t) === 100));

const calendarEvents = computed(() => props.timelines.map(timeline => {
  const status = getTimelineStatus(timeline);
  const progress = getTaskProgress(timeline);
  let backgroundColor, borderColor, textColor;
  if (progress === 100) { backgroundColor = '#22c55e'; borderColor = '#15803d'; textColor = '#ffffff'; }
  else if (status.label === '已過期') { backgroundColor = '#ef4444'; borderColor = '#b91c1c'; textColor = '#ffffff'; }
  else if (status.label === '緊急') { backgroundColor = '#f97316'; borderColor = '#c2410c'; textColor = '#ffffff'; }
  else if (status.label === '即將到期') { backgroundColor = '#fbbf24'; borderColor = '#d97706'; textColor = '#78350f'; }
  else { backgroundColor = '#3b82f6'; borderColor = '#1d4ed8'; textColor = '#ffffff'; }
  return {
    id: timeline.id,
    title: `${status.icon} ${timeline.name} (${progress}%)`,
    start: timeline.startDate || timeline.endDate,
    end: timeline.endDate ? addDays(timeline.endDate, 1) : null,
    backgroundColor, borderColor, textColor,
    extendedProps: { timeline, status: status.label, progress }
  };
}));

const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, interactionPlugin, multiMonthPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-tw',
  headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth,multiMonthYear' },
  buttonText: { today: '今天', month: '月', year: '年度' },
  height: 'auto',
  events: calendarEvents.value,
  eventClick: (info) => emit('view-timeline', info.event.extendedProps.timeline),
  eventDidMount: (info) => {
    const el = info.el;
    el.title = `${info.event.title}\n狀態：${info.event.extendedProps.status}\n進度：${info.event.extendedProps.progress}% 完成`;
    el.style.borderRadius = '8px'; el.style.padding = '4px 8px'; el.style.margin = '2px 4px';
    el.style.fontSize = '12px'; el.style.fontWeight = '500'; el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    el.style.border = 'none'; el.style.borderLeft = `4px solid ${info.event.borderColor}`; el.style.transition = 'all 0.2s ease';
    el.addEventListener('mouseenter', () => { el.style.transform = 'translateY(-2px)'; el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)'; });
    el.addEventListener('mouseleave', () => { el.style.transform = 'translateY(0)'; el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)'; });
  },
  dayCellDidMount: (info) => {
    const today = new Date();
    if (info.date.toDateString() === today.toDateString()) { info.el.style.backgroundColor = 'rgba(59, 130, 246, 0.08)'; info.el.style.borderRadius = '8px'; }
    const day = info.date.getDay();
    if (day === 0 || day === 6) info.el.style.backgroundColor = 'rgba(100, 116, 139, 0.03)';
  },
  eventDisplay: 'block', displayEventTime: false,
  eventClassNames: 'cursor-pointer fc-event-custom',
  dayMaxEvents: 3, moreLinkClick: 'popover'
}));

// ────────────── 純工具函式（與 TimelinesView 相同邏輯） ──────────────
const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

const addDays = (dateStr, days) => {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
};

const getDaysRemaining = (endDate) => {
  if (!endDate) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-gray-400' };
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const end = new Date(endDate); end.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((end - today) / (1000 * 60 * 60 * 24));
  if (diffDays < 0) return { days: diffDays, text: `已過期 ${Math.abs(diffDays)} 天`, display: `過期 ${Math.abs(diffDays)} 天`, colorClass: 'text-red-500' };
  if (diffDays === 0) return { days: 0, text: '今天到期', display: '今天到期', colorClass: 'text-red-500' };
  if (diffDays === 1) return { days: 1, text: '明天到期', display: '剩 1 天', colorClass: 'text-orange-500' };
  if (diffDays <= 3) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-orange-500' };
  if (diffDays <= 7) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-yellow-600' };
  if (diffDays <= 30) return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-blue-500' };
  return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-green-500' };
};

const getTaskProgress = (timeline) => {
  if (!timeline.totalTasks || timeline.totalTasks === 0) return 0;
  return Math.round((timeline.completedTasks || 0) / timeline.totalTasks * 100);
};

const getTimeProgress = (timeline) => {
  if (!timeline.startDate || !timeline.endDate) return 0;
  const today = new Date(), start = new Date(timeline.startDate), end = new Date(timeline.endDate);
  if (today < start) return 0;
  if (today > end) return 100;
  return Math.round(((today - start) / (end - start)) * 100);
};

const getTimelineStatus = (timeline) => {
  const { days } = getDaysRemaining(timeline.endDate);
  const progress = getTaskProgress(timeline);
  if (progress === 100) return { label: '已完成', icon: '✅', bgClass: 'bg-green-100', textClass: 'text-green-600', badgeClass: 'bg-green-100 text-green-700', borderClass: 'border-green-200', barClass: 'bg-gradient-to-r from-green-400 to-green-500' };
  if (days === null) return { label: '進行中', icon: '📋', bgClass: 'bg-gray-100', textClass: 'text-gray-600', badgeClass: 'bg-gray-100 text-gray-600', borderClass: 'border-gray-200', barClass: 'bg-gradient-to-r from-gray-300 to-gray-400' };
  if (days < 0) return { label: '已過期', icon: '⚠️', bgClass: 'bg-red-100', textClass: 'text-red-600', badgeClass: 'bg-red-100 text-red-700', borderClass: 'border-red-200', barClass: 'bg-gradient-to-r from-red-400 to-red-500' };
  if (days <= 3) return { label: '緊急', icon: '🔥', bgClass: 'bg-orange-100', textClass: 'text-orange-600', badgeClass: 'bg-orange-100 text-orange-700', borderClass: 'border-orange-200', barClass: 'bg-gradient-to-r from-orange-400 to-orange-500' };
  if (days <= 7) return { label: '即將到期', icon: '⏰', bgClass: 'bg-yellow-100', textClass: 'text-yellow-600', badgeClass: 'bg-yellow-100 text-yellow-700', borderClass: 'border-yellow-200', barClass: 'bg-gradient-to-r from-yellow-400 to-yellow-500' };
  return { label: '進行中', icon: '📋', bgClass: 'bg-blue-100', textClass: 'text-blue-600', badgeClass: 'bg-blue-100 text-blue-700', borderClass: 'border-blue-200', barClass: 'bg-gradient-to-r from-blue-400 to-blue-500' };
};

const getProgressBarColor = (timeline) => {
  const progress = getTaskProgress(timeline), status = getTimelineStatus(timeline);
  if (progress === 100) return 'bg-gradient-to-r from-green-400 to-green-500';
  if (status.label === '已過期') return 'bg-gradient-to-r from-red-400 to-red-500';
  if (status.label === '緊急') return 'bg-gradient-to-r from-orange-400 to-orange-500';
  return 'bg-gradient-to-r from-primary to-primary-light';
};

const getProgressTextColor = (timeline) => {
  const progress = getTaskProgress(timeline);
  if (progress === 100) return 'text-green-600';
  if (progress >= 50) return 'text-blue-600';
  return 'text-gray-600';
};

const getPriorityLabel = (priority) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中');

const getPriorityBadgeClass = (priority) => ({
  1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
  2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
  3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
}[priority] || 'bg-gray-100 text-gray-700 border border-gray-200');

const getSubtaskProgress = (task) => {
  if (!task.subtasks || task.subtasks.length === 0) return 0;
  return Math.round((task.subtasks.filter(s => s.completed).length / task.subtasks.length) * 100);
};

const getTaskTimelineName = (task) => {
  if (!task.timeline_id) return '';
  const tl = props.timelines.find(t => t.id === task.timeline_id);
  return tl ? tl.name : '';
};

// ────────────── 看板操作 ──────────────
const onTaskMoved = async (evt, newStatus) => {
  if (!evt.added) return;
  const task = evt.added.element;
  try {
    await taskService.updateStatus(task.task_id, newStatus);
    const local = props.allTasks.find(t => t.task_id === task.task_id);
    if (local) { local.status = newStatus; local.completed = newStatus === 'completed'; }
  } catch {
    alert('更新狀態失敗');
    emit('refresh-all');
  }
};

const viewKanbanTaskDetail = async (task) => {
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
    selectedKanbanTask.value.subtasks.push(res.data.subtask);
    newSubtaskName.value = '';
    emit('refresh-all');
  } catch { alert('新增子任務失敗'); }
};

const toggleSubtask = async (subtask) => {
  try {
    await taskService.toggleSubtask(selectedKanbanTask.value.task_id, subtask.id);
    subtask.completed = !subtask.completed;
    emit('refresh-all');
  } catch { alert('更新子任務失敗'); }
};

const deleteSubtask = async (subtask) => {
  try {
    await taskService.deleteSubtask(selectedKanbanTask.value.task_id, subtask.id);
    selectedKanbanTask.value.subtasks = selectedKanbanTask.value.subtasks.filter(s => s.id !== subtask.id);
    emit('refresh-all');
  } catch { alert('刪除子任務失敗'); }
};

const updateTaskPriority = async (priority) => {
  if (!selectedKanbanTask.value) return;
  try {
    await taskService.update(selectedKanbanTask.value.task_id, { ...selectedKanbanTask.value, priority });
    selectedKanbanTask.value.priority = priority;
    emit('refresh-all');
  } catch { alert('更新優先級失敗'); }
};

const updateTaskTags = async () => {
  if (!selectedKanbanTask.value) return;
  try {
    await taskService.update(selectedKanbanTask.value.task_id, { ...selectedKanbanTask.value, tags: selectedKanbanTask.value.tags });
    emit('refresh-all');
  } catch { alert('更新標籤失敗'); }
};
</script>
