<template>
  <div class="h-full w-full bg-linear-to-br from-slate-50 to-blue-50/30 p-6 overflow-y-auto">
    <div class="grid grid-cols-1 gap-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="text-center pt-6 pb-2 px-4 animate-slideDown">
      <div class="inline-flex items-center gap-3 bg-white/80 backdrop-blur-sm px-6 py-3 rounded-2xl shadow-sm mb-4">
        <span class="text-4xl">📊</span>
        <div class="text-left">
          <h1 class="text-2xl font-bold text-gray-800">專案管理</h1>
          <p class="text-sm text-gray-500">{{ todayFormatted }}</p>
        </div>
      </div>
    </div>
    
    <!-- Stats Overview -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 px-4">
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">📁</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-gray-800">{{ timelines.length }}</p>
            <p class="text-xs text-gray-500">進行中專案</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">⚠️</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-orange-600">{{ urgentCount }}</p>
            <p class="text-xs text-gray-500">即將到期</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">✅</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-green-600">{{ totalCompletedTasks }}</p>
            <p class="text-xs text-gray-500">已完成任務</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <span class="text-xl">📋</span>
          </div>
          <div>
            <p class="text-2xl font-bold text-purple-600">{{ totalTasks }}</p>
            <p class="text-xs text-gray-500">總任務數</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- View Toggle & Action Bar -->
    <div class="flex flex-col sm:flex-row justify-between items-center gap-4 px-4">
      <!-- View Toggle -->
      <div class="flex bg-white rounded-xl p-1 shadow-sm border border-gray-100">
        <button 
          @click="viewMode = 'card'"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'card' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📇</span> 卡片
        </button>
        <button 
          @click="viewMode = 'kanban'"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'kanban' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📊</span> 看板
        </button>
        <button 
          @click="viewMode = 'timeline'"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'timeline' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📋</span> 列表
        </button>
        <button 
          @click="viewMode = 'calendar'"
          :class="[
            'px-4 py-2 rounded-lg text-sm font-medium transition-all',
            viewMode === 'calendar' ? 'bg-primary text-white shadow-sm' : 'text-gray-600 hover:bg-gray-100'
          ]"
        >
          <span class="mr-1">📅</span> 月曆
        </button>
      </div>
      
      <!-- Add Button -->
      <button 
        @click="showCreateModal = true"
        class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:brightness-110 transition-all"
      >
        <span class="text-lg">➕</span>
        <span>新增專案</span>
      </button>
    </div>
    
    <!-- Kanban View (看板模式) -->
    <div v-if="viewMode === 'kanban'" class="px-4 pb-8">
      <!-- 專案選擇器 -->
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
        
        <!-- 搜尋框 -->
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
        
        <!-- 篩選按鈕 -->
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
      
      <!-- 篩選面板 -->
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
      
      <!-- 看板欄位 - 使用 vuedraggable -->
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
            @start="onDragStart"
            @end="onDragEnd"
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
                  <span v-for="tag in task.tags.split(',').slice(0, 3)" :key="tag" class="text-xs px-2 py-0.5 bg-linear-to-r from-blue-100 to-indigo-100 text-blue-700 rounded-full">
                    {{ tag.trim() }}
                  </span>
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
                  <span class="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded-md">
                    📅 {{ formatDate(task.end_date) }}
                  </span>
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
            @start="onDragStart"
            @end="onDragEnd"
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
                  <span v-for="tag in task.tags.split(',').slice(0, 3)" :key="tag" class="text-xs px-2 py-0.5 bg-linear-to-r from-blue-100 to-indigo-100 text-blue-700 rounded-full">
                    {{ tag.trim() }}
                  </span>
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
                  <span class="flex items-center gap-1 bg-blue-100 px-2 py-1 rounded-md text-blue-600">
                    📅 {{ formatDate(task.end_date) }}
                  </span>
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
            @start="onDragStart"
            @end="onDragEnd"
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
                  <span class="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 shrink-0 ml-2 font-medium">
                    ✓ 完成
                  </span>
                </div>
                <div class="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-100">
                  <span class="flex items-center gap-1 bg-green-100 px-2 py-1 rounded-md text-green-600">
                    📅 {{ formatDate(task.end_date) }}
                  </span>
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
        <!-- Calendar Legend -->
        <div class="p-5 border-b border-gray-100 bg-gradient-to-r from-primary/5 via-blue-50 to-indigo-50">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <h3 class="font-bold text-gray-800 flex items-center gap-2 text-lg">
              <span class="w-10 h-10 bg-white rounded-xl shadow-sm flex items-center justify-center">📅</span>
              專案月曆
            </h3>
            <div class="flex flex-wrap items-center gap-4 text-sm bg-white/80 backdrop-blur-sm px-4 py-2.5 rounded-xl shadow-sm">
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-gradient-to-r from-green-400 to-green-500 shadow-sm"></span> 已完成</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-gradient-to-r from-red-400 to-red-500 shadow-sm"></span> 已過期</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-gradient-to-r from-orange-400 to-orange-500 shadow-sm"></span> 緊急</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-gradient-to-r from-yellow-400 to-yellow-500 shadow-sm"></span> 即將到期</span>
              <span class="flex items-center gap-2"><span class="w-4 h-4 rounded-md bg-gradient-to-r from-blue-400 to-blue-500 shadow-sm"></span> 進行中</span>
            </div>
          </div>
        </div>
        
        <!-- FullCalendar -->
        <div class="p-6">
          <FullCalendar 
            ref="calendarRef"
            :options="calendarOptions" 
            class="fc-custom"
          />
        </div>
      </div>
      
      <!-- Quick Stats Below Calendar -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
        <div class="bg-white rounded-2xl p-5 shadow-lg border border-gray-100 hover:shadow-xl transition-shadow">
          <h4 class="text-sm font-bold text-gray-700 mb-4 flex items-center gap-2">
            <span class="w-8 h-8 bg-orange-100 rounded-lg flex items-center justify-center">📌</span>
            本週截止
          </h4>
          <div class="space-y-2 max-h-36 overflow-y-auto">
            <div 
              v-for="timeline in thisWeekTimelines" 
              :key="timeline.id"
              @click="viewTimeline(timeline)"
              class="flex items-center justify-between p-3 bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl cursor-pointer hover:from-orange-100 hover:to-amber-100 transition-all border border-orange-100"
            >
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
            <div 
              v-for="timeline in overdueTimelines" 
              :key="timeline.id"
              @click="viewTimeline(timeline)"
              class="flex items-center justify-between p-3 bg-gradient-to-r from-red-50 to-rose-50 rounded-xl cursor-pointer hover:from-red-100 hover:to-rose-100 transition-all border border-red-100"
            >
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
            <div 
              v-for="timeline in completedTimelines" 
              :key="timeline.id"
              @click="viewTimeline(timeline)"
              class="flex items-center justify-between p-3 bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl cursor-pointer hover:from-green-100 hover:to-emerald-100 transition-all border border-green-100"
            >
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs bg-green-500 text-white px-2 py-1 rounded-full font-medium">100%</span>
            </div>
            <p v-if="completedTimelines.length === 0" class="text-sm text-gray-400 text-center py-4">🎯 尚無完成專案</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Create/Edit Project Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-gradient-to-r from-primary/5 to-transparent">
          <h2 class="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📁</span>
            {{ editingTimeline ? '編輯專案' : '新增專案' }}
          </h2>
          <button @click="closeModal" class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors">&times;</button>
        </div>
        
        <form @submit.prevent="handleSubmit" class="p-5 space-y-5">
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">專案名稱 *</label>
            <input 
              v-model.lazy="timelineForm.name" 
              type="text" 
              placeholder="例如:Q1 產品開發計畫"
              class="w-full px-4 py-3 text-base border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all bg-gray-50/50"
              required
            />
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">開始日期</label>
              <input 
                v-model.lazy="timelineForm.start_date" 
                type="date" 
                class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all bg-gray-50/50"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-700 mb-2">結束日期</label>
              <input 
                v-model.lazy="timelineForm.end_date" 
                type="date" 
                class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all bg-gray-50/50"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-700 mb-2">專案備註</label>
            <textarea 
              v-model.lazy="timelineForm.remark" 
              rows="3"
              placeholder="描述專案目標、重要里程碑..."
              class="w-full px-4 py-3 text-sm border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all resize-none bg-gray-50/50"
            ></textarea>
          </div>
          
          <div class="flex gap-3 pt-2">
            <button 
              type="submit"
              class="flex-1 py-3 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2"
            >
              <span>✓</span>
              {{ editingTimeline ? '更新專案' : '建立專案' }}
            </button>
            <button 
              type="button"
              @click="closeModal"
              class="flex-1 py-3 bg-gray-100 text-gray-700 font-semibold rounded-xl hover:bg-gray-200 transition-all"
            >
              取消
            </button>
          </div>
        </form>
      </div>
    </div>
    
    <!-- Timeline View -->
    <div v-if="viewMode === 'timeline'" class="px-4 pb-8">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <!-- Timeline Header -->
        <div class="p-4 border-b border-gray-100 bg-gray-50/50">
          <div class="flex items-center justify-between">
            <h3 class="font-semibold text-gray-700">📋 專案列表</h3>
            <span class="text-sm text-gray-500">依結束日期排序</span>
          </div>
        </div>
        
        <!-- Timeline Items -->
        <div class="divide-y divide-gray-100">
          <div 
            v-for="timeline in sortedTimelines" 
            :key="timeline.id"
            @click="viewTimeline(timeline)"
            class="p-4 hover:bg-blue-50/50 cursor-pointer transition-colors"
          >
            <div class="flex items-start gap-4">
              <!-- Date Column -->
              <div class="shrink-0 w-20 text-center">
                <div 
                  :class="[
                    'w-12 h-12 mx-auto rounded-xl flex flex-col items-center justify-center',
                    getTimelineStatus(timeline).bgClass
                  ]"
                >
                  <span class="text-xs font-medium" :class="getTimelineStatus(timeline).textClass">
                    {{ timeline.endDate ? new Date(timeline.endDate).getMonth() + 1 + '月' : '--' }}
                  </span>
                  <span class="text-lg font-bold -mt-1" :class="getTimelineStatus(timeline).textClass">
                    {{ timeline.endDate ? new Date(timeline.endDate).getDate() : '--' }}
                  </span>
                </div>
                <p class="text-xs text-gray-400 mt-1">
                  {{ getDaysRemaining(timeline.endDate).text }}
                </p>
              </div>
              
              <!-- Content -->
              <div class="flex-1 min-w-0">
                <div class="flex items-start justify-between gap-2 mb-2">
                  <h4 class="font-semibold text-gray-800 truncate">{{ timeline.name }}</h4>
                  <span 
                    :class="[
                      'shrink-0 px-2 py-0.5 text-xs font-medium rounded-full',
                      getTimelineStatus(timeline).badgeClass
                    ]"
                  >
                    {{ getTimelineStatus(timeline).label }}
                  </span>
                </div>
                
                <!-- Progress Bar -->
                <div class="mb-2">
                  <div class="flex items-center gap-2">
                    <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div 
                        :class="['h-full rounded-full transition-all duration-500', getProgressBarColor(timeline)]"
                        :style="{ width: getTaskProgress(timeline) + '%' }"
                      ></div>
                    </div>
                    <span class="text-xs font-medium text-gray-500 w-10 text-right">{{ getTaskProgress(timeline) }}%</span>
                  </div>
                </div>
                
                <!-- Meta Info -->
                <div class="flex items-center gap-4 text-xs text-gray-500">
                  <span class="flex items-center gap-1">
                    <span>📅</span>
                    {{ formatDate(timeline.startDate) }} - {{ formatDate(timeline.endDate) }}
                  </span>
                  <span class="flex items-center gap-1">
                    <span>✅</span>
                    {{ timeline.completedTasks || 0 }}/{{ timeline.totalTasks || 0 }}
                  </span>
                </div>
              </div>
              
              <!-- Actions -->
              <div class="shrink-0 flex items-center gap-1" @click.stop>
                <button 
                  @click="editTimeline(timeline)"
                  class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                >✏️</button>
                <button 
                  @click="deleteTimeline(timeline.id)"
                  class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >🗑️</button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- Empty State -->
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
          v-for="timeline in sortedTimelines" 
          :key="timeline.id"
          @click="viewTimeline(timeline)"
          :class="[
            'group bg-white rounded-2xl shadow-sm border hover:-translate-y-1 hover:shadow-lg transition-all cursor-pointer overflow-hidden',
            getTimelineStatus(timeline).borderClass
          ]"
        >
          <!-- Status Bar -->
          <div :class="['h-1.5', getTimelineStatus(timeline).barClass]"></div>
          
          <div class="p-5">
            <!-- Header -->
            <div class="flex justify-between items-start mb-4">
              <div class="flex-1 min-w-0">
                <h3 class="font-semibold text-gray-800 truncate mb-1">{{ timeline.name }}</h3>
                <span 
                  :class="[
                    'inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded-full',
                    getTimelineStatus(timeline).badgeClass
                  ]"
                >
                  {{ getTimelineStatus(timeline).icon }} {{ getTimelineStatus(timeline).label }}
                </span>
              </div>
              <div class="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" @click.stop>
                <button 
                  @click="editTimeline(timeline)"
                  class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-primary hover:bg-primary/10 rounded-lg transition-colors"
                >✏️</button>
                <button 
                  @click="deleteTimeline(timeline.id)"
                  class="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                >🗑️</button>
              </div>
            </div>
            
            <!-- Days Remaining -->
            <div class="flex items-center justify-between mb-4 p-3 bg-gray-50 rounded-xl">
              <div class="flex items-center gap-2">
                <span :class="['text-2xl', getTimelineStatus(timeline).emoji]">
                  {{ getTimelineStatus(timeline).icon }}
                </span>
                <div>
                  <p class="text-xs text-gray-500">剩餘時間</p>
                  <p :class="['text-lg font-bold', getDaysRemaining(timeline.endDate).colorClass]">
                    {{ getDaysRemaining(timeline.endDate).display }}
                  </p>
                </div>
              </div>
              <div class="text-right">
                <p class="text-xs text-gray-500">截止日期</p>
                <p class="text-sm font-medium text-gray-700">{{ formatDate(timeline.endDate) || '未設定' }}</p>
              </div>
            </div>
            
            <!-- Time Progress (Visual Timeline) -->
            <div class="mb-4" v-if="timeline.startDate && timeline.endDate">
              <div class="flex justify-between text-xs text-gray-400 mb-1">
                <span>{{ formatDate(timeline.startDate) }}</span>
                <span>{{ formatDate(timeline.endDate) }}</span>
              </div>
              <div class="relative h-2 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  class="absolute left-0 top-0 h-full bg-linear-to-r from-blue-400 to-blue-500 rounded-full transition-all duration-500"
                  :style="{ width: getTimeProgress(timeline) + '%' }"
                ></div>
                <!-- Today Marker -->
                <div 
                  v-if="getTimeProgress(timeline) > 0 && getTimeProgress(timeline) < 100"
                  class="absolute top-1/2 -translate-y-1/2 w-3 h-3 bg-white border-2 border-blue-500 rounded-full shadow-sm"
                  :style="{ left: getTimeProgress(timeline) + '%', transform: 'translate(-50%, -50%)' }"
                ></div>
              </div>
              <p class="text-xs text-gray-400 text-center mt-1">時程進度 {{ getTimeProgress(timeline) }}%</p>
            </div>
            
            <!-- Task Progress -->
            <div class="mb-4">
              <div class="flex justify-between text-sm mb-1">
                <span class="text-gray-500">任務完成度</span>
                <span class="font-semibold" :class="getProgressTextColor(timeline)">
                  {{ timeline.completedTasks || 0 }} / {{ timeline.totalTasks || 0 }}
                </span>
              </div>
              <div class="h-2.5 bg-gray-100 rounded-full overflow-hidden">
                <div 
                  :class="['h-full rounded-full transition-all duration-500', getProgressBarColor(timeline)]"
                  :style="{ width: getTaskProgress(timeline) + '%' }"
                ></div>
              </div>
            </div>
            
            <!-- Footer -->
            <div class="flex items-center justify-between pt-3 border-t border-gray-100">
              <div class="flex items-center gap-2 text-xs text-gray-400">
                <span>📅 {{ formatDate(timeline.startDate) || '未設定' }}</span>
              </div>
              <span class="text-xs text-primary font-medium group-hover:underline">查看詳情 →</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-if="timelines.length === 0" class="text-center py-16 bg-white rounded-2xl border border-dashed border-gray-200">
        <span class="text-6xl block mb-4">📁</span>
        <p class="text-xl text-gray-600 mb-2">目前尚無專案</p>
        <p class="text-sm text-gray-400 mb-6">建立您的第一個專案來開始追蹤進度</p>
        <button 
          @click="showCreateModal = true"
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-primary text-white font-semibold rounded-xl shadow-lg shadow-primary/25 hover:shadow-xl transition-all"
        >
          <span>➕</span> 新增專案
        </button>
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
              class="px-4 py-2 bg-linear-to-r from-primary to-primary-light text-white rounded-lg hover:brightness-110 transition-all flex items-center gap-2"
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
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg transition-all duration-300 opacity-0 translate-y-8 max-h-[90vh] overflow-y-auto" :class="showAddTaskModal ? 'opacity-100 translate-y-0' : ''">
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
              v-model.lazy="taskForm.name" 
              type="text" 
              placeholder="請輸入任務名稱"
              class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              required
            />
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">快速筆記（選填）</label>
            <input 
              v-model.lazy="taskForm.assistant" 
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
                v-model.lazy="taskForm.start_date" 
                type="datetime-local" 
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">截止日期 *</label>
              <input 
                v-model.lazy="taskForm.end_date" 
                type="datetime-local" 
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                required
              />
            </div>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">優先級</label>
              <select 
                v-model="taskForm.priority"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              >
                <option :value="1">🔴 高優先</option>
                <option :value="2">🟡 中優先</option>
                <option :value="3">🟢 低優先</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-semibold text-gray-600 mb-2">標籤（逗號分隔）</label>
              <input 
                v-model.lazy="taskForm.tags" 
                type="text" 
                placeholder="例如：前端, 重要"
                class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
              />
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-semibold text-gray-600 mb-2">備註</label>
            <textarea 
              v-model.lazy="taskForm.task_remark" 
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
              class="flex-1 py-3 bg-linear-to-r from-primary to-primary-light text-white font-semibold rounded-xl hover:brightness-110 transition-all flex items-center justify-center gap-2"
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
          <!-- 狀態與優先級 -->
          <div class="flex flex-wrap items-center gap-4">
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">狀態：</span>
              <span :class="[
                'px-3 py-1 text-sm font-medium rounded-full',
                selectedKanbanTask.status === 'completed' ? 'bg-green-100 text-green-700' :
                selectedKanbanTask.status === 'in_progress' ? 'bg-blue-100 text-blue-700' :
                'bg-gray-100 text-gray-700'
              ]">
                {{ selectedKanbanTask.status === 'completed' ? '✅ 已完成' : 
                   selectedKanbanTask.status === 'in_progress' ? '🔄 進行中' : '📋 待辦' }}
              </span>
            </div>
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">優先級：</span>
              <select 
                :value="selectedKanbanTask.priority"
                @change="updateTaskPriority(Number($event.target.value))"
                class="px-3 py-1 text-sm border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
              >
                <option :value="1">🔴 高優先</option>
                <option :value="2">🟡 中優先</option>
                <option :value="3">🟢 低優先</option>
              </select>
            </div>
          </div>
          
          <!-- 日期資訊 -->
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
          
          <!-- 標籤編輯 -->
          <div>
            <label class="block text-sm font-medium text-gray-600 mb-2">
              <span>🏷️</span> 標籤（逗號分隔）
            </label>
            <div class="flex gap-2">
              <input 
                v-model="selectedKanbanTask.tags"
                type="text"
                placeholder="例如：前端, 重要, Bug"
                class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
              />
              <button 
                @click="updateTaskTags"
                class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all"
              >儲存</button>
            </div>
            <div v-if="selectedKanbanTask.tags" class="flex flex-wrap gap-2 mt-2">
              <span 
                v-for="tag in selectedKanbanTask.tags.split(',')" 
                :key="tag"
                class="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded-full"
              >
                {{ tag.trim() }}
              </span>
            </div>
          </div>
          
          <!-- 子任務 -->
          <div>
            <h4 class="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <span>📋</span>
              子任務
              <span class="text-sm font-normal text-gray-500">
                ({{ selectedKanbanTask.subtasks?.filter(s => s.completed).length || 0 }}/{{ selectedKanbanTask.subtasks?.length || 0 }})
              </span>
            </h4>
            
            <!-- 子任務進度條 -->
            <div v-if="selectedKanbanTask.subtasks && selectedKanbanTask.subtasks.length > 0" class="mb-4">
              <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                <div 
                  class="h-full bg-primary rounded-full transition-all duration-300"
                  :style="{ width: getSubtaskProgress(selectedKanbanTask) + '%' }"
                ></div>
              </div>
            </div>
            
            <!-- 子任務列表 -->
            <div class="space-y-2 mb-4">
              <div 
                v-for="subtask in selectedKanbanTask.subtasks" 
                :key="subtask.id"
                class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg group hover:bg-gray-100 transition-colors"
              >
                <input 
                  type="checkbox"
                  :checked="subtask.completed"
                  @change="toggleSubtask(subtask)"
                  class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer"
                />
                <span :class="['flex-1 text-sm', subtask.completed ? 'line-through text-gray-400' : 'text-gray-700']">
                  {{ subtask.name }}
                </span>
                <button 
                  @click="deleteSubtask(subtask)"
                  class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all"
                >🗑️</button>
              </div>
              <div v-if="!selectedKanbanTask.subtasks || selectedKanbanTask.subtasks.length === 0" class="text-center py-4 text-gray-400 text-sm">
                尚無子任務
              </div>
            </div>
            
            <!-- 新增子任務 -->
            <div class="flex gap-2">
              <input 
                v-model="newSubtaskName"
                type="text"
                placeholder="輸入子任務名稱..."
                @keyup.enter="addSubtask"
                class="flex-1 px-4 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
              />
              <button 
                @click="addSubtask"
                class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all"
              >新增</button>
            </div>
          </div>
          
          <!-- 備註 -->
          <div v-if="selectedKanbanTask.task_remark" class="p-4 bg-yellow-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-2 flex items-center gap-2">
              <span>📝</span> 備註
            </h4>
            <p class="text-gray-600 text-sm">{{ selectedKanbanTask.task_remark }}</p>
          </div>
        </div>
      </div>
    </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import api from '../services/api';
