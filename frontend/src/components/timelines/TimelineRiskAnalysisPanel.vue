<template>
  <div class="mb-4 p-4 bg-rose-50 border border-rose-200 rounded-xl">
    <div class="flex items-center justify-between gap-3 mb-3">
      <div>
        <p class="text-sm font-semibold text-rose-700">⚠️ 風險分析（Critical Path）</p>
        <p class="text-xs text-rose-500">關鍵路徑、延期衝擊與資料品質警示</p>
      </div>
      <div class="flex items-center gap-2">
        <button
          @click="$emit('toggle-expanded')"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors"
        >
          {{ expanded ? '收合' : '展開' }}
        </button>
        <button
          @click="$emit('toggle-graph')"
          :disabled="loading"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors disabled:opacity-50"
        >
          {{ isRiskGraphVisible ? '隱藏依賴圖' : '產生依賴圖' }}
        </button>
        <button
          @click="$emit('refresh')"
          :disabled="loading"
          class="px-3 py-1.5 text-xs font-medium rounded-lg bg-white border border-rose-200 text-rose-600 hover:bg-rose-100 transition-colors disabled:opacity-50"
        >
          {{ loading ? '載入中...' : '重新整理' }}
        </button>
      </div>
    </div>

    <div v-show="expanded">
      <div v-if="error" class="mb-3 p-2.5 text-xs text-red-600 bg-red-50 border border-red-200 rounded-lg">
        {{ error }}
      </div>

      <div v-if="loading" class="text-xs text-rose-500 py-2">正在分析關鍵路徑...</div>

      <div v-else-if="riskAnalysis" class="space-y-3">
        <div v-if="isRiskGraphVisible" class="p-3 bg-white border border-rose-200 rounded-lg">
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs font-medium text-rose-700">依賴圖（自動佈局）</p>
            <button
              type="button"
              @click="$emit('rebuild-graph')"
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
                  :width="nodeWidth"
                  :height="nodeHeight"
                  :rx="10"
                  :fill="getNodeFill(node)"
                  :stroke="getNodeStroke(node)"
                  :stroke-width="node.is_critical ? 2.2 : 1.4"
                />
                <text
                  :x="node.x + 10"
                  :y="node.y + 20"
                  font-size="11"
                  fill="#334155"
                >
                  {{ truncateNodeName(node.name) }}
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
</template>

<script setup lang="ts">
import type { CriticalPathAnalysisResponse } from '../../types';

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

defineProps<{
  expanded: boolean;
  loading: boolean;
  error: string;
  riskAnalysis: CriticalPathAnalysisResponse | null;
  isRiskGraphVisible: boolean;
  riskGraphVersion: number;
  riskGraphLayout: RiskGraphLayout | null;
  nodeWidth: number;
  nodeHeight: number;
  truncateNodeName: (name: string) => string;
  getNodeFill: (node: RiskGraphLayoutNode) => string;
  getNodeStroke: (node: RiskGraphLayoutNode) => string;
}>();

defineEmits<{
  (e: 'toggle-expanded'): void;
  (e: 'toggle-graph'): void;
  (e: 'refresh'): void;
  (e: 'rebuild-graph'): void;
}>();
</script>
