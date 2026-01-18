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
    
    <!-- Calendar View -->
    <div v-if="viewMode === 'calendar'" class="px-4 pb-8">
      <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <!-- Calendar Legend -->
        <div class="p-4 border-b border-gray-100 bg-gray-50/50">
          <div class="flex flex-wrap items-center justify-between gap-4">
            <h3 class="font-semibold text-gray-700">📅 專案月曆</h3>
            <div class="flex flex-wrap items-center gap-3 text-xs">
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-green-500"></span> 已完成</span>
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-red-500"></span> 已過期</span>
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-orange-500"></span> 緊急</span>
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-yellow-500"></span> 即將到期</span>
              <span class="flex items-center gap-1"><span class="w-3 h-3 rounded-full bg-blue-500"></span> 進行中</span>
            </div>
          </div>
        </div>
        
        <!-- FullCalendar -->
        <div class="p-4">
          <FullCalendar 
            ref="calendarRef"
            :options="calendarOptions" 
            class="fc-custom"
          />
        </div>
      </div>
      
      <!-- Quick Stats Below Calendar -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
        <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h4 class="text-sm font-semibold text-gray-600 mb-3">📌 本週截止</h4>
          <div class="space-y-2 max-h-32 overflow-y-auto">
            <div 
              v-for="timeline in thisWeekTimelines" 
              :key="timeline.id"
              @click="viewTimeline(timeline)"
              class="flex items-center justify-between p-2 bg-orange-50 rounded-lg cursor-pointer hover:bg-orange-100 transition-colors"
            >
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs text-orange-600 font-medium">{{ getDaysRemaining(timeline.endDate).text }}</span>
            </div>
            <p v-if="thisWeekTimelines.length === 0" class="text-xs text-gray-400 text-center py-2">無專案</p>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h4 class="text-sm font-semibold text-gray-600 mb-3">🔥 已過期專案</h4>
          <div class="space-y-2 max-h-32 overflow-y-auto">
            <div 
              v-for="timeline in overdueTimelines" 
              :key="timeline.id"
              @click="viewTimeline(timeline)"
              class="flex items-center justify-between p-2 bg-red-50 rounded-lg cursor-pointer hover:bg-red-100 transition-colors"
            >
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs text-red-600 font-medium">{{ getDaysRemaining(timeline.endDate).text }}</span>
            </div>
            <p v-if="overdueTimelines.length === 0" class="text-xs text-gray-400 text-center py-2">無過期專案 👍</p>
          </div>
        </div>
        <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <h4 class="text-sm font-semibold text-gray-600 mb-3">✅ 近期完成</h4>
          <div class="space-y-2 max-h-32 overflow-y-auto">
            <div 
              v-for="timeline in completedTimelines" 
              :key="timeline.id"
              @click="viewTimeline(timeline)"
              class="flex items-center justify-between p-2 bg-green-50 rounded-lg cursor-pointer hover:bg-green-100 transition-colors"
            >
              <span class="text-sm font-medium text-gray-700 truncate">{{ timeline.name }}</span>
              <span class="text-xs text-green-600 font-medium">100%</span>
            </div>
            <p v-if="completedTimelines.length === 0" class="text-xs text-gray-400 text-center py-2">尚無完成專案</p>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Create/Edit Project Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div class="bg-white rounded-2xl shadow-2xl w-full max-w-lg animate-slideUp max-h-[90vh] overflow-y-auto">
        <div class="p-5 border-b border-gray-100 flex justify-between items-center bg-linear-to-r from-primary/5 to-transparent">
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
const viewMode = ref('card'); // 'card', 'timeline', or 'calendar'
const calendarRef = ref(null);

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
    // 添加 tooltip
    info.el.title = `${info.event.title}\n${info.event.extendedProps.status}\n${info.event.extendedProps.progress}% 完成`;
  },
  dayCellDidMount: (info) => {
    // 標記今天
    const today = new Date();
    if (info.date.toDateString() === today.toDateString()) {
      info.el.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
    }
  },
  eventDisplay: 'block',
  displayEventTime: false,
  eventClassNames: 'cursor-pointer'
}));

// 將專案轉換為日曆事件
const calendarEvents = computed(() => {
  return timelines.value.map(timeline => {
    const status = getTimelineStatus(timeline);
    const progress = getTaskProgress(timeline);
    
    // 根據狀態決定顏色
    let backgroundColor, borderColor;
    if (progress === 100) {
      backgroundColor = '#22c55e'; // green
      borderColor = '#16a34a';
    } else if (status.label === '已過期') {
      backgroundColor = '#ef4444'; // red
      borderColor = '#dc2626';
    } else if (status.label === '緊急') {
      backgroundColor = '#f97316'; // orange
      borderColor = '#ea580c';
    } else if (status.label === '即將到期') {
      backgroundColor = '#eab308'; // yellow
      borderColor = '#ca8a04';
    } else {
      backgroundColor = '#3b82f6'; // blue
      borderColor = '#2563eb';
    }
    
    return {
      id: timeline.id,
      title: `${status.icon} ${timeline.name}`,
      start: timeline.startDate || timeline.endDate,
      end: timeline.endDate ? addDays(timeline.endDate, 1) : null, // FullCalendar end is exclusive
      backgroundColor,
      borderColor,
      extendedProps: {
        timeline,
        status: status.label,
        progress
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
});
</script>

<style>
/* FullCalendar 自訂樣式 */
.fc-custom {
  --fc-border-color: #e5e7eb;
  --fc-button-bg-color: #f3f4f6;
  --fc-button-border-color: #e5e7eb;
  --fc-button-text-color: #374151;
  --fc-button-hover-bg-color: #e5e7eb;
  --fc-button-hover-border-color: #d1d5db;
  --fc-button-active-bg-color: var(--color-primary);
  --fc-button-active-border-color: var(--color-primary);
  --fc-today-bg-color: rgba(59, 130, 246, 0.08);
}

.fc-custom .fc-toolbar-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1f2937;
}

.fc-custom .fc-button {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
  font-weight: 500;
  border-radius: 0.5rem;
  transition: all 0.2s;
}

.fc-custom .fc-button:focus {
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
}

.fc-custom .fc-button-active {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  color: white !important;
}

.fc-custom .fc-daygrid-day-number {
  padding: 0.5rem;
  font-size: 0.875rem;
  color: #374151;
}

.fc-custom .fc-daygrid-day.fc-day-today .fc-daygrid-day-number {
  background-color: var(--color-primary);
  color: white;
  border-radius: 50%;
  width: 1.75rem;
  height: 1.75rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fc-custom .fc-event {
  padding: 0.25rem 0.5rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  border: none;
  margin-bottom: 2px;
}

.fc-custom .fc-event:hover {
  filter: brightness(0.95);
}

.fc-custom .fc-daygrid-event-dot {
  display: none;
}

.fc-custom .fc-col-header-cell {
  padding: 0.75rem 0;
  background-color: #f9fafb;
  font-weight: 600;
  color: #6b7280;
  font-size: 0.75rem;
  text-transform: uppercase;
}

.fc-custom .fc-scrollgrid {
  border-radius: 0.75rem;
  overflow: hidden;
}

.fc-custom .fc-daygrid-day-frame {
  min-height: 100px;
}

.fc-custom .fc-more-link {
  color: var(--color-primary);
  font-weight: 500;
}

/* 年度視圖調整 */
.fc-custom .fc-multimonth {
  border: none;
}

.fc-custom .fc-multimonth-month {
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  margin: 0.5rem;
  overflow: hidden;
}

.fc-custom .fc-multimonth-header {
  background-color: #f9fafb;
}
</style>