import FullCalendar from '@fullcalendar/vue3';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
import multiMonthPlugin from '@fullcalendar/multimonth';
import draggable from 'vuedraggable';

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
const viewMode = ref('card'); // 'card', 'kanban', 'timeline', or 'calendar'
const calendarRef = ref(null);

// 看板模式相關
const allTasks = ref([]);
const selectedKanbanTimeline = ref(null);
const searchQuery = ref('');
const showFilterPanel = ref(false);
const filterPriority = ref(null);
const filterTag = ref('');
const showKanbanTaskModal = ref(false);
const selectedKanbanTask = ref(null);
const newSubtaskName = ref('');
const isDragging = ref(false);

// 取得所有任務（看板用）
const fetchAllTasks = async () => {
  try {
    const response = await api.get('/tasks');
    allTasks.value = response.data;
  } catch (error) {
    console.error('取得任務失敗:', error);
  }
};

// 所有可用的標籤（從所有任務中提取）
const allTags = computed(() => {
  const tagSet = new Set();
  allTasks.value.forEach(task => {
    if (task.tags) {
      task.tags.split(',').forEach(tag => {
        const trimmed = tag.trim();
        if (trimmed) tagSet.add(trimmed);
      });
    }
  });
  return Array.from(tagSet).sort();
});

