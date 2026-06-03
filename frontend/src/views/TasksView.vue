<template>
  <div class="h-full w-full overflow-y-auto bg-slate-100/70 px-4 pt-6 pb-24 md:px-6 md:pb-6">
    <div class="mx-auto grid w-full max-w-6xl grid-cols-1 gap-6">
    <header
      class="overflow-hidden rounded-3xl border border-slate-200 bg-linear-to-br from-white via-slate-50 to-slate-100 shadow-[0_20px_40px_rgba(15,23,42,0.08)]"
    >
      <div class="relative px-5 py-5 md:px-6 md:py-6">
        <div class="pointer-events-none absolute -top-10 -right-10 h-28 w-28 rounded-full bg-primary/10 blur-2xl" />
        <div class="pointer-events-none absolute -bottom-10 -left-8 h-24 w-24 rounded-full bg-slate-300/30 blur-2xl" />
        <div class="relative">
          <p class="mb-2 inline-flex rounded-full border border-slate-200 bg-white px-2.5 py-1 text-[0.7rem] font-semibold tracking-[0.06em] text-slate-500">
            TASK OPERATIONS
          </p>
          <h1 class="text-[clamp(1.45rem,2.2vw,2rem)] font-black tracking-[0.01em] text-slate-900">任務管理</h1>
          <p class="mt-2 text-sm leading-6 text-slate-600">管理您的任務、附件、子任務與協作者。</p>
        </div>
      </div>
    </header>

    <!-- Header actions -->
    <div class="grid gap-3 lg:grid-cols-[1fr_auto] lg:items-end">
      <div class="grid grid-cols-2 gap-2 sm:grid-cols-4">
        <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
          <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">全部任務</p>
          <p class="text-xl font-extrabold text-slate-800">{{ taskSummary.total }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
          <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">進行中</p>
          <p class="text-xl font-extrabold text-slate-800">{{ taskSummary.active }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
          <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">已完成</p>
          <p class="text-xl font-extrabold text-slate-800">{{ taskSummary.completed }}</p>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2 shadow-sm">
          <p class="text-[0.72rem] tracking-[0.04em] text-slate-500">逾期</p>
          <p class="text-xl font-extrabold text-red-600">{{ taskSummary.overdue }}</p>
        </div>
      </div>
      <button
        @click="showForm = true"
        class="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)]"
      >
        新增任務
      </button>
    </div>

    <section class="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div class="grid gap-3 md:grid-cols-[1fr_180px_180px]">
        <input
          v-model.trim="taskQuery"
          type="text"
          placeholder="搜尋任務名稱 / 備註 / 成員 / 標籤"
          class="rounded-xl border border-slate-300 px-4 py-2.5 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
        />
        <select
          v-model="taskViewFilter"
          class="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
        >
          <option value="all">全部狀態</option>
          <option value="active">僅未完成</option>
          <option value="completed">僅已完成</option>
          <option value="overdue">僅逾期</option>
        </select>
        <select
          v-model="taskSort"
          class="rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
        >
          <option value="due_asc">截止日（近到遠）</option>
          <option value="due_desc">截止日（遠到近）</option>
          <option value="updated_desc">最近更新</option>
          <option value="priority_desc">優先級（高到低）</option>
        </select>
      </div>
      <p class="mt-2 text-xs text-slate-400">
        目前顯示 {{ filteredTasks.length }} / {{ tasks.length }} 筆任務
      </p>
    </section>

    <!-- Modal -->
    <Teleport to="body">
      <div
        v-if="showForm"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="cancelEdit"
      >
        <div class="mx-4 w-full max-w-lg rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-2 text-xl font-semibold text-slate-800">
              <span>{{ editingTask ? '編輯任務' : '新增任務' }}</span>
            </div>
            <button @click="cancelEdit" class="text-2xl leading-none text-slate-400 transition hover:text-slate-600">✕</button>
          </div>

          <form @submit.prevent="handleSubmit" class="space-y-4">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">任務名稱 *</label>
                <input
                  v-model="taskForm.name"
                  type="text"
                  placeholder="請輸入任務名稱"
                  class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                  required
                />
              </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">開始日期</label>
                <input
                  v-model="taskForm.start_date"
                  type="date"
                  class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                />
              </div>
              <div>
                <label class="mb-2 block text-sm font-semibold text-slate-600">截止日期 *</label>
                <input
                  v-model="taskForm.end_date"
                  type="date"
                  class="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
                  required
                />
              </div>
            </div>

            <div v-if="editingTask?.timeline_id">
              <label class="mb-2 block text-sm font-semibold text-slate-600">前置依賴任務（可多選）</label>
              <select
                v-model="taskForm.depends_on_task_ids"
                multiple
                class="min-h-30 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              >
                <option
                  v-for="candidate in dependencyCandidateTasks"
                  :key="`task-dependency-${candidate.task_id}`"
                  :value="candidate.task_id"
                >
                  {{ candidate.name }}
                </option>
              </select>
              <p class="mt-1.5 text-xs text-slate-500">僅限同專案任務，會在後端再次驗證。</p>
            </div>

            <div>
              <label class="mb-2 block text-sm font-semibold text-slate-600">備註</label>
              <textarea
                v-model="taskForm.task_remark"
                rows="3"
                placeholder="輸入任務備註..."
                class="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              ></textarea>
            </div>

            <div v-if="taskConflictPreview?.has_conflict" class="p-3 bg-amber-50 border border-amber-200 rounded-xl">
              <p class="text-sm font-semibold text-amber-700 mb-1">⚠️ 偵測到 {{ taskConflictPreview.conflict_count }} 個排程衝突</p>
              <div class="text-[11px] text-amber-700/90 space-y-1 mb-2">
                <p v-if="(taskConflictPreview.cross_project_conflict_count ?? 0) > 0">
                  跨專案衝突：{{ taskConflictPreview.cross_project_conflict_count }} 個
                </p>
                <p v-if="(taskConflictPreview.workload_overload_count ?? 0) > 0">
                  過載日：{{ taskConflictPreview.workload_overload_count }} 天
                </p>
              </div>
              <ul class="list-disc list-inside text-xs text-amber-700 space-y-1">
                <li v-for="item in taskConflictPreview.conflicts.slice(0, 3)" :key="`task-form-conflict-${item.task_id}`">
                  {{ item.name }}（{{ item.start_date }} ~ {{ item.end_date }}）
                </li>
              </ul>
              <div
                v-if="(taskConflictPreview.workload_overload_days ?? []).length > 0"
                class="mt-2.5 p-2.5 bg-white/70 border border-amber-200 rounded-lg"
              >
                <p class="text-xs font-semibold text-amber-700 mb-1.5">📅 過載日列表</p>
                <ul class="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                  <li
                    v-for="day in taskConflictPreview.workload_overload_days"
                    :key="`task-overload-${day.date}`"
                    class="text-xs text-amber-700"
                  >
                    <span class="font-medium">{{ formatDate(day.date) || day.date }}</span>
                    <span class="text-amber-600">：{{ day.projected_task_count }} 件（門檻 {{ day.threshold }}）</span>
                    <p v-if="day.sample_tasks.length" class="text-[11px] text-amber-600 mt-0.5 line-clamp-1">
                      既有任務：{{ day.sample_tasks.join('、') }}
                    </p>
                  </li>
                </ul>
              </div>
              <p v-if="taskConflictPreview.suggestion" class="text-xs text-amber-600 mt-2">
                建議改期：{{ taskConflictPreview.suggestion.start_date }} ~ {{ taskConflictPreview.suggestion.end_date }}
              </p>
              <p v-if="taskConflictPreview.ai_suggestion" class="text-xs text-amber-700 italic mt-2">
                💡 {{ taskConflictPreview.ai_suggestion }}
              </p>
            </div>

            <div class="flex gap-3">
              <button type="submit" class="rounded-xl bg-primary px-6 py-3 text-sm font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.25)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.32)]">
                <span>{{ editingTask ? '更新任務' : '新增任務' }}</span>
              </button>
              <button
                type="button"
                @click="cancelEdit"
                class="rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
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
        <div class="mx-4 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl">
          <div class="flex items-center justify-between mb-5">
            <div class="flex items-center gap-2 text-xl font-semibold text-slate-800">
              <span>成員管理 — {{ shareTask?.name }}</span>
            </div>
            <button @click="isSharePanelOpen = false" class="text-2xl leading-none text-slate-400 transition hover:text-slate-600">✕</button>
          </div>

          <!-- 現有成員列表 -->
          <div class="mb-4 space-y-2">
            <p class="mb-2 text-sm font-semibold text-slate-500">目前成員</p>
            <div
              v-for="member in taskMembers"
              :key="member.user_id"
              class="flex items-center justify-between gap-3 rounded-xl px-3 py-2 hover:bg-slate-50"
            >
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-sm">
                  {{ member.name?.charAt(0) || '?' }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ member.name }}</p>
                  <p class="text-xs text-slate-400">{{ member.email }}</p>
                </div>
              </div>
              <div class="flex items-center gap-2">
                <span
                  :class="member.role === 0 ? 'bg-primary/10 text-primary' : 'bg-slate-100 text-slate-500'"
                  class="text-xs px-2 py-0.5 rounded-full font-medium"
                >
                  {{ member.role === 0 ? '負責人' : '協作者' }}
                </span>
                <button
                  v-if="member.role !== 0"
                  @click="setTaskOwner(member)"
                  class="px-2 py-1 text-[11px] rounded-md bg-amber-100 text-amber-700 hover:bg-amber-200 transition-colors"
                  title="設為主責人"
                >主責</button>
                <button
                  v-if="member.role !== 0"
                  @click="kickTaskMember(member)"
                  class="text-lg leading-none text-slate-300 transition-colors hover:text-red-500"
                  title="移除成員"
                >✕</button>
              </div>
            </div>
          </div>

          <!-- 專案成員快速指派 -->
          <div v-if="shareTask?.timeline_id" class="mb-4">
            <p class="mb-2 text-sm font-semibold text-slate-500">專案成員（快速指派）</p>
            <div class="space-y-1">
              <p v-if="timelineMembers.length === 0" class="py-2 text-center text-xs text-slate-400">載入中...</p>
              <template v-else-if="timelineMembers.filter(m => !taskMembers.some(tm => tm.user_id === m.user_id)).length">
                <div
                  v-for="m in timelineMembers.filter(m => !taskMembers.some(tm => tm.user_id === m.user_id))"
                  :key="m.user_id"
                  class="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"
                >
                  <div class="flex items-center gap-3">
                    <div class="w-8 h-8 rounded-full bg-indigo-100 text-indigo-600 font-bold flex items-center justify-center text-sm">
                      {{ m.name?.charAt(0) || '?' }}
                    </div>
                    <div>
                      <p class="text-sm font-semibold text-slate-800">{{ m.name }}</p>
                      <p class="text-xs text-slate-400">{{ m.email }}</p>
                    </div>
                  </div>
                  <button
                    @click="quickAssignMember(m)"
                    class="px-3 py-1 bg-primary text-white font-medium rounded-lg text-xs hover:brightness-110 transition-colors"
                  >指派</button>
                </div>
              </template>
              <p v-else class="py-1 text-center text-xs text-slate-400">所有專案成員已加入此任務</p>
            </div>
          </div>

          <!-- 邀請新成員 -->
          <div class="border-t border-slate-200 pt-4">
            <p class="mb-3 text-sm font-semibold text-slate-500">以 Email 邀請協作者</p>
            <div class="flex gap-2">
              <input
                v-model="shareInputEmail"
                type="email"
                placeholder="輸入 Email 搜尋使用者"
                @keyup.enter="searchShareUser"
                class="flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20"
              />
              <button
                @click="searchShareUser"
                class="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
              >搜尋</button>
            </div>
            <p v-if="shareSearchError" class="mt-2 text-xs text-red-500">{{ shareSearchError }}</p>

            <!-- 搜尋結果 -->
            <div v-if="shareSearchResult" class="mt-3 flex items-center justify-between gap-3 rounded-xl bg-slate-50 p-3">
              <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full bg-primary/20 text-primary font-bold flex items-center justify-center text-sm">
                  {{ shareSearchResult.name?.charAt(0) || '?' }}
                </div>
                <div>
                  <p class="text-sm font-semibold text-slate-800">{{ shareSearchResult.name }}</p>
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
      <div v-if="filteredTasks.length === 0" class="rounded-3xl border border-dashed border-slate-300 bg-white py-16 text-center shadow-sm">
        <p class="text-xl font-semibold text-slate-700">找不到符合條件的任務</p>
        <p class="mt-1 text-sm text-slate-500">調整搜尋關鍵字或篩選條件試試。</p>
      </div>

      <div v-else class="space-y-6">
        <section
          v-for="section in taskSections"
          :key="section.key"
          v-show="section.items.length > 0"
        >
          <div class="mb-2 flex items-center justify-between">
            <h2 class="text-sm font-semibold tracking-[0.04em] text-slate-600">{{ section.title }}</h2>
            <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-600">{{ section.items.length }}</span>
          </div>

          <div class="space-y-3">
            <article
              v-for="task in section.items"
              :key="task.task_id"
              class="rounded-2xl border border-slate-200 bg-white p-5 shadow-[0_12px_26px_rgba(15,23,42,0.06)] transition hover:-translate-y-px hover:shadow-[0_16px_30px_rgba(15,23,42,0.08)]"
              :class="{ 'opacity-80 bg-slate-50': task.completed }"
            >
              <div class="flex flex-wrap items-start justify-between gap-3">
                <div class="min-w-0 flex-1">
                  <div class="mb-2 flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      @click="openTaskDetail(task)"
                      class="truncate text-left text-lg font-bold text-slate-800 transition hover:text-primary hover:underline"
                    >
                      {{ task.name }}
                    </button>
                    <span :class="getPriorityBadgeClass(task.priority)" class="rounded-full px-2 py-0.5 text-xs font-semibold">
                      {{ getPriorityLabel(task.priority) }}
                    </span>
                    <span :class="getStatusBadgeClass(task.status, task.completed)" class="rounded-full px-2 py-0.5 text-xs font-semibold">
                      {{ getStatusLabel(task.status, task.completed) }}
                    </span>
                    <span
                      v-if="isTaskOverdue(task)"
                      class="rounded-full bg-red-100 px-2 py-0.5 text-xs font-semibold text-red-600"
                    >
                      已逾期
                    </span>
                  </div>

                  <div class="flex flex-wrap items-center gap-3 text-xs text-slate-500">
                    <span>截止：{{ task.end_date ? formatDate(task.end_date) : '未設定' }}</span>
                    <span v-if="task.timeline_id">專案任務</span>
                    <span v-if="task.members?.length">成員 {{ task.members.length }} 人</span>
                    <span v-if="(task.depends_on_task_ids || []).length">依賴 {{ task.depends_on_task_ids?.length }} 項</span>
                  </div>

                  <p v-if="task.task_remark" class="mt-2 line-clamp-2 text-sm text-slate-500">{{ task.task_remark }}</p>
                </div>

                <div class="flex shrink-0 flex-wrap items-center gap-2">
                  <button
                    @click="toggleTask(task)"
                    :class="task.completed ? 'bg-amber-500 hover:bg-amber-600' : 'bg-emerald-500 hover:bg-emerald-600'"
                    class="rounded-lg px-3 py-1.5 text-xs font-semibold text-white transition-colors"
                  >
                    {{ task.completed ? '改未完成' : '完成' }}
                  </button>
                  <button
                    @click="openTaskDetail(task)"
                    class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    詳情
                  </button>
                  <button
                    v-if="task.is_owner || task.timeline_id"
                    @click="openSharePanel(task)"
                    class="rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-100"
                  >
                    成員
                  </button>
                  <button
                    @click="editTask(task)"
                    class="rounded-lg border border-sky-200 bg-sky-50 px-3 py-1.5 text-xs font-semibold text-sky-700 transition hover:bg-sky-100"
                  >
                    編輯
                  </button>
                  <button
                    @click="deleteTask(task.task_id)"
                    class="rounded-lg border border-red-200 bg-white px-3 py-1.5 text-xs font-semibold text-red-600 transition hover:bg-red-50"
                  >
                    刪除
                  </button>
                </div>
              </div>
            </article>
          </div>
        </section>
      </div>
    </div>

    <!-- 任務詳情 Modal -->
    <Teleport to="body">
      <div
        v-if="showTaskDetail && detailTask"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        @click.self="showTaskDetail = false"
      >
        <div class="mx-4 max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl">
          <!-- Header -->
          <div class="sticky top-0 z-10 flex items-center justify-between border-b border-slate-200 bg-white/95 p-5 backdrop-blur-sm">
            <h2 class="flex items-center gap-2 text-lg font-semibold text-slate-800">
              <span class="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">📌</span>
              {{ detailTask.name }}
            </h2>
            <button @click="showTaskDetail = false" class="flex h-8 w-8 items-center justify-center rounded-xl text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600">&times;</button>
          </div>
          <div class="p-6 space-y-6">
            <!-- 基本資訊 -->
            <div class="grid grid-cols-2 gap-4 rounded-xl bg-slate-50 p-4">
              <div><p class="mb-1 text-xs text-slate-500">開始日期</p><p class="font-medium text-slate-800">{{ formatDate(detailTask.start_date) || '未設定' }}</p></div>
              <div><p class="mb-1 text-xs text-slate-500">截止日期</p><p class="font-medium text-slate-800">{{ formatDate(detailTask.end_date) || '未設定' }}</p></div>
            </div>
            <div v-if="detailTask.task_remark" class="rounded-xl bg-amber-50 p-4">
              <h4 class="mb-2 font-semibold text-slate-700">📝 備註</h4>
              <p class="text-sm text-slate-600">{{ detailTask.task_remark }}</p>
            </div>
            <div v-if="(detailTask.depends_on_task_ids || []).length" class="rounded-xl bg-slate-50 p-4">
              <h4 class="mb-2 font-semibold text-slate-700">🔗 前置依賴</h4>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="dependencyId in detailTask.depends_on_task_ids"
                  :key="`task-detail-dependency-${dependencyId}`"
                  class="px-2.5 py-1 text-xs rounded-full bg-slate-200 text-slate-700"
                >
                  {{ getTaskNameById(dependencyId) }}
                </span>
              </div>
            </div>

            <!-- ── 子任務區 ── -->
            <div>
              <h4 class="mb-3 flex items-center gap-2 font-semibold text-slate-700">
                <span>📋</span> 子任務
                <span class="text-sm font-normal text-slate-500">({{ detailSubtasks.filter(s => s.completed).length }}/{{ detailSubtasks.length }})</span>
              </h4>
              <div v-if="detailSubtasks.length > 0" class="mb-4 h-2 overflow-hidden rounded-full bg-slate-200">
                <div class="h-full bg-primary rounded-full transition-all duration-300" :style="{ width: detailSubtaskProgress + '%' }"></div>
              </div>
              <div class="mb-3 space-y-2">
                <div v-for="subtask in detailSubtasks" :key="subtask.id" class="group flex items-center gap-3 rounded-lg bg-slate-50 p-3 transition-colors hover:bg-slate-100">
                  <input type="checkbox" :checked="subtask.completed" @change="toggleDetailSubtask(subtask)" class="h-5 w-5 cursor-pointer rounded border-slate-300 text-primary focus:ring-primary" />
                  <span :class="['flex-1 text-sm', subtask.completed ? 'line-through text-slate-400' : 'text-slate-700']">{{ subtask.name }}</span>
                  <button @click="deleteDetailSubtask(subtask)" class="opacity-0 group-hover:opacity-100 text-red-400 hover:text-red-600 transition-all">🗑️</button>
                </div>
                <div v-if="detailSubtasks.length === 0" class="py-4 text-center text-sm text-slate-400">尚無子任務</div>
              </div>
              <div class="flex gap-2">
                <input v-model="detailNewSubtask" type="text" placeholder="輸入子任務名稱..." @keyup.enter="addDetailSubtask" class="flex-1 rounded-xl border border-slate-300 px-4 py-2 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20" />
                <button @click="addDetailSubtask" class="px-4 py-2 bg-primary text-white rounded-xl hover:brightness-110 transition-all">新增</button>
              </div>
            </div>

            <!-- ── 附件區 ── -->
            <div>
              <div class="flex items-center justify-between mb-3">
                <h4 class="flex items-center gap-2 font-semibold text-slate-700">
                  <span>📎</span> 附件
                  <span class="text-xs font-normal text-slate-400">({{ detailFiles.length }})</span>
                </h4>
                <label class="cursor-pointer flex items-center gap-1.5 px-3 py-1.5 bg-primary/10 text-primary text-sm font-medium rounded-lg hover:bg-primary/20 transition-colors">
                  <span>＋</span> 上傳檔案
                  <input ref="detailFileInput" type="file" class="hidden"
                    accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.csv,.mp4,.mov"
                    @change="handleDetailFileUpload" />
                </label>
              </div>
              <div v-if="detailFiles.length === 0" class="rounded-xl border border-dashed border-slate-300 bg-slate-50 py-6 text-center text-sm text-slate-400">
                尚無附件，點擊「上傳檔案」新增
              </div>
              <div v-else class="space-y-2">
                <div v-for="file in detailFiles" :key="file.id"
                  class="group flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 transition-colors hover:bg-slate-100">
                  <img v-if="isImageFile(file.original_filename)"
                    :src="`${apiBase}/tasks/files/${file.filename}`"
                    class="h-12 w-12 shrink-0 rounded-lg border border-slate-200 object-cover"
                    :alt="file.original_filename" />
                  <span v-else class="text-3xl shrink-0">{{ getFileIcon(file.original_filename) }}</span>
                  <div class="flex-1 min-w-0">
                    <p class="truncate text-sm font-medium text-slate-700">{{ file.original_filename }}</p>
                    <p class="text-xs text-slate-400">{{ formatFileSize(file.file_size) }} · {{ formatDateTime(file.uploaded_at) }}</p>
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
              <div class="mb-4 flex items-center justify-between gap-3">
                <h4 class="flex items-center gap-2 font-semibold text-slate-700">
                  <span>💬</span> 留言
                  <span class="text-xs font-normal text-slate-400">({{ detailComments.length }})</span>
                </h4>
                <button
                  @click="summarizeDetailComments"
                  :disabled="isSummarizingDetailComments"
                  class="px-3 py-1.5 bg-violet-100 text-violet-700 text-xs font-semibold rounded-lg hover:bg-violet-200 transition-colors disabled:opacity-50"
                >
                  {{ isSummarizingDetailComments ? '摘要中...' : '🤖 AI 摘要' }}
                </button>
              </div>

              <div v-if="detailCommentSummary" class="mb-4 space-y-3 rounded-xl border border-violet-100 bg-violet-50 p-4 text-sm text-slate-700">
                <div>
                  <p class="font-semibold text-violet-800 mb-1">決議</p>
                  <ul v-if="detailCommentSummary.decisions.length" class="list-disc list-inside space-y-1">
                    <li v-for="(item, idx) in detailCommentSummary.decisions" :key="`dd-${idx}`">{{ item }}</li>
                  </ul>
                  <p v-else class="text-slate-400">暫無</p>
                </div>
                <div>
                  <p class="font-semibold text-violet-800 mb-1">風險</p>
                  <ul v-if="detailCommentSummary.risks.length" class="list-disc list-inside space-y-1">
                    <li v-for="(item, idx) in detailCommentSummary.risks" :key="`dr-${idx}`">{{ item }}</li>
                  </ul>
                  <p v-else class="text-slate-400">暫無</p>
                </div>
                <div>
                  <p class="font-semibold text-violet-800 mb-1">下一步</p>
                  <ul v-if="detailCommentSummary.next_actions.length" class="list-disc list-inside space-y-1">
                    <li v-for="(item, idx) in detailCommentSummary.next_actions" :key="`dn-${idx}`">{{ item }}</li>
                  </ul>
                  <p v-else class="text-slate-400">暫無</p>
                </div>
                <p v-if="detailCommentSummaryMeta?.truncated" class="text-xs text-violet-600">
                  已自動截斷較舊留言，摘要以最近 {{ detailCommentSummaryMeta.used_comments }} / {{ detailCommentSummaryMeta.total_comments }} 筆為主。
                </p>
              </div>

              <div class="mb-4 max-h-60 space-y-3 overflow-y-auto">
                <div v-for="comment in detailComments" :key="comment.comment_id" class="group flex gap-3 rounded-xl bg-slate-50 p-3">
                  <div class="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center text-sm font-bold text-primary shrink-0">
                    {{ comment.user_name?.charAt(0)?.toUpperCase() }}
                  </div>
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <span class="text-sm font-medium text-slate-700">{{ comment.user_name }}</span>
                      <span class="text-xs text-slate-400">{{ formatDateTime(comment.created_at) }}</span>
                    </div>
                    <p class="text-sm text-slate-600">{{ comment.task_message }}</p>
                  </div>
                  <button @click="deleteDetailComment(comment.comment_id)"
                    class="h-7 w-7 shrink-0 opacity-0 transition-all group-hover:opacity-100 flex items-center justify-center rounded-lg text-slate-300 hover:bg-red-50 hover:text-red-500"
                    title="刪除留言">✕</button>
                </div>
                <div v-if="detailComments.length === 0" class="py-4 text-center text-sm text-slate-400">尚無留言</div>
              </div>
              <div class="flex gap-2">
                <input v-model="detailNewComment" type="text" placeholder="新增留言..." @keyup.enter="addDetailComment"
                  class="flex-1 rounded-xl border border-slate-300 px-4 py-2.5 outline-none transition focus:border-slate-500 focus:ring-2 focus:ring-slate-400/20" />
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

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { toast } from 'vue-sonner';
import { storeToRefs } from 'pinia';
import { useTaskStore } from '../stores/tasks';
import { taskService } from '../services/taskService';
import { timelineService } from '../services/timelineService';
import { formatDate, formatDateTime, formatFileSize, isImageFile, getFileIcon } from '../utils/formatters';
import { getApiErrorMessage } from '../utils/apiError';
import { downloadFileFromUrl, loadTaskDetailResources } from '../utils/taskDetails';
import { useConfirm } from '../composables/useConfirm';
import type { Task, TaskComment, TaskCommentSummary, TaskFile, Subtask, TaskMember, SearchUserResult, ResourceConflictResponse } from '../types';

const { confirm } = useConfirm();

const store = useTaskStore();
const { tasks } = storeToRefs(store);
const route = useRoute();
const router = useRouter();

// 檔案下載基礎 URL（僅用於 <img> src 與下載連結）
const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api';

// ── 新增/編輯任務 ──
const showForm = ref(false);
const editingTask = ref<Task | null>(null);
const taskForm = ref({
  name: '',
  start_date: '',
  end_date: '',
  task_remark: '',
  depends_on_task_ids: [] as number[],
});
const taskConflictPreview = ref<ResourceConflictResponse | null>(null);
const taskQuery = ref('');
const taskViewFilter = ref<'all' | 'active' | 'completed' | 'overdue'>('all');
const taskSort = ref<'due_asc' | 'due_desc' | 'updated_desc' | 'priority_desc'>('due_asc');

const toTimestamp = (value?: string | null): number | null => {
  if (!value) return null;
  const parsed = new Date(value).getTime();
  if (Number.isNaN(parsed)) return null;
  return parsed;
};

const isTaskOverdue = (task: Task): boolean => {
  if (task.completed || !task.end_date) return false;
  const due = toTimestamp(task.end_date);
  if (due === null) return false;
  return due < Date.now();
};

const getPriorityLabel = (priority: number): string => {
  if (priority === 1) return '高優先';
  if (priority === 2) return '中優先';
  return '低優先';
};

const getPriorityBadgeClass = (priority: number): string => {
  if (priority === 1) return 'bg-red-100 text-red-700';
  if (priority === 2) return 'bg-amber-100 text-amber-700';
  return 'bg-emerald-100 text-emerald-700';
};

const getStatusLabel = (status: Task['status'], completed: boolean): string => {
  if (completed) return '已完成';
  if (status === 'in_progress') return '進行中';
  if (status === 'review') return '審核中';
  if (status === 'cancelled') return '已取消';
  return '待辦';
};

const getStatusBadgeClass = (status: Task['status'], completed: boolean): string => {
  if (completed) return 'bg-emerald-100 text-emerald-700';
  if (status === 'in_progress') return 'bg-sky-100 text-sky-700';
  if (status === 'review') return 'bg-violet-100 text-violet-700';
  if (status === 'cancelled') return 'bg-slate-200 text-slate-600';
  return 'bg-slate-100 text-slate-700';
};

const taskSummary = computed(() => {
  const total = tasks.value.length;
  const completed = tasks.value.filter((task) => task.completed).length;
  const active = total - completed;
  const overdue = tasks.value.filter((task) => isTaskOverdue(task)).length;
  return { total, completed, active, overdue };
});

const filteredTasks = computed(() => {
  const query = taskQuery.value.trim().toLowerCase();

  return tasks.value.filter((task) => {
    if (taskViewFilter.value === 'active' && task.completed) return false;
    if (taskViewFilter.value === 'completed' && !task.completed) return false;
    if (taskViewFilter.value === 'overdue' && !isTaskOverdue(task)) return false;

    if (!query) return true;

    const memberText = (task.members || [])
      .map((member) => `${member.name} ${member.email} ${member.username ?? ''}`)
      .join(' ');

    const haystack = `${task.name} ${task.task_remark ?? ''} ${task.tags ?? ''} ${memberText}`.toLowerCase();
    return haystack.includes(query);
  });
});

const sortedTasks = computed(() => {
  const cloned = [...filteredTasks.value];

  cloned.sort((a, b) => {
    if (taskSort.value === 'due_asc') {
      const aDue = toTimestamp(a.end_date) ?? Number.MAX_SAFE_INTEGER;
      const bDue = toTimestamp(b.end_date) ?? Number.MAX_SAFE_INTEGER;
      return aDue - bDue;
    }

    if (taskSort.value === 'due_desc') {
      const aDue = toTimestamp(a.end_date) ?? Number.MIN_SAFE_INTEGER;
      const bDue = toTimestamp(b.end_date) ?? Number.MIN_SAFE_INTEGER;
      return bDue - aDue;
    }

    if (taskSort.value === 'updated_desc') {
      const aUpdated = toTimestamp(a.updated_at) ?? toTimestamp(a.created_at) ?? 0;
      const bUpdated = toTimestamp(b.updated_at) ?? toTimestamp(b.created_at) ?? 0;
      return bUpdated - aUpdated;
    }

    const aPriority = Number.isFinite(a.priority) ? a.priority : 99;
    const bPriority = Number.isFinite(b.priority) ? b.priority : 99;
    return aPriority - bPriority;
  });

  return cloned;
});

const taskSections = computed(() => {
  if (taskViewFilter.value === 'all') {
    const activeItems = sortedTasks.value.filter((task) => !task.completed);
    const completedItems = sortedTasks.value.filter((task) => task.completed);
    return [
      { key: 'active', title: '未完成任務', items: activeItems },
      { key: 'completed', title: '已完成任務', items: completedItems },
    ];
  }

  return [
    { key: 'filtered', title: '任務清單', items: sortedTasks.value },
  ];
});

const normalizeIdList = (values: Array<number | string>): number[] => {
  return Array.from(
    new Set(
      values
        .map((value) => Number(value))
        .filter((value) => Number.isInteger(value) && value > 0)
    )
  );
};

const dependencyCandidateTasks = computed(() => {
  if (!editingTask.value?.timeline_id) return [];

  return tasks.value.filter((task) => {
    if (task.timeline_id !== editingTask.value?.timeline_id) return false;
    return task.task_id !== editingTask.value?.task_id;
  });
});

const getTaskNameById = (taskId: number): string => {
  const matchedTask = tasks.value.find((task) => task.task_id === taskId);
  return matchedTask?.name || `任務 #${taskId}`;
};

const toDateOnly = (value?: string | null): string | null => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toISOString().split('T')[0];
};

