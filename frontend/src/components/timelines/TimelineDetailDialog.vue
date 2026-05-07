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

          <!-- 週報預覽（Phase 7.1） -->
          <div class="mb-4 p-4 bg-slate-50 border border-slate-200 rounded-xl">
            <div class="flex items-center justify-between gap-3 mb-3">
              <div>
                <p class="text-sm font-semibold text-slate-700">📊 週報預覽</p>
                <p class="text-xs text-slate-500">完成任務、風險與下一步建議</p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  @click="toggleWeeklyReportExpanded"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors"
                >
                  {{ isWeeklyReportExpanded ? '收合' : '展開' }}
                </button>
                <button
                  @click="fetchWeeklyReport"
                  :disabled="weeklyReportLoading"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-200 text-slate-600 hover:bg-slate-100 transition-colors disabled:opacity-50"
                >
                  {{ weeklyReportLoading ? '載入中...' : '重新整理' }}
                </button>
              </div>
            </div>

            <div v-show="isWeeklyReportExpanded">
              <div class="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <label class="block text-[11px] text-slate-500 mb-1">起始日</label>
                  <input
                    v-model="weeklyReportRange.start_date"
                    type="date"
                    class="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  />
                </div>
                <div>
                  <label class="block text-[11px] text-slate-500 mb-1">結束日</label>
                  <input
                    v-model="weeklyReportRange.end_date"
                    type="date"
                    class="w-full px-3 py-2 text-xs border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                  />
                </div>
              </div>

              <div v-if="weeklyReportError" class="mb-3 p-2.5 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg">
                {{ weeklyReportError }}
              </div>

              <div v-if="weeklyReportLoading" class="text-xs text-slate-500 py-2">正在產生週報...</div>

              <div v-else-if="weeklyReport" class="space-y-3">
                <div v-if="weeklyReport.ai_summary" class="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <p class="text-xs font-medium text-blue-700 mb-1">📌 AI 週報摘要</p>
                  <p class="text-xs text-blue-600">{{ weeklyReport.ai_summary }}</p>
                  <p class="mt-1 text-[11px] text-blue-500">來源：{{ getWeeklyReportAiSummarySourceLabel(weeklyReport.ai_summary_source) }}</p>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
                    <p class="text-[11px] text-slate-500">本期完成</p>
                    <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.completed_tasks }}</p>
                  </div>
                  <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
                    <p class="text-[11px] text-slate-500">總任務數</p>
                    <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.total_tasks }}</p>
                  </div>
                  <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
                    <p class="text-[11px] text-slate-500">完成率</p>
                    <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.completion_rate }}%</p>
                  </div>
                  <div class="p-2.5 bg-white border border-slate-200 rounded-lg">
                    <p class="text-[11px] text-slate-500">風險項目</p>
                    <p class="text-sm font-semibold text-slate-700">{{ weeklyReport.overview.at_risk_tasks }}</p>
                  </div>
                </div>

                <div class="grid md:grid-cols-2 gap-3">
                  <div class="p-3 bg-white border border-slate-200 rounded-lg">
                    <p class="text-xs font-medium text-slate-600 mb-2">本期完成任務</p>
                    <div v-if="weeklyReport.completed_tasks.length === 0" class="text-xs text-slate-400">本期尚無完成任務</div>
                    <ul v-else class="space-y-1.5">
                      <li
                        v-for="item in weeklyReport.completed_tasks.slice(0, 5)"
                        :key="`weekly-done-${item.task_id}`"
                        class="text-xs text-slate-600"
                      >
                        ✓ {{ item.name }}
                        <span class="text-slate-400">（{{ formatDate(item.completed_at || item.due_date) || '未標記' }}）</span>
                      </li>
                    </ul>
                  </div>

                  <div class="p-3 bg-white border border-slate-200 rounded-lg flex flex-col">
                    <p class="text-xs font-medium text-slate-600 mb-2">風險清單</p>
                    <div v-if="weeklyReport.risk_items.length === 0" class="text-xs text-slate-400">本期無風險項目</div>
                    <ul v-else class="space-y-1.5 overflow-y-auto max-h-48 pr-2">
                      <li
                        v-for="item in weeklyReport.risk_items"
                        :key="`weekly-risk-${item.task_id}`"
                        class="text-xs text-amber-700"
                      >
                        ⚠ {{ item.name }}
                        <span class="text-amber-600">（{{ item.reason }}，截止 {{ formatDate(item.due_date) || item.due_date }}）</span>
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 風險分析（Phase 7.2） -->
          <div class="mb-4 p-4 bg-rose-50 border border-rose-200 rounded-xl">
            <div class="flex items-center justify-between gap-3 mb-3">
              <div>
                <p class="text-sm font-semibold text-rose-700">⚠️ 風險分析（Critical Path）</p>
                <p class="text-xs text-rose-500">關鍵路徑、延期衝擊與資料品質警示</p>
              </div>
              <div class="flex items-center gap-2">
                <button
                  @click="toggleRiskAnalysisExpanded"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors"
                >
                  {{ isRiskAnalysisExpanded ? '收合' : '展開' }}
                </button>
                <button
                  @click="toggleRiskGraph"
                  :disabled="riskAnalysisLoading"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors disabled:opacity-50"
                >
                  {{ isRiskGraphVisible ? '隱藏依賴圖' : '產生依賴圖' }}
                </button>
                <button
                  @click="fetchRiskAnalysis"
                  :disabled="riskAnalysisLoading"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors disabled:opacity-50"
                >
                  {{ riskAnalysisLoading ? '載入中...' : '重新整理' }}
                </button>
              </div>
            </div>

            <div v-show="isRiskAnalysisExpanded">
              <div v-if="riskAnalysisError" class="mb-3 p-2.5 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg">
                {{ riskAnalysisError }}
              </div>

              <div v-if="riskAnalysisLoading" class="text-xs text-rose-500 py-2">正在分析關鍵路徑...</div>

              <div v-else-if="riskAnalysis" class="space-y-3">
                <div v-if="isRiskGraphVisible" class="p-3 bg-white border border-rose-200 rounded-lg">
                  <div class="flex items-center justify-between mb-2">
                    <p class="text-xs font-medium text-rose-700">依賴圖（自動佈局）</p>
                    <button
                      type="button"
                      @click="rebuildRiskGraph"
                      class="px-2.5 py-1 text-[11px] rounded-md border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors"
                    >
                      重新產生
                    </button>
                  </div>

                  <div v-if="!riskGraphLayout" class="text-xs text-rose-400">
                    目前沒有可視化的依賴資料（請先建立任務依賴）。
                  </div>

                  <div v-else class="overflow-x-auto border border-rose-100 rounded-lg bg-rose-50/30">
                    <svg
                      :key="riskGraphVersion"
                      :width="riskGraphLayout.width"
                      :height="riskGraphLayout.height"
                      role="img"
                      aria-label="risk dependency graph"
                    >
                      <defs>
                        <marker
                          id="risk-graph-arrow"
                          markerWidth="8"
                          markerHeight="8"
                          refX="7"
                          refY="4"
                          orient="auto"
                        >
                          <path d="M0,0 L8,4 L0,8 z" fill="#94a3b8" />
                        </marker>
                      </defs>

                      <line
                        v-for="edge in riskGraphLayout.edges"
                        :key="`risk-graph-edge-${edge.source_task_id}-${edge.target_task_id}`"
                        :x1="edge.x1"
                        :y1="edge.y1"
                        :x2="edge.x2"
                        :y2="edge.y2"
                        :stroke="edge.is_critical ? '#e11d48' : '#94a3b8'"
                        :stroke-width="edge.is_critical ? 2.2 : 1.4"
                        marker-end="url(#risk-graph-arrow)"
                      />

                      <g
                        v-for="node in riskGraphLayout.nodes"
                        :key="`risk-graph-node-${node.task_id}`"
                      >
                        <rect
                          :x="node.x"
                          :y="node.y"
                          :width="RISK_GRAPH_NODE_WIDTH"
                          :height="RISK_GRAPH_NODE_HEIGHT"
                          :rx="10"
                          :fill="getRiskGraphNodeFill(node)"
                          :stroke="getRiskGraphNodeStroke(node)"
                          :stroke-width="node.is_critical ? 2.2 : 1.4"
                        />
                        <text
                          :x="node.x + 10"
                          :y="node.y + 20"
                          font-size="11"
                          fill="#334155"
                        >
                          {{ truncateRiskGraphNodeName(node.name) }}
                        </text>
                        <text
                          :x="node.x + 10"
                          :y="node.y + 36"
                          font-size="10"
                          fill="#64748b"
                        >
                          #{{ node.task_id }} · {{ node.is_critical ? 'Critical' : 'Normal' }}
                        </text>
                      </g>
                    </svg>
                  </div>

                  <div class="mt-2 flex flex-wrap gap-2 text-[11px]">
                    <span class="px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 border border-rose-200">關鍵路徑</span>
                    <span class="px-2 py-0.5 rounded-full bg-red-100 text-red-700 border border-red-200">高風險</span>
                    <span class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 border border-amber-200">中風險</span>
                    <span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 border border-slate-200">一般任務</span>
                  </div>
                </div>

                <div class="grid grid-cols-2 md:grid-cols-4 gap-2">
                  <div class="p-2.5 bg-white border border-rose-200 rounded-lg">
                    <p class="text-[11px] text-rose-500">預估總工期</p>
                    <p class="text-sm font-semibold text-rose-700">{{ riskAnalysis.summary.projected_duration_days }} 天</p>
                  </div>
                  <div class="p-2.5 bg-white border border-rose-200 rounded-lg">
                    <p class="text-[11px] text-rose-500">關鍵路徑任務</p>
                    <p class="text-sm font-semibold text-rose-700">{{ riskAnalysis.summary.critical_path_task_count }} 項</p>
                  </div>
                  <div class="p-2.5 bg-white border border-rose-200 rounded-lg">
                    <p class="text-[11px] text-rose-500">高風險任務</p>
                    <p class="text-sm font-semibold text-rose-700">{{ riskAnalysis.summary.high_risk_count }} 項</p>
                  </div>
                  <div class="p-2.5 bg-white border border-rose-200 rounded-lg">
                    <p class="text-[11px] text-rose-500">警示數</p>
                    <p class="text-sm font-semibold text-rose-700">{{ riskAnalysis.summary.warning_count }} 筆</p>
                  </div>
                </div>

                <div class="grid md:grid-cols-2 gap-3">
                  <div class="p-3 bg-white border border-rose-200 rounded-lg">
                    <p class="text-xs font-medium text-rose-700 mb-2">關鍵路徑</p>
                    <div v-if="riskAnalysis.critical_path.length === 0" class="text-xs text-rose-400">目前沒有可計算的路徑</div>
                    <ol v-else class="space-y-1.5">
                      <li
                        v-for="(item, idx) in riskAnalysis.critical_path"
                        :key="`critical-path-${item.task_id}`"
                        class="text-xs text-rose-700"
                      >
                        {{ idx + 1 }}. {{ item.name }}
                        <span class="text-rose-500">（工期 {{ item.duration_days }} 天，float {{ item.float_days }}）</span>
                      </li>
                    </ol>
                  </div>

                  <div class="p-3 bg-white border border-rose-200 rounded-lg">
                    <p class="text-xs font-medium text-rose-700 mb-2">風險任務</p>
                    <div v-if="riskAnalysis.risk_items.length === 0" class="text-xs text-rose-400">目前無風險任務</div>
                    <ul v-else class="space-y-1.5 overflow-y-auto max-h-48 pr-2">
                      <li
                        v-for="item in riskAnalysis.risk_items.slice(0, 8)"
                        :key="`risk-item-${item.task_id}`"
                        class="text-xs"
                      >
                        <p class="font-medium text-rose-700">
                          {{ item.name }}
                          <span class="text-rose-500">（{{ item.severity.toUpperCase() }}，impact {{ item.impact_days }} 天）</span>
                        </p>
                        <p class="text-rose-600 mt-0.5">{{ item.reasons.join('；') }}</p>
                      </li>
                    </ul>
                  </div>
                </div>

                <div v-if="riskAnalysis.warnings.length > 0" class="p-3 bg-white border border-rose-200 rounded-lg">
                  <p class="text-xs font-medium text-rose-700 mb-2">資料警示</p>
                  <ul class="space-y-1.5 max-h-32 overflow-y-auto pr-2">
                    <li
                      v-for="(warning, index) in riskAnalysis.warnings"
                      :key="`risk-warning-${warning.code}-${index}`"
                      class="text-xs text-rose-600"
                    >
                      • {{ warning.message }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div class="mb-4 p-4 bg-indigo-50 border border-indigo-200 rounded-xl">
            <div class="flex items-center justify-between gap-3 mb-3">
              <div>
                <p class="text-sm font-semibold text-indigo-700">專案檔案區</p>
                <p class="text-xs text-indigo-500">支援上傳、批次操作與 RAG 引用來源</p>
              </div>
              <div class="flex items-center gap-2">
                <input
                  ref="projectKnowledgeInput"
                  type="file"
                  class="hidden"
                  @change="handleProjectKnowledgeUpload"
                />
                <button
                  type="button"
                  class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-100 transition-colors disabled:opacity-60"
                  :disabled="projectKnowledgeUploading"
                  @click="projectKnowledgeInput?.click()"
                >
                  {{ projectKnowledgeUploading ? '上傳中...' : '上傳檔案' }}
                </button>
                <button type="button" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-indigo-200 text-indigo-600 hover:bg-indigo-100 transition-colors" @click="fetchProjectKnowledgeDocuments">刷新</button>
              </div>
            </div>
            <div class="grid md:grid-cols-3 gap-2 mb-3">
              <input v-model="projectKnowledgeQuery" type="text" placeholder="搜尋檔名" class="px-3 py-2 text-xs border border-indigo-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
              <select v-model="projectKnowledgeSort" class="px-3 py-2 text-xs border border-indigo-200 rounded-lg bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                <option value="created_desc">最新建立</option>
                <option value="created_asc">最早建立</option>
                <option value="name_asc">檔名 A-Z</option>
                <option value="name_desc">檔名 Z-A</option>
                <option value="status_asc">狀態</option>
              </select>
              <select v-model="projectKnowledgeStatus" class="px-3 py-2 text-xs border border-indigo-200 rounded-lg bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none">
                <option value="">全部狀態</option>
                <option value="uploaded">uploaded</option>
                <option value="indexing">indexing</option>
                <option value="ready">ready</option>
                <option value="failed">failed</option>
              </select>
            </div>
            <div class="flex items-center gap-2 mb-3">
              <button type="button" class="px-3 py-1.5 text-xs rounded-lg border border-red-200 text-red-600 bg-white hover:bg-red-50 disabled:opacity-40" :disabled="projectKnowledgeSelectedIds.length===0" @click="batchDeleteProjectKnowledge">批次刪除</button>
              <button type="button" class="px-3 py-1.5 text-xs rounded-lg border border-amber-200 text-amber-700 bg-white hover:bg-amber-50 disabled:opacity-40" :disabled="projectKnowledgeSelectedIds.length===0" @click="batchReindexProjectKnowledge">批次重建</button>
              <button type="button" class="px-3 py-1.5 text-xs rounded-lg border border-indigo-200 text-indigo-700 bg-white hover:bg-indigo-50" @click="fetchProjectKnowledgeDocuments">套用篩選</button>
            </div>
            <p v-if="projectKnowledgeError" class="mb-2 text-xs text-red-600">{{ projectKnowledgeError }}</p>
            <div v-if="projectKnowledgeLoading" class="text-xs text-indigo-500">載入中...</div>
            <div v-else-if="projectKnowledgeDocuments.length===0" class="text-xs text-indigo-400">目前沒有檔案</div>
            <div v-else class="space-y-2 mb-3">
              <div v-for="doc in projectKnowledgeDocuments" :key="`pk-doc-${doc.id}`" class="p-2.5 bg-white border border-indigo-100 rounded-lg text-xs flex items-start gap-2">
                <input type="checkbox" class="mt-0.5" :checked="projectKnowledgeSelectedIds.includes(doc.id)" @change="toggleKnowledgeSelection(doc.id)" />
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <p class="font-medium text-indigo-700 truncate">{{ doc.original_filename || doc.filename }}</p>
                    <span class="px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-700">{{ doc.status }}</span>
                  </div>
                  <p class="text-indigo-500 mt-0.5">
                    {{ typeof doc.chunk_count === 'number' ? `${doc.chunk_count} chunks` : '索引數未知' }}
                  </p>
                  <p v-if="doc.error_message" class="text-red-500 mt-0.5">{{ doc.error_message }}</p>
                </div>
                <div class="flex items-center gap-1">
                  <button type="button" class="px-2 py-1 border border-indigo-200 rounded text-indigo-700 hover:bg-indigo-50" @click="downloadProjectKnowledgeDocument(doc)">下載</button>
                  <button type="button" class="px-2 py-1 border border-indigo-200 rounded text-indigo-700 hover:bg-indigo-50" @click="previewProjectKnowledgeDocument(doc)">預覽</button>
                </div>
              </div>
            </div>
            <div>
              <p class="text-xs font-semibold text-indigo-700 mb-1">最近操作</p>
              <div v-if="projectKnowledgeEvents.length===0" class="text-xs text-indigo-400">尚無紀錄</div>
              <div v-else class="space-y-1 max-h-24 overflow-y-auto pr-1">
                <p v-for="evt in projectKnowledgeEvents" :key="`pk-evt-${evt.id}`" class="text-xs text-indigo-600">
                  {{ evt.event_type }} · #{{ evt.document_id || '-' }} · {{ formatDateTime(evt.created_at || '') }}
                </p>
              </div>
            </div>
          </div>

          <!-- 任務列表 -->
          <div class="space-y-2">
            <div v-for="task in timelineTasks" :key="task.task_id" class="flex items-center gap-3 p-3 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors group">
              <input type="checkbox" :checked="task.completed" @change="$emit('toggle-task', task.task_id)" class="w-5 h-5 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer" />
              <div class="flex-1 min-w-0">
                <span :class="['text-sm cursor-pointer', task.completed ? 'line-through text-gray-400' : 'text-gray-700']" @click="openTaskDetail(task)">{{ task.name }}</span>
                <p v-if="(task.depends_on_task_ids || []).length > 0" class="text-[11px] text-gray-400 mt-0.5 truncate">
                  前置：{{ (task.depends_on_task_ids || []).map(getTaskNameById).join('、') }}
                </p>
              </div>
              <span v-if="task.end_date" class="text-xs text-gray-400 hidden group-hover:inline">{{ formatDate(task.end_date) }}</span>
              <span :class="['text-xs px-2 py-0.5 rounded-full font-medium', getPriorityBadgeClass(task.priority)]">{{ getPriorityLabel(task.priority) }}</span>
              <button v-if="canManageTaskMembers(task)" @click.stop="openTaskMemberPanel(task)" class="opacity-100 md:opacity-0 md:group-hover:opacity-100 text-indigo-400 hover:text-indigo-600 transition-all text-sm" title="指派成員">👥</button>
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
            <label class="block text-sm font-medium text-gray-700 mb-1.5">指派成員（可多選）</label>
            <select
              v-model="addTaskAssigneeIds"
              multiple
              class="w-full min-h-30 px-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white text-sm"
            >
              <option
                v-for="member in timelineMembers"
                :key="`add-assignee-${member.user_id}`"
                :value="member.user_id"
              >
                {{ member.username || member.name }}
              </option>
            </select>
            <p class="text-[11px] text-gray-500 mt-1.5">
              未選擇時預設分派給自己。若分派給他人，衝突明細會只顯示件數。
            </p>
            <div v-if="addTaskAssigneeIds.length > 0" class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="memberId in addTaskAssigneeIds"
                :key="`add-assignee-chip-${memberId}`"
                class="px-2.5 py-1 text-xs rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100"
              >
                {{ getTimelineMemberName(memberId) }}
              </span>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">前置依賴任務（可多選）</label>
            <select
              v-model="addTaskDependencyIds"
              multiple
              class="w-full min-h-30 px-3 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white text-sm"
            >
              <option
                v-for="taskOption in availableDependencyTasks"
                :key="`add-dependency-${taskOption.task_id}`"
                :value="taskOption.task_id"
              >
                {{ taskOption.name }}
              </option>
            </select>
            <p class="text-[11px] text-gray-500 mt-1.5">僅可依賴本專案任務；會自動去重與驗證。</p>
            <div v-if="addTaskDependencyIds.length > 0" class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="dependencyId in addTaskDependencyIds"
                :key="`add-dependency-chip-${dependencyId}`"
                class="px-2.5 py-1 text-xs rounded-full bg-slate-100 text-slate-700 border border-slate-200"
              >
                {{ getTaskNameById(dependencyId) }}
              </span>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">標籤（逗號分隔）</label>
            <input v-model="taskForm.tags" type="text" placeholder="例如：前端, 重要, Bug" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none" />
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1.5">備註</label>
            <textarea v-model="taskForm.task_remark" rows="3" placeholder="任務備註（可選）" class="w-full px-4 py-2.5 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"></textarea>
          </div>
          <div v-if="addTaskConflictSummary.hasConflict" class="p-3 bg-amber-50 border border-amber-200 rounded-xl">
            <p class="text-sm font-semibold text-amber-700 mb-1">⚠️ 偵測到 {{ addTaskConflictSummary.totalSignals }} 個排程衝突訊號</p>
            <p class="text-[11px] text-amber-700/90 mb-2">依被分派者逐一檢測，分派給他人時僅顯示件數。</p>

            <div class="space-y-2.5">
              <div
                v-for="item in addTaskConflictPreviews.filter((entry) => entry.preview.has_conflict)"
                :key="`add-conflict-assignee-${item.assignee_user_id ?? 'self'}`"
                class="p-2.5 bg-white/70 border border-amber-200 rounded-lg"
              >
                <p class="text-xs font-semibold text-amber-700 mb-1.5">
                  👤 {{ item.assignee_label }}：{{ item.preview.conflict_count }} 個訊號
                </p>
                <div class="text-[11px] text-amber-700/90 space-y-1 mb-2">
                  <p v-if="(item.preview.cross_project_conflict_count ?? 0) > 0">
                    跨專案衝突：{{ item.preview.cross_project_conflict_count }} 個
                  </p>
                  <p v-if="(item.preview.workload_overload_count ?? 0) > 0">
                    過載日：{{ item.preview.workload_overload_count }} 天
                  </p>
                </div>

                <ul class="list-disc list-inside text-xs text-amber-700 space-y-1">
                  <li v-for="conflict in item.preview.conflicts.slice(0, 3)" :key="`add-conflict-${item.assignee_user_id ?? 'self'}-${conflict.task_id}`">
                    {{ conflict.name }}（{{ conflict.reason }}，{{ conflict.start_date }} ~ {{ conflict.end_date }}）
                  </li>
                </ul>

                <div
                  v-if="(item.preview.workload_overload_days ?? []).length > 0"
                  class="mt-2.5 p-2.5 bg-white/80 border border-amber-200 rounded-lg"
                >
                  <p class="text-xs font-semibold text-amber-700 mb-1.5">📅 過載日列表</p>
                  <ul class="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                    <li
                      v-for="day in item.preview.workload_overload_days"
                      :key="`overload-${item.assignee_user_id ?? 'self'}-${day.date}`"
                      class="text-xs text-amber-700"
                    >
                      <span class="font-medium">{{ formatDate(day.date) || day.date }}</span>
                      <span class="text-amber-600">：{{ day.projected_task_count }} 件（門檻 {{ day.threshold }}）</span>
                      <p v-if="day.sample_tasks.length" class="text-[11px] text-amber-600 mt-0.5 line-clamp-1">
                        既有任務：{{ day.sample_tasks.join('、') }}
                      </p>
                      <p v-else class="text-[11px] text-amber-600 mt-0.5">
                        既有任務：{{ day.existing_task_count }} 件（僅顯示件數）
                      </p>
                    </li>
                  </ul>
                </div>

                <p v-if="item.preview.suggestion" class="text-xs text-amber-600 mt-2">
                  建議改期為 {{ item.preview.suggestion.start_date }} ~ {{ item.preview.suggestion.end_date }}
                </p>
                <button
                  type="button"
                  @click="requestAddTaskConflictAiSuggestion(item.assignee_user_id)"
                  :disabled="conflictAiSuggestionLoadingKey === getConflictPreviewKey(item.assignee_user_id)"
                  class="mt-2 inline-flex items-center px-2.5 py-1 text-[11px] rounded-md border border-amber-300 text-amber-700 bg-white hover:bg-amber-50 transition-colors disabled:opacity-50"
                >
                  {{ conflictAiSuggestionLoadingKey === getConflictPreviewKey(item.assignee_user_id) ? 'AI 產生中...' : '✨ 產生 AI 衝突建議' }}
                </button>
                <p v-if="item.preview.ai_suggestion" class="text-xs text-amber-700 italic mt-2">
                  💡 {{ item.preview.ai_suggestion }}
                </p>
              </div>
            </div>
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
                  <p class="font-medium text-gray-800">{{ searchResult.name }}</p>
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
          <div class="p-4 bg-slate-50 rounded-xl">
            <h4 class="font-semibold text-gray-700 mb-2">🔗 前置依賴</h4>
            <select
              v-model="selectedTaskDependencyIds"
              multiple
              class="w-full min-h-30 px-3 py-2.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none bg-white text-sm"
            >
              <option
                v-for="taskOption in selectedTaskDependencyOptions"
                :key="`detail-dependency-option-${taskOption.task_id}`"
                :value="taskOption.task_id"
              >
                {{ taskOption.name }}
              </option>
            </select>
            <p class="text-[11px] text-gray-500 mt-1.5">僅可依賴本專案任務；會自動去重與驗證。</p>
            <div v-if="selectedTaskDependencyIds.length > 0" class="mt-2 flex flex-wrap gap-1.5">
              <span
                v-for="dependencyId in selectedTaskDependencyIds"
                :key="`detail-dependency-chip-${dependencyId}`"
                class="px-2.5 py-1 text-xs rounded-full bg-slate-200 text-slate-700"
              >
                {{ getTaskNameById(dependencyId) }}
              </span>
            </div>
            <div class="mt-3 flex justify-end">
              <button
                type="button"
                @click="saveSelectedTaskDependencies"
                :disabled="isSavingTaskDependencies"
                class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-slate-300 text-slate-700 hover:bg-slate-100 transition-colors disabled:opacity-50"
              >
                {{ isSavingTaskDependencies ? '儲存中...' : '儲存前置依賴' }}
              </button>
            </div>
          </div>

          <!-- ── 成員指派區 ── -->
          <div v-if="canManageTaskMembers(selectedTask)" class="p-4 bg-indigo-50/60 rounded-xl">
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
            <p class="text-gray-500 mb-4 text-center">可輸入需求情境，讓 AI 透過 MCP 生成更貼近專案的任務建議</p>
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
                  <input v-model="useRagPlanning" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                  使用 RAG 規劃建議
                </label>
                <label v-if="!useRagPlanning" class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input v-model="useCopilotMcp" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                  優先使用 AI + MCP 工具路由
                </label>
                <label v-if="useRagPlanning" class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input v-model="usePersonalKnowledge" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                  納入個人知識庫
                </label>
                <label v-if="useRagPlanning" class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input v-model="useProjectKnowledge" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" @change="useProjectKnowledgeTouched = true" />
                  納入專案檔案
                </label>
                <label class="inline-flex items-center gap-2 cursor-pointer select-none">
                  <input v-model="autoCreateAfterGenerate" type="checkbox" class="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary" />
                  生成後直接建立任務
                </label>
              </div>
              <p v-if="ragErrorMessage" class="text-sm text-red-600">{{ ragErrorMessage }}</p>
            </div>
            <div class="text-center">
              <button @click="generateTasksWithAi" class="px-6 py-3 bg-linear-to-r from-purple-500 to-indigo-500 text-white font-semibold rounded-xl hover:brightness-110 transition-all shadow-lg shadow-purple-200">
                {{ useRagPlanning ? '📚 RAG 規劃生成' : (useCopilotMcp ? '✨ AI 智慧生成' : '🤖 開始生成') }}
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
            <div v-if="ragSourceReferences.length > 0" class="p-3 rounded-xl border border-indigo-100 bg-indigo-50/60">
              <p class="text-xs font-semibold text-indigo-700 mb-2">來源依據（{{ ragSourceReferences.length }}）</p>
              <p v-if="ragSummary" class="text-xs text-indigo-600 mb-2">{{ ragSummary }}</p>
              <div class="space-y-2 max-h-40 overflow-y-auto pr-1">
                <div v-for="ref in ragSourceReferences" :key="`${ref.source_type}-${ref.source_id}`" class="text-xs text-indigo-700 bg-white/80 border border-indigo-100 rounded-lg p-2">
                  <p class="font-medium">{{ getSourceReferenceLabel(ref.source_type) }} · score {{ Number(ref.score || 0).toFixed(2) }}</p>
                  <p class="truncate">{{ ref.title }}</p>
                  <p class="text-indigo-500 line-clamp-2">{{ ref.snippet }}</p>
                </div>
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
                    <p v-if="(task.depends_on_task_refs || []).length > 0" class="text-xs text-indigo-600 mt-1">
                      🔗 前置：{{ (task.depends_on_task_refs || []).join('、') }}
                    </p>
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
import { toast } from 'vue-sonner';
import { taskService } from '../../services/taskService';
import { timelineService } from '../../services/timelineService';
import { copilotService } from '../../services/copilotService';
import { formatDate, formatDateTime, formatFileSize, isImageFile, getFileIcon } from '../../utils/formatters';
import { downloadFileFromUrl, loadTaskDetailResourcesWithMembers } from '../../utils/taskDetails';
import { useConfirm } from '../../composables/useConfirm';
import { getApiErrorMessage } from '../../utils/apiError';
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
  TimelineBatchCreateTasksResponse,
  TimelineBatchTaskPayload,
  GenerateTasksResponse,
  AIPlanSuggestionResponse,
  CopilotMcpExecuteResponse,
  CriticalPathAnalysisResponse,
  KnowledgeDocumentEventItem,
  KnowledgeDocumentItem,
  SourceReference,
  WeeklyReportAiSummarySource,
  WeeklyReportResponse,
  ConflictCheckPayload,
  ResourceConflictResponse,
} from '../../types';