// 篩選後的任務
const filteredTasks = computed(() => {
  let tasks = allTasks.value;
  
  // 專案篩選
  if (selectedKanbanTimeline.value) {
    tasks = tasks.filter(t => t.timeline_id === selectedKanbanTimeline.value);
  }
  
  // 搜尋篩選
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    tasks = tasks.filter(t => t.name.toLowerCase().includes(query));
  }
  
  // 優先級篩選
  if (filterPriority.value) {
    tasks = tasks.filter(t => t.priority === filterPriority.value);
  }
  
  // 標籤篩選
  if (filterTag.value) {
    const tag = filterTag.value.toLowerCase();
    tasks = tasks.filter(t => t.tags && t.tags.toLowerCase().includes(tag));
  }
  
  return tasks;
});

// 看板欄位任務 (唯讀)
const pendingTasks = computed(() => filteredTasks.value.filter(t => t.status === 'pending' && !t.completed));
const inProgressTasks = computed(() => filteredTasks.value.filter(t => t.status === 'in_progress' && !t.completed));
const completedTasks = computed(() => filteredTasks.value.filter(t => t.status === 'completed' || t.completed));

// 看板欄位任務列表 (可寫入，供 vuedraggable 使用)
const pendingTasksList = computed({
  get: () => pendingTasks.value,
  set: (val) => { /* 由 onTaskMoved 處理 */ }
});
const inProgressTasksList = computed({
  get: () => inProgressTasks.value,
  set: (val) => { /* 由 onTaskMoved 處理 */ }
});
const completedTasksList = computed({
  get: () => completedTasks.value,
  set: (val) => { /* 由 onTaskMoved 處理 */ }
});