const runConflictPrecheckForSubmit = async (): Promise<boolean> => {
  if (!editingTask.value?.timeline_id) {
    taskConflictPreview.value = null;
    return true;
  }

  if (!taskForm.value.end_date) {
    taskConflictPreview.value = null;
    return true;
  }

  const timelineId = editingTask.value.timeline_id;

  try {
    const res = await timelineService.conflictCheck(timelineId, {
      task_id: editingTask.value.task_id,
      name: taskForm.value.name,
      start_date: taskForm.value.start_date || null,
      end_date: taskForm.value.end_date || null,
      include_ai_suggestion: false,
    });
    taskConflictPreview.value = res.data;

    if (!res.data.has_conflict) {
      return true;
    }

    const lines = res.data.conflicts
      .slice(0, 3)
      .map((item) => `• ${item.name}（${item.start_date} ~ ${item.end_date}）`)
      .join('\n');

    const suggestion = res.data.suggestion
      ? `\n\n建議改期：${res.data.suggestion.start_date} ~ ${res.data.suggestion.end_date}`
      : '';

    return await confirm({
      title: `偵測到 ${res.data.conflict_count} 個衝突，仍要儲存？`,
      message: `${lines}${suggestion}`,
    });
  } catch (error: unknown) {
    toast.error(getApiErrorMessage(error, '衝突檢查失敗'));
    return false;
  }
};