const { confirm } = useConfirm();

const props = defineProps<TimelineDetailDialogProps>();

const getSourceReferenceLabel = (sourceType: SourceReference['source_type']) => {
  if (sourceType === 'timeline_task') return '歷史任務';
  return '知識文件';
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
const projectKnowledgeInput = ref<HTMLInputElement | null>(null);
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

const toDateOnly = (value?: string | null): string | null => {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed.toISOString().split('T')[0];
};

const getTimelineMemberName = (memberId: number): string => {
  const member = timelineMembers.value.find((item) => item.user_id === memberId);
  return member?.username || member?.name || `使用者 #${memberId}`;
};

const normalizeIdList = (values: Array<number | string>): number[] => {
  return Array.from(
    new Set(
      values
        .map((value) => Number(value))
        .filter((value) => Number.isInteger(value) && value > 0)
    )
  );
};

const normalizeStringList = (values: unknown): string[] => {
  if (!Array.isArray(values)) {
    return [];
  }

  return Array.from(
    new Set(
      values
        .map((value) => (typeof value === 'string' ? value.trim() : ''))
        .filter((value) => value.length > 0)
    )
  );
};

const collectTasksWithPotentiallyDroppedDependencies = (tasks: TimelineBatchTaskPayload[]): string[] => {
  const selectedTaskNames = new Set<string>();
  const selectedExistingTaskIds = new Set<number>();

  for (const task of tasks) {
    const name = String(task.name ?? '').trim();
    if (name) {
      selectedTaskNames.add(name);
    }

    if (task.isExisting) {
      const taskId = Number(task.task_id);
      if (Number.isInteger(taskId) && taskId > 0) {
        selectedExistingTaskIds.add(taskId);
      }
    }
  }

  const affectedTaskNames = new Set<string>();

  for (const task of tasks) {
    if (task.isExisting) {
      continue;
    }

    const taskName = String(task.name ?? '').trim();
    if (!taskName) {
      continue;
    }

    const dependencyRefs = normalizeStringList(task.depends_on_task_refs);
    const dependencyIds = normalizeIdList(task.depends_on_task_ids || []);

    const hasMissingRef = dependencyRefs.some((ref) => !selectedTaskNames.has(ref));

    const currentTaskId = Number(task.task_id);
    const hasCurrentTaskId = Number.isInteger(currentTaskId) && currentTaskId > 0;
    const hasMissingId = dependencyIds.some((dependencyId) => {
      if (hasCurrentTaskId && dependencyId === currentTaskId) {
        return true;
      }
      return !selectedExistingTaskIds.has(dependencyId);
    });

    if (hasMissingRef || hasMissingId) {
      affectedTaskNames.add(taskName);
    }
  }

  return Array.from(affectedTaskNames);
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
    start_date: data.start_date ?? null,
    end_date: data.end_date ?? null,
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

const getDefaultWeeklyReportRange = () => {
  const end = new Date();
  const start = new Date(end);
  start.setDate(end.getDate() - 6);

  return {
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0],
  };
};

const getWeeklyReportAiSummarySourceLabel = (source?: WeeklyReportAiSummarySource | string) => {
  switch (source) {
    case 'llm':
      return 'AI 直接生成';
    case 'cache':
      return 'AI 快取結果';
    case 'fallback-timeout':
      return '模板回退（AI 逾時）';
    case 'fallback-error':
      return '模板回退（AI 錯誤）';
    case 'fallback-empty':
      return '模板回退（AI 回傳空內容）';
    default:
      return '未標記';
  }
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

  const payloadData = mapToCreateTaskPayload({
    ...taskForm.value,
    timeline_id: props.selectedTimeline.id,
    assignee_user_ids: normalizeIdList(addTaskAssigneeIds.value),
    depends_on_task_ids: normalizeIdList(addTaskDependencyIds.value),
  });

  if (!payloadData.end_date) {
    toast.warning('請先填寫截止日期再產生 AI 衝突建議');
    return;
  }

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

    selectedTask.value = {
      ...selectedTask.value,
      depends_on_task_ids: dependencyIds,
    };
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

const mapRagPriorityToTaskPriority = (priority: string | undefined): number => {
  const normalized = String(priority || '').toUpperCase();
  if (normalized === 'CRITICAL' || normalized === 'HIGH') return 1;
  if (normalized === 'LOW') return 3;
  return 2;
};

const mapRagResponseToGeneratedTasks = (payload: AIPlanSuggestionResponse): AiGeneratedTask[] => {
  const tasks = Array.isArray(payload.suggested_tasks) ? payload.suggested_tasks : [];
  const today = new Date();
  return tasks.map((task, index) => {
    const estimatedDays = Number(task.estimated_days) > 0 ? Number(task.estimated_days) : 3;
    const startDate = new Date(today);
    const endDate = new Date(today);
    startDate.setDate(today.getDate() + index);
    endDate.setDate(startDate.getDate() + Math.max(estimatedDays - 1, 0));

    return {
      name: task.name || `建議任務 ${index + 1}`,
      priority: mapRagPriorityToTaskPriority(task.priority),
      estimated_days: estimatedDays,
      start_date: startDate.toISOString().split('T')[0],
      end_date: endDate.toISOString().split('T')[0],
      remark: task.reason || null,
      task_remark: task.reason || null,
      depends_on_task_refs: Array.isArray(task.depends_on) ? task.depends_on : [],
      status: 'pending',
    };
  });
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
        priority: Number(task.priority) || 2,
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

const getPriorityLabel = (priority: number) => ({ 1: '🔴 高', 2: '🟡 中', 3: '🟢 低' }[priority] || '🟡 中');

const getPriorityBadgeClass = (priority: number) => ({
  1: 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border border-red-200',
  2: 'bg-gradient-to-r from-yellow-100 to-amber-100 text-yellow-700 border border-yellow-200',
  3: 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border border-green-200'
}[priority] || 'bg-gray-100 text-gray-700 border border-gray-200');

const getAiPriorityClass = (priority: number) => ({
  1: 'bg-red-100 text-red-700', 2: 'bg-yellow-100 text-yellow-700', 3: 'bg-green-100 text-green-700'
}[priority] || 'bg-gray-100 text-gray-700');

const fetchProjectKnowledgeDocuments = async () => {
  if (!props.selectedTimeline) return;
  projectKnowledgeLoading.value = true;
  projectKnowledgeError.value = '';
  try {
    const res = await timelineService.listKnowledgeDocuments({
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
    const res = await timelineService.listKnowledgeDocumentEvents({
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
    await timelineService.uploadKnowledgeDocument(file, props.selectedTimeline.id);
    toast.success('檔案已上傳');
    await fetchProjectKnowledgeDocuments();
    await fetchProjectKnowledgeEvents();
  } catch (err: unknown) {
    toast.error(getApiErrorMessage(err, '上傳失敗'));
  } finally {
    projectKnowledgeUploading.value = false;
    if (projectKnowledgeInput.value) projectKnowledgeInput.value.value = '';
  }
};

const batchDeleteProjectKnowledge = async () => {
  if (!props.selectedTimeline || projectKnowledgeSelectedIds.value.length === 0) return;
  if (!await confirm({ title: `確定刪除 ${projectKnowledgeSelectedIds.value.length} 份檔案？`, danger: true })) return;
  try {
    await timelineService.batchDeleteKnowledgeDocuments(props.selectedTimeline.id, projectKnowledgeSelectedIds.value);
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
    await timelineService.batchReindexKnowledgeDocuments(props.selectedTimeline.id, projectKnowledgeSelectedIds.value);
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
    const res = await timelineService.downloadKnowledgeDocumentFile(document.id, props.selectedTimeline.id);
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
    const res = await timelineService.previewKnowledgeDocumentFile(document.id, props.selectedTimeline.id);
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