// 篩選相關
const hasActiveFilters = computed(() => filterPriority.value || filterTag.value);
const activeFilterCount = computed(() => {
  let count = 0;
  if (filterPriority.value) count++;
  if (filterTag.value) count++;
  return count;
});

const clearFilters = () => {
  filterPriority.value = null;
  filterTag.value = '';
};

// 拖曳相關 - 使用 vuedraggable
const onDragStart = () => {
  isDragging.value = true;
};

const onDragEnd = () => {
  isDragging.value = false;
};

// 處理任務狀態變更
const onTaskMoved = async (evt, newStatus) => {
  if (evt.added) {
    const task = evt.added.element;
    try {
      await api.patch(`/tasks/${task.task_id}/status`, { status: newStatus });
      // 更新本地狀態
      const localTask = allTasks.value.find(t => t.task_id === task.task_id);
      if (localTask) {
        localTask.status = newStatus;
        localTask.completed = newStatus === 'completed';
      }
    } catch (error) {
      console.error('更新狀態失敗:', error);
      alert('更新狀態失敗');
      // 重新載入任務以回復狀態
      await fetchAllTasks();
    }
  }
};

// 優先級相關
const getPriorityLabel = (priority) => {
  const labels = { 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' };
  return labels[priority] || '🟡 中';
};

const getPriorityBadgeClass = (priority) => {
  const classes = {
    1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
    2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
    3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
  };
  return classes[priority] || 'bg-gray-100 text-gray-700 border border-gray-200';
};

// 子任務進度
const getSubtaskProgress = (task) => {
  if (!task.subtasks || task.subtasks.length === 0) return 0;
  const completed = task.subtasks.filter(s => s.completed).length;
  return Math.round((completed / task.subtasks.length) * 100);
};

// 取得任務所屬專案名稱
const getTaskTimelineName = (task) => {
  if (!task.timeline_id) return '';
  const timeline = timelines.value.find(t => t.id === task.timeline_id);
  return timeline ? timeline.name : '';
};

// 看板任務詳情
const viewKanbanTaskDetail = async (task) => {
  selectedKanbanTask.value = { ...task };
  
  // 取得子任務
  try {
    const response = await api.get(`/tasks/${task.task_id}/subtasks`);
    selectedKanbanTask.value.subtasks = response.data;
  } catch (error) {
    console.error('取得子任務失敗:', error);
    selectedKanbanTask.value.subtasks = [];
  }
  
  showKanbanTaskModal.value = true;
};

// 新增子任務
const addSubtask = async () => {
  if (!newSubtaskName.value.trim() || !selectedKanbanTask.value) return;
  
  try {
    const response = await api.post(`/tasks/${selectedKanbanTask.value.task_id}/subtasks`, {
      name: newSubtaskName.value.trim()
    });
    selectedKanbanTask.value.subtasks.push(response.data.subtask);
    newSubtaskName.value = '';
    await fetchAllTasks();
  } catch (error) {
    alert('新增子任務失敗');
  }
};

// 切換子任務完成狀態
const toggleSubtask = async (subtask) => {
  try {
    await api.patch(`/tasks/${selectedKanbanTask.value.task_id}/subtasks/${subtask.id}/toggle`);
    subtask.completed = !subtask.completed;
    await fetchAllTasks();
  } catch (error) {
    alert('更新子任務失敗');
  }
};

// 刪除子任務
const deleteSubtask = async (subtask) => {
  try {
    await api.delete(`/tasks/${selectedKanbanTask.value.task_id}/subtasks/${subtask.id}`);
    selectedKanbanTask.value.subtasks = selectedKanbanTask.value.subtasks.filter(s => s.id !== subtask.id);
    await fetchAllTasks();
  } catch (error) {
    alert('刪除子任務失敗');
  }
};

// 更新任務優先級
const updateTaskPriority = async (priority) => {
  if (!selectedKanbanTask.value) return;
  
  try {
    await api.put(`/tasks/${selectedKanbanTask.value.task_id}`, {
      ...selectedKanbanTask.value,
      priority
    });
    selectedKanbanTask.value.priority = priority;
    await fetchAllTasks();
  } catch (error) {
    alert('更新優先級失敗');
  }
};

// 更新任務標籤
const updateTaskTags = async () => {
  if (!selectedKanbanTask.value) return;
  
  try {
    await api.put(`/tasks/${selectedKanbanTask.value.task_id}`, {
      ...selectedKanbanTask.value,
      tags: selectedKanbanTask.value.tags
    });
    await fetchAllTasks();
  } catch (error) {
    alert('更新標籤失敗');
  }
};

// FullCalendar 設定
const calendarOptions = computed(() => ({
  plugins: [dayGridPlugin, interactionPlugin, multiMonthPlugin],
  initialView: 'dayGridMonth',
  locale: 'zh-tw',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,multiMonthYear'
  },
  buttonText: {
    today: '今天',
    month: '月',
    year: '年度'
  },
  height: 'auto',
  events: calendarEvents.value,
  eventClick: handleEventClick,
  eventDidMount: (info) => {
    // 添加自定義樣式和 tooltip
    const el = info.el;
    const progress = info.event.extendedProps.progress;
    
    // 添加 tooltip
    el.title = `${info.event.title}\n狀態：${info.event.extendedProps.status}\n進度：${progress}% 完成`;
    
    // 美化事件樣式
    el.style.borderRadius = '8px';
    el.style.padding = '4px 8px';
    el.style.margin = '2px 4px';
    el.style.fontSize = '12px';
    el.style.fontWeight = '500';
    el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    el.style.border = 'none';
    el.style.borderLeft = `4px solid ${info.event.borderColor}`;
    el.style.transition = 'all 0.2s ease';
    
    // Hover 效果
    el.addEventListener('mouseenter', () => {
      el.style.transform = 'translateY(-2px)';
      el.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    });
    el.addEventListener('mouseleave', () => {
      el.style.transform = 'translateY(0)';
      el.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
    });
  },
  dayCellDidMount: (info) => {
    // 標記今天
    const today = new Date();
    if (info.date.toDateString() === today.toDateString()) {
      info.el.style.backgroundColor = 'rgba(59, 130, 246, 0.08)';
      info.el.style.borderRadius = '8px';
    }
    // 週末淡色背景
    const day = info.date.getDay();
    if (day === 0 || day === 6) {
      info.el.style.backgroundColor = 'rgba(100, 116, 139, 0.03)';
    }
  },
  eventDisplay: 'block',
  displayEventTime: false,
  eventClassNames: 'cursor-pointer fc-event-custom',
  dayMaxEvents: 3,
  moreLinkClick: 'popover'
}));