const runConflictPrecheckForMemberAssignment = async (
  task: Task,
  member: Pick<TaskMember, 'user_id' | 'name'>
): Promise<boolean> => {
  if (!task.timeline_id) {
    return true;
  }

  const endDate = toDateOnly(task.end_date);
  if (!endDate) {
    return true;
  }

  try {
    const res = await timelineService.conflictCheck(task.timeline_id, {
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

    const message = [
      `日期衝突：${res.data.conflicts.length} 個`,
      `跨專案衝突：${res.data.cross_project_conflict_count ?? 0} 個`,
      `過載日：${res.data.workload_overload_count ?? 0} 天`,
    ].join('\n');

    const suggestion = res.data.suggestion
      ? `\n\n建議改期：${res.data.suggestion.start_date} ~ ${res.data.suggestion.end_date}`
      : '';

    return await confirm({
      title: `指派給 ${member.name} 前偵測到衝突，仍要指派？`,
      message: `${message}${suggestion}`,
    });
  } catch (error: unknown) {
    toast.error(getApiErrorMessage(error, '檢查衝突失敗'));
    return false;
  }
};

const handleSubmit = async () => {
  try {
    const canProceed = await runConflictPrecheckForSubmit();
    if (!canProceed) {
      return;
    }

    const payload = {
      ...taskForm.value,
      depends_on_task_ids: normalizeIdList(taskForm.value.depends_on_task_ids),
    };

    if (editingTask.value) {
      await store.updateTask(editingTask.value.task_id, payload);
    } else {
      await store.addTask(payload);
    }
    resetForm();
  } catch (error) {
    console.error('儲存任務失敗:', error);
  }
};

const editTask = (task: Task) => {
  editingTask.value = task;
  taskConflictPreview.value = null;
  taskForm.value = {
    name: task.name,
    start_date: task.start_date ? task.start_date.slice(0, 10) : '',
    end_date: task.end_date ? task.end_date.slice(0, 10) : '',
    task_remark: task.task_remark || '',
    depends_on_task_ids: normalizeIdList(task.depends_on_task_ids || []),
  };
  showForm.value = true;
};

const cancelEdit = () => { resetForm(); };

const deleteTask = async (taskId: number) => {
  if (!await confirm({ title: '確定要刪除此任務？', danger: true })) return;
  try {
    await store.removeTask(taskId);
  } catch (error) {
    console.error('刪除任務失敗:', error);
  }
};

const toggleTask = async (task: Task) => {
  try {
    await store.toggleTask(task.task_id);
  } catch (error) {
    console.error('更新任務狀態失敗:', error);
  }
};

const resetForm = () => {
  editingTask.value = null;
  showForm.value = false;
  taskConflictPreview.value = null;
  taskForm.value = { name: '', start_date: '', end_date: '', task_remark: '', depends_on_task_ids: [] };
};

// ── 任務詳情 Modal ──
const showTaskDetail = ref(false);
const detailTask = ref<Task | null>(null);
const detailComments = ref<TaskComment[]>([]);
const detailCommentSummary = ref<TaskCommentSummary | null>(null);
const detailCommentSummaryMeta = ref<{ total_comments?: number; used_comments?: number; truncated?: boolean } | null>(null);
const isSummarizingDetailComments = ref(false);
const detailFiles = ref<TaskFile[]>([]);
const detailNewComment = ref('');
const detailFileInput = ref<HTMLInputElement | null>(null);
const detailSubtasks = ref<Subtask[]>([]);
const detailNewSubtask = ref('');

const detailSubtaskProgress = computed(() => {
  if (!detailSubtasks.value.length) return 0;
  return Math.round(detailSubtasks.value.filter(s => s.completed).length / detailSubtasks.value.length * 100);
});

const openTaskDetail = async (task: Task) => {
  detailTask.value = { ...task };
  detailComments.value = [];
  detailCommentSummary.value = null;
  detailCommentSummaryMeta.value = null;
  detailFiles.value = [];
  detailSubtasks.value = [];
  showTaskDetail.value = true;
  await router.replace({ query: { ...route.query, task_id: String(task.task_id) } });
  try {
    const resources = await loadTaskDetailResources(task.task_id);
    detailComments.value = resources.comments;
    detailFiles.value = resources.files;
    detailSubtasks.value = resources.subtasks;
  } catch (err) {
    console.error('取得任務詳情失敗:', err);
  }
};

watch(showTaskDetail, (opened) => {
  if (!opened) {
    const nextQuery = { ...route.query };
    delete nextQuery.task_id;
    void router.replace({ query: nextQuery });
  }
});

const addDetailSubtask = async () => {
  if (!detailNewSubtask.value.trim() || !detailTask.value) return;
  try {
    await taskService.createSubtask(detailTask.value.task_id, { name: detailNewSubtask.value.trim() });
    detailNewSubtask.value = '';
    const res = await taskService.getSubtasks(detailTask.value.task_id);
    detailSubtasks.value = res.data || [];
  } catch { toast.error('新增子任務失敗'); }
};

const toggleDetailSubtask = async (subtask: Subtask) => {
  if (!detailTask.value) return;
  try {
    await taskService.toggleSubtask(detailTask.value.task_id, subtask.id);
    const res = await taskService.getSubtasks(detailTask.value.task_id);
    detailSubtasks.value = res.data || [];
  } catch { toast.error('更新子任務狀態失敗'); }
};

const deleteDetailSubtask = async (subtask: Subtask) => {
  if (!detailTask.value) return;
  if (!await confirm({ title: '確定要刪除此子任務？', danger: true })) return;
  try {
    await taskService.deleteSubtask(detailTask.value.task_id, subtask.id);
    detailSubtasks.value = detailSubtasks.value.filter(s => s.id !== subtask.id);
  } catch { toast.error('刪除子任務失敗'); }
};

const addDetailComment = async () => {
  if (!detailNewComment.value.trim() || !detailTask.value) return;
  try {
    await taskService.addComment(detailTask.value.task_id, detailNewComment.value.trim());
    detailNewComment.value = '';
    const res = await taskService.getComments(detailTask.value.task_id);
    detailComments.value = res.data || [];
    detailCommentSummary.value = null;
    detailCommentSummaryMeta.value = null;
  } catch { toast.error('新增留言失敗'); }
};

const deleteDetailComment = async (commentId: number) => {
  if (!detailTask.value) return;
  if (!await confirm({ title: '確定要刪除此留言？', danger: true })) return;
  try {
    await taskService.deleteComment(detailTask.value.task_id, commentId);
    detailComments.value = detailComments.value.filter(c => c.comment_id !== commentId);
    detailCommentSummary.value = null;
    detailCommentSummaryMeta.value = null;
  } catch { toast.error('刪除留言失敗'); }
};

const summarizeDetailComments = async () => {
  if (!detailTask.value) return;
  isSummarizingDetailComments.value = true;
  try {
    const res = await taskService.summarizeComments(detailTask.value.task_id);
    detailCommentSummary.value = res.data.summary;
    detailCommentSummaryMeta.value = res.data.meta;
    if (res.data.message) {
      toast.info(res.data.message);
    } else {
      toast.success('AI 摘要完成');
    }
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, 'AI 摘要失敗'));
  } finally {
    isSummarizingDetailComments.value = false;
  }
};