// 將專案轉換為日曆事件
const calendarEvents = computed(() => {
  return timelines.value.map(timeline => {
    const status = getTimelineStatus(timeline);
    const progress = getTaskProgress(timeline);
    
    // 根據狀態決定漸層顏色
    let backgroundColor, borderColor, textColor;
    if (progress === 100) {
      backgroundColor = 'linear-gradient(135deg, #22c55e 0%, #16a34a 100%)';
      borderColor = '#15803d';
      textColor = '#ffffff';
    } else if (status.label === '已過期') {
      backgroundColor = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
      borderColor = '#b91c1c';
      textColor = '#ffffff';
    } else if (status.label === '緊急') {
      backgroundColor = 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)';
      borderColor = '#c2410c';
      textColor = '#ffffff';
    } else if (status.label === '即將到期') {
      backgroundColor = 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)';
      borderColor = '#d97706';
      textColor = '#78350f';
    } else {
      backgroundColor = 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)';
      borderColor = '#1d4ed8';
      textColor = '#ffffff';
    }
    
    return {
      id: timeline.id,
      title: `${status.icon} ${timeline.name} (${progress}%)`,
      start: timeline.startDate || timeline.endDate,
      end: timeline.endDate ? addDays(timeline.endDate, 1) : null,
      backgroundColor: backgroundColor.includes('linear') ? backgroundColor.match(/#[a-f0-9]{6}/i)?.[0] || '#3b82f6' : backgroundColor,
      borderColor,
      textColor,
      extendedProps: {
        timeline,
        status: status.label,
        progress,
        gradient: backgroundColor
      }
    };
  });
});

// 日期加天數
const addDays = (dateStr, days) => {
  if (!dateStr) return null;
  const date = new Date(dateStr);
  date.setDate(date.getDate() + days);
  return date.toISOString().split('T')[0];
};

// 處理日曆事件點擊
const handleEventClick = (info) => {
  const timeline = info.event.extendedProps.timeline;
  viewTimeline(timeline);
};

// 本週截止的專案
const thisWeekTimelines = computed(() => {
  return timelines.value.filter(t => {
    const days = getDaysRemaining(t.endDate).days;
    return days !== null && days >= 0 && days <= 7;
  });
});

// 已過期的專案
const overdueTimelines = computed(() => {
  return timelines.value.filter(t => {
    const days = getDaysRemaining(t.endDate).days;
    return days !== null && days < 0;
  });
});

// 已完成的專案
const completedTimelines = computed(() => {
  return timelines.value.filter(t => getTaskProgress(t) === 100);
});

// 今日日期格式化
const todayFormatted = computed(() => {
  const today = new Date();
  const options = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' };
  return today.toLocaleDateString('zh-TW', options);
});

// 統計數據
const urgentCount = computed(() => {
  return timelines.value.filter(t => {
    const days = getDaysRemaining(t.endDate).days;
    return days !== null && days >= 0 && days <= 7;
  }).length;
});

const totalCompletedTasks = computed(() => {
  return timelines.value.reduce((sum, t) => sum + (t.completedTasks || 0), 0);
});