const handleDetailFileUpload = async (event: Event) => {
  const target = event.target as HTMLInputElement | null;
  const file = target?.files?.[0];
  if (!file || !detailTask.value) return;
  if (file.size > 10 * 1024 * 1024) { toast.warning('檔案大小不可超過 10MB'); return; }
  const formData = new FormData();
  formData.append('file', file);
  try {
    await taskService.uploadFile(detailTask.value.task_id, formData);
    const res = await taskService.getFiles(detailTask.value.task_id);
    detailFiles.value = res.data || [];
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '上傳失敗'));
  } finally {
    if (detailFileInput.value) detailFileInput.value.value = '';
  }
};

const deleteDetailFile = async (fileId: number) => {
  if (!detailTask.value) return;
  if (!await confirm({ title: '確定要刪除此附件？', danger: true })) return;
  try {
    await taskService.deleteFile(detailTask.value.task_id, fileId);
    detailFiles.value = detailFiles.value.filter(f => f.id !== fileId);
  } catch { toast.error('刪除附件失敗'); }
};

// ── 成員管理 ──
const shareTask = ref<Task | null>(null);
const isSharePanelOpen = ref(false);
const taskMembers = ref<TaskMember[]>([]);
const timelineMembers = ref<TaskMember[]>([]);
const shareInputEmail = ref('');
const shareSearchResult = ref<SearchUserResult | null>(null);
const shareSearchError = ref('');