const totalTasks = computed(() => {
  return timelines.value.reduce((sum, t) => sum + (t.totalTasks || 0), 0);
});

// 依結束日期排序的專案列表
const sortedTimelines = computed(() => {
  return [...timelines.value].sort((a, b) => {
    if (!a.endDate && !b.endDate) return 0;
    if (!a.endDate) return 1;
    if (!b.endDate) return -1;
    return new Date(a.endDate) - new Date(b.endDate);
  });
});

// 計算剩餘天數
const getDaysRemaining = (endDate) => {
  if (!endDate) return { days: null, text: '未設定', display: '未設定', colorClass: 'text-gray-400' };
  
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const end = new Date(endDate);
  end.setHours(0, 0, 0, 0);
  
  const diffTime = end - today;
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
  
  if (diffDays < 0) {
    return { 
      days: diffDays, 
      text: `已過期 ${Math.abs(diffDays)} 天`, 
      display: `過期 ${Math.abs(diffDays)} 天`,
      colorClass: 'text-red-500' 
    };
  } else if (diffDays === 0) {
    return { days: 0, text: '今天到期', display: '今天到期', colorClass: 'text-red-500' };
  } else if (diffDays === 1) {
    return { days: 1, text: '明天到期', display: '剩 1 天', colorClass: 'text-orange-500' };
  } else if (diffDays <= 3) {
    return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-orange-500' };
  } else if (diffDays <= 7) {
    return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-yellow-600' };
  } else if (diffDays <= 30) {
    return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-blue-500' };
  } else {
    return { days: diffDays, text: `剩 ${diffDays} 天`, display: `剩 ${diffDays} 天`, colorClass: 'text-green-500' };
  }
};

// 取得專案狀態樣式
const getTimelineStatus = (timeline) => {
  const { days } = getDaysRemaining(timeline.endDate);
  const progress = getTaskProgress(timeline);
  
  if (progress === 100) {
    return {
      label: '已完成',
      icon: '✅',
      bgClass: 'bg-green-100',
      textClass: 'text-green-600',
      badgeClass: 'bg-green-100 text-green-700',
      borderClass: 'border-green-200',
      barClass: 'bg-gradient-to-r from-green-400 to-green-500'
    };
  }
  
  if (days === null) {
    return {
      label: '進行中',
      icon: '📋',
      bgClass: 'bg-gray-100',
      textClass: 'text-gray-600',
      badgeClass: 'bg-gray-100 text-gray-600',
      borderClass: 'border-gray-200',
      barClass: 'bg-gradient-to-r from-gray-300 to-gray-400'
    };
  }
  
  if (days < 0) {
    return {
      label: '已過期',
      icon: '⚠️',
      bgClass: 'bg-red-100',
      textClass: 'text-red-600',
      badgeClass: 'bg-red-100 text-red-700',
      borderClass: 'border-red-200',
      barClass: 'bg-gradient-to-r from-red-400 to-red-500'
    };
  }
  
  if (days <= 3) {
    return {
      label: '緊急',
      icon: '🔥',
      bgClass: 'bg-orange-100',
      textClass: 'text-orange-600',
      badgeClass: 'bg-orange-100 text-orange-700',
      borderClass: 'border-orange-200',
      barClass: 'bg-gradient-to-r from-orange-400 to-orange-500'
    };
  }
  
  if (days <= 7) {
    return {
      label: '即將到期',
      icon: '⏰',
      bgClass: 'bg-yellow-100',
      textClass: 'text-yellow-600',
      badgeClass: 'bg-yellow-100 text-yellow-700',
      borderClass: 'border-yellow-200',
      barClass: 'bg-gradient-to-r from-yellow-400 to-yellow-500'
    };
  }
  
  return {
    label: '進行中',
    icon: '📋',
    bgClass: 'bg-blue-100',
    textClass: 'text-blue-600',
    badgeClass: 'bg-blue-100 text-blue-700',
    borderClass: 'border-blue-200',
    barClass: 'bg-gradient-to-r from-blue-400 to-blue-500'
  };
};

// 計算任務完成進度
const getTaskProgress = (timeline) => {
  if (!timeline.totalTasks || timeline.totalTasks === 0) return 0;
  return Math.round((timeline.completedTasks || 0) / timeline.totalTasks * 100);
};

// 計算時間進度（從開始到結束的百分比）
const getTimeProgress = (timeline) => {
  if (!timeline.startDate || !timeline.endDate) return 0;
  
  const today = new Date();
  const start = new Date(timeline.startDate);
  const end = new Date(timeline.endDate);
  
  if (today < start) return 0;
  if (today > end) return 100;
  
  const totalDuration = end - start;
  const elapsed = today - start;
  
  return Math.round((elapsed / totalDuration) * 100);
};

// 進度條顏色
const getProgressBarColor = (timeline) => {
  const progress = getTaskProgress(timeline);
  const status = getTimelineStatus(timeline);
  
  if (progress === 100) return 'bg-gradient-to-r from-green-400 to-green-500';
  if (status.label === '已過期') return 'bg-gradient-to-r from-red-400 to-red-500';
  if (status.label === '緊急') return 'bg-gradient-to-r from-orange-400 to-orange-500';
  return 'bg-gradient-to-r from-primary to-primary-light';
};

// 進度文字顏色
const getProgressTextColor = (timeline) => {
  const progress = getTaskProgress(timeline);
  if (progress === 100) return 'text-green-600';
  if (progress >= 50) return 'text-blue-600';
  return 'text-gray-600';
};

const timelineForm = ref({
  name: '',
  start_date: '',
  end_date: '',
  remark: ''
});

const taskForm = ref({
  name: '',
  assistant: '',
  start_date: '',
  end_date: '',
  task_remark: '',
  isWork: false,
  priority: 2,
  tags: ''
});

const resetTaskForm = () => {
  taskForm.value = {
    name: '',
    assistant: '',
    start_date: '',
    end_date: '',
    task_remark: '',
    isWork: false,
    priority: 2,
    tags: ''
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
      remark: timelineForm.value.remark || ''
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
    // 將 assistant 處理為逗號分隔的字串
    const assistantStr = taskForm.value.assistant 
      ? taskForm.value.assistant.trim()
      : '';
    
    // 處理標籤為逗號分隔的字串
    const tagsStr = taskForm.value.tags 
      ? taskForm.value.tags.trim()
      : '';
    
    const formData = {
      name: taskForm.value.name.trim(),
      assistant: assistantStr,
      timeline_id: selectedTimeline.value.id,
      start_date: taskForm.value.start_date || null,
      end_date: taskForm.value.end_date,
      task_remark: taskForm.value.task_remark || '',
      isWork: taskForm.value.isWork ? 1 : 0,
      priority: taskForm.value.priority || 2,
      tags: tagsStr
    };
    
    await api.post('/tasks', formData);
    alert('任務新增成功');
    showAddTaskModal.value = false;
    resetTaskForm();
    await viewTimeline(selectedTimeline.value);
    await fetchTimelines();
    await fetchAllTasks();
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
    remark: timeline.remark || ''
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
    await fetchAllTasks();
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
    remark: ''
  };
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('zh-TW');
};

onMounted(() => {
  fetchTimelines();
  fetchAllTasks();
});
</script>

<style>
/* FullCalendar 自訂樣式 */
.fc-custom {
  --fc-border-color: #e2e8f0;
  --fc-button-bg-color: #f8fafc;
  --fc-button-border-color: #e2e8f0;
  --fc-button-text-color: #475569;
  --fc-button-hover-bg-color: #f1f5f9;
  --fc-button-hover-border-color: #cbd5e1;
  --fc-button-active-bg-color: var(--color-primary);
  --fc-button-active-border-color: var(--color-primary);
  --fc-today-bg-color: rgba(59, 130, 246, 0.06);
  font-family: inherit;
}

.fc-custom .fc-toolbar {
  padding: 1rem 0;
  gap: 1rem;
}

.fc-custom .fc-toolbar-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: -0.025em;
}

.fc-custom .fc-button {
  padding: 0.625rem 1.25rem;
  font-size: 0.875rem;
  font-weight: 600;
  border-radius: 0.75rem;
  transition: all 0.2s ease;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}

.fc-custom .fc-button:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}

.fc-custom .fc-button:focus {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
  outline: none;
}

.fc-custom .fc-button-active {
  background: linear-gradient(135deg, var(--color-primary) 0%, #2563eb 100%) !important;
  border-color: transparent !important;
  color: white !important;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4) !important;
}

.fc-custom .fc-daygrid-day-number {
  padding: 0.625rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #475569;
}

.fc-custom .fc-daygrid-day.fc-day-today {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(99, 102, 241, 0.05) 100%) !important;
}

.fc-custom .fc-daygrid-day.fc-day-today .fc-daygrid-day-number {
  background: linear-gradient(135deg, var(--color-primary) 0%, #6366f1 100%);
  color: white;
  border-radius: 50%;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.fc-custom .fc-event {
  padding: 0.375rem 0.625rem;
  border-radius: 0.5rem;
  font-size: 0.8125rem;
  font-weight: 600;
  border: none;
  margin: 2px 4px 4px 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.08);
  cursor: pointer;
  transition: all 0.2s ease;
}

.fc-custom .fc-event:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.fc-custom .fc-event-main {
  padding: 0;
}

.fc-custom .fc-daygrid-event-dot {
  display: none;
}

.fc-custom .fc-col-header-cell {
  padding: 1rem 0;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  font-weight: 700;
  color: #64748b;
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;
}

.fc-custom .fc-scrollgrid {
  border-radius: 1rem;
  overflow: hidden;
  border: 1px solid #e2e8f0;
}

.fc-custom .fc-daygrid-day-frame {
  min-height: 110px;
  padding: 4px;
}

.fc-custom .fc-daygrid-day:hover {
  background-color: rgba(59, 130, 246, 0.02);
}

.fc-custom .fc-more-link {
  color: var(--color-primary);
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  background: rgba(59, 130, 246, 0.1);
  margin: 2px 4px;
  transition: all 0.2s;
}

.fc-custom .fc-more-link:hover {
  background: rgba(59, 130, 246, 0.2);
}

/* 年度視圖調整 */
.fc-custom .fc-multimonth {
  border: none;
}

.fc-custom .fc-multimonth-month {
  border: 1px solid #e2e8f0;
  border-radius: 1rem;
  margin: 0.75rem;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
}

.fc-custom .fc-multimonth-header {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 0.75rem;
}

.fc-custom .fc-multimonth-title {
  font-weight: 700;
  color: #334155;
}

/* Popover 樣式 */
.fc-custom .fc-popover {
  border-radius: 0.75rem;
  box-shadow: 0 10px 40px rgba(0,0,0,0.15);
  border: 1px solid #e2e8f0;
  overflow: hidden;
}

.fc-custom .fc-popover-header {
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 0.75rem 1rem;
  font-weight: 600;
}

/* ========== 看板拖拽樣式 ========== */
.kanban-ghost {
  opacity: 0.5;
  background: linear-gradient(135deg, #dbeafe 0%, #e0e7ff 100%) !important;
  border: 2px dashed #3b82f6 !important;
  border-radius: 0.75rem;
}

.kanban-drag {
  transform: rotate(3deg);
  box-shadow: 0 20px 40px rgba(0,0,0,0.2) !important;
  z-index: 1000;
}

.kanban-card {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.kanban-card:hover {
  border-color: #3b82f6 !important;
}

/* 拖拽時的視覺反饋 */
.sortable-chosen {
  cursor: grabbing !important;
}

/* 滑動動畫 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.kanban-card {
  animation: slideIn 0.3s ease-out;
}

/* 拖放區域高亮 */
.sortable-ghost-class {
  position: relative;
}

.sortable-ghost-class::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%);
  border-radius: 0.75rem;
  border: 2px dashed #3b82f6;
}
</style>