const openSharePanel = async (task: Task) => {
  shareTask.value = task;
  isSharePanelOpen.value = true;
};

watch(isSharePanelOpen, async (val: boolean) => {
  if (val && shareTask.value) {
    await loadTaskMembers();
    // 若任務屬於某 timeline，也載入該 timeline 的成員供快速指派
    if (shareTask.value.timeline_id) {
      try {
        const res = await timelineService.getMembers(shareTask.value.timeline_id);
        timelineMembers.value = res.data || [];
      } catch (e: unknown) {
        console.error('載入專案成員失敗', e);
        timelineMembers.value = [];
      }
    } else {
      timelineMembers.value = [];
    }
  } else {
    shareInputEmail.value = '';
    shareSearchResult.value = null;
    shareSearchError.value = '';
    timelineMembers.value = [];
  }
});

const loadTaskMembers = async () => {
  if (!shareTask.value) return;
  try {
    const res = await taskService.getMembers(shareTask.value.task_id);
    taskMembers.value = res.data;
  } catch (e: unknown) {
    console.error('載入成員失敗', e);
  }
};

const searchShareUser = async () => {
  shareSearchResult.value = null;
  shareSearchError.value = '';
  if (!shareInputEmail.value.trim()) return;
  if (!shareTask.value?.timeline_id) {
    shareSearchError.value = '此任務未關聯專案，無法透過 Email 搜尋協作者';
    return;
  }
  try {
    const res = await taskService.searchUser(shareTask.value.timeline_id, shareInputEmail.value.trim());
    const found = res.data;
    const alreadyIn = taskMembers.value.some(m => m.user_id === found.id);
    if (alreadyIn) { shareSearchError.value = '此使用者已是成員'; return; }
    shareSearchResult.value = found;
  } catch (e: unknown) {
    shareSearchError.value = getApiErrorMessage(e, '找不到使用者');
  }
};

const confirmShare = async () => {
  if (!shareSearchResult.value || !shareTask.value) return;

  const canAssign = await runConflictPrecheckForMemberAssignment(shareTask.value, {
    user_id: shareSearchResult.value.id,
    name: shareSearchResult.value.name,
  });
  if (!canAssign) {
    return;
  }

  try {
    await taskService.addMember(shareTask.value.task_id, shareSearchResult.value.id);
    shareInputEmail.value = '';
    shareSearchResult.value = null;
    await loadTaskMembers();
    await store.fetchTasks();
    toast.success('已成功指派成員');
  } catch (e: unknown) {
    shareSearchError.value = getApiErrorMessage(e, '新增失敗');
  }
};

const quickAssignMember = async (member: TaskMember) => {
  if (!shareTask.value) return;

  const canAssign = await runConflictPrecheckForMemberAssignment(shareTask.value, member);
  if (!canAssign) {
    return;
  }

  try {
    await taskService.addMember(shareTask.value.task_id, member.user_id);
    await loadTaskMembers();
    await store.fetchTasks();
    toast.success(`已指派 ${member.name}`);
  } catch (e: unknown) {
    toast.error(getApiErrorMessage(e, '指派失敗'));
  }
};

const kickTaskMember = async (member: TaskMember) => {
  if (!shareTask.value) return;
  if (!await confirm({ title: `確定要移除「${member.name}」？`, danger: true })) return;
  try {
    await taskService.removeMember(shareTask.value.task_id, member.user_id);
    await loadTaskMembers();
    await store.fetchTasks();
  } catch (e: unknown) {
    toast.error(getApiErrorMessage(e, '移除失敗'));
  }
};

const setTaskOwner = async (member: TaskMember) => {
  if (!shareTask.value) return;
  if (!await confirm({ title: `將「${member.name}」設為主責人？`, message: '原主責人會自動改為協作者。' })) return;

  try {
    await taskService.updateMemberRole(shareTask.value.task_id, member.user_id, 0);
    await loadTaskMembers();
    await store.fetchTasks();
    toast.success(`已將 ${member.name} 設為主責人`);
  } catch (e: unknown) {
    toast.error(getApiErrorMessage(e, '設定主責人失敗'));
  }
};

const downloadFile = async (url: string, originalFilename: string) => {
  try {
    await downloadFileFromUrl(url, originalFilename);
  } catch {
    toast.error('下載失敗，請稍後再試');
  }
};

onMounted(() => { void store.fetchTasks(); });
</script>
