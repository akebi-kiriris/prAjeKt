<template>
  <div v-if="isAuthenticated" class="fixed right-4 bottom-22 z-70 md:right-5 md:bottom-5">
    <button
      class="inline-flex cursor-pointer items-center gap-2.5 rounded-full border border-slate-300 bg-linear-to-b from-white to-slate-50 px-4 py-2.5 font-bold tracking-[0.01em] text-slate-900 shadow-[0_10px_26px_rgba(15,23,42,0.14)] transition hover:-translate-y-px hover:scale-[1.01] hover:shadow-[0_16px_34px_rgba(15,23,42,0.2)]"
      type="button"
      :aria-expanded="isOpen"
      aria-controls="copilot-panel"
      @click="toggleOpen"
    >
      <span class="copilot-fab-label">{{ isOpen ? '收合 Agent' : '打開 Agent' }}</span>
      <span class="inline-flex h-7 w-7 items-center justify-center rounded-full bg-slate-900 text-[0.8rem] font-extrabold text-white">{{ isOpen ? '×' : 'AI' }}</span>
    </button>

    <transition name="copilot-panel-pop">
      <section
        v-if="isOpen"
        id="copilot-panel"
        class="mt-3 ml-auto w-[min(26rem,calc(100vw-1.5rem))] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl backdrop-blur-sm"
      >
        <header class="border-b border-slate-200 bg-slate-50/80 px-4 pt-4 pb-3.5">
          <h2 class="text-slate-900">Copilot Agent</h2>
          <p class="mt-1 text-[0.78rem] text-slate-600">自然語言目標 -> 多步工具調用</p>
          <p class="mt-1 text-xs text-slate-500">上下文由系統自動帶入（user/route）</p>
        </header>

        <form class="grid gap-3.5 px-4 pt-4 pb-4" @submit.prevent="submitPlan">
          <label class="grid gap-1.5">
            <span class="text-[0.78rem] font-semibold text-slate-700">你的目標</span>
            <textarea
              v-model="message"
              class="min-h-25.5 w-full resize-y rounded-[0.6rem] border border-slate-300 bg-white px-3 py-2.5 text-[0.9rem] text-slate-900 transition focus:border-slate-500 focus:outline-none focus:ring-3 focus:ring-slate-400/20"
              rows="4"
              placeholder="例如：幫我建立新任務，並先檢查時間衝突"
              required
            />
          </label>

          <div class="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
            <p class="leading-5">
              系統會自動帶入目前登入者與當前頁面上下文，無需手動填寫參數。
            </p>
            <p class="mt-0.5 leading-5">
              {{ contextSummary }}
            </p>
          </div>

          <button
            class="rounded-[0.7rem] bg-primary px-3 py-2.5 text-[0.92rem] font-bold text-white shadow-[0_8px_18px_rgba(37,99,235,0.22)] transition hover:-translate-y-px hover:shadow-[0_12px_22px_rgba(37,99,235,0.26)] disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-none"
            type="submit"
            :disabled="loading || planning"
          >
            {{ planning ? '規劃中...' : '產生執行計畫' }}
          </button>
        </form>

        <section v-if="planResult" class="border-t border-slate-200 bg-slate-50/70 px-4 pt-4 pb-4">
          <h3 class="text-slate-900">執行計畫預覽</h3>
          <p class="mt-1 text-[0.75rem] text-slate-500">Plan ID：{{ planResult.plan_id }}</p>
          <p class="mt-1.5 text-[0.89rem] leading-[1.45] text-slate-700">{{ planResult.summary }}</p>
          <p class="mt-1 text-[0.75rem] text-slate-500">有效至：{{ formatDate(planResult.expires_at) }}</p>
          <p class="mt-1 text-[0.75rem] text-slate-500">
            提案來源：{{ planResult.proposal_source === 'llm_proposal' ? '模型提案' : '規則回退' }}
          </p>
          <p v-if="planResult.proposal_reason" class="mt-1 text-[0.75rem] text-slate-500">
            提案說明：{{ planResult.proposal_reason }}
          </p>

          <h4 class="mt-3 text-slate-900">預計步驟（{{ planResult.steps_preview.length }}）</h4>
          <ol class="mt-1.5 grid gap-1.5 pl-4 text-[0.84rem]">
            <li v-for="(step, index) in planResult.steps_preview" :key="`preview-${index}`" class="text-slate-700">
              {{ step }}
            </li>
          </ol>

          <div v-if="planResult.risk_notes.length" class="mt-3 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            <p class="text-[0.75rem] font-semibold text-amber-800">注意事項</p>
            <ul class="mt-1 list-disc pl-4 text-[0.78rem] text-amber-700">
              <li v-for="(risk, index) in planResult.risk_notes" :key="`risk-${index}`">{{ risk }}</li>
            </ul>
          </div>

          <label class="mt-3 grid gap-1.5">
            <span class="text-[0.78rem] font-semibold text-slate-700">調整後需求（選填）</span>
            <textarea
              v-model="replanMessage"
              class="min-h-18 w-full resize-y rounded-[0.6rem] border border-slate-300 bg-white px-3 py-2 text-[0.84rem] text-slate-900 transition focus:border-slate-500 focus:outline-none focus:ring-3 focus:ring-slate-400/20"
              rows="2"
              placeholder="例如：先只建立專案，暫時不要建立任務"
            />
          </label>

          <div class="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
            <button
              class="rounded-[0.7rem] bg-primary px-3 py-2 text-[0.86rem] font-bold text-white disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="loading || !planResult"
              @click="confirmPlanExecution"
            >
              {{ loading ? '執行中...' : '確認執行' }}
            </button>
            <button
              class="rounded-[0.7rem] border border-indigo-300 bg-indigo-50 px-3 py-2 text-[0.86rem] font-semibold text-indigo-700 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="loading || !planResult"
              @click="replan"
            >
              {{ loading ? '處理中...' : '調整後重提案' }}
            </button>
            <button
              class="rounded-[0.7rem] border border-slate-300 bg-white px-3 py-2 text-[0.86rem] font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
              type="button"
              :disabled="loading || !planResult"
              @click="rejectPlan"
            >
              放棄計畫
            </button>
          </div>
        </section>

        <section v-if="result" class="border-t border-slate-200 bg-white px-4 pt-4 pb-4">
          <h3 class="text-slate-900">執行結果</h3>
          <p class="mt-1.5 mb-3.5 text-[0.89rem] leading-[1.45] text-slate-700">{{ result.final_answer }}</p>
          <h4 class="text-slate-900">工具步驟（{{ result.executed_tools.length }}）</h4>
          <ol class="mt-1.5 grid gap-1.5 pl-4 text-[0.84rem]">
            <li v-for="(step, index) in result.steps" :key="`${step.tool_name}-${index}`" class="flex items-center justify-between gap-3 text-slate-700">
              <strong class="truncate">{{ step.tool_name }}</strong>
              <span :class="step.output.ok ? 'step-ok' : 'step-fail'">
                {{ step.output.ok ? '成功' : '失敗' }}
              </span>
            </li>
          </ol>
        </section>
      </section>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';
import { useRoute } from 'vue-router';
import { toast } from 'vue-sonner';

import { copilotService } from '../services/copilotService';
import { useAuthStore } from '../stores/auth';
import { getApiErrorMessage } from '../utils/apiError';
import type {
  CopilotAgentExecuteResponse,
  CopilotAgentPlanResponse,
} from '../types';

const authStore = useAuthStore();
const { isAuthenticated, currentUser } = storeToRefs(authStore);
const route = useRoute();

const isOpen = ref(false);
const loading = ref(false);
const planning = ref(false);

const message = ref('');
const replanMessage = ref('');

const result = ref<CopilotAgentExecuteResponse | null>(null);
const planResult = ref<CopilotAgentPlanResponse | null>(null);

const parseOptionalInt = (value: unknown): number | undefined => {
  if (Array.isArray(value)) return parseOptionalInt(value[0]);
  if (value === undefined || value === null) return undefined;
  const parsed = Number.parseInt(String(value), 10);
  if (Number.isNaN(parsed) || parsed <= 0) return undefined;
  return parsed;
};

const autoContext = computed(() => {
  const routeTimelineId =
    parseOptionalInt(route.params.timelineId) ??
    parseOptionalInt(route.params.id) ??
    parseOptionalInt(route.query.timeline_id);
  const routeTaskId =
    parseOptionalInt(route.params.taskId) ??
    parseOptionalInt(route.query.task_id);
  const routeGroupId =
    parseOptionalInt(route.params.groupId) ??
    parseOptionalInt(route.query.group_id);

  return {
    user_id: currentUser.value?.id,
    timeline_id: routeTimelineId,
    task_id: routeTaskId,
    group_id: routeGroupId,
    timeline_name: typeof route.query.timeline_name === 'string' ? route.query.timeline_name : undefined,
  };
});

const contextSummary = computed((): string => {
  const areas: string[] = [];
  if (autoContext.value.timeline_id) areas.push('時間軸');
  if (autoContext.value.task_id) areas.push('任務');
  if (autoContext.value.group_id) areas.push('群組');
  if (areas.length === 0) return '目前未鎖定特定頁面物件，Agent 會以一般目標流程處理。';
  return `已偵測頁面上下文：${areas.join('、')}。`;
});

const toggleOpen = (): void => {
  isOpen.value = !isOpen.value;
};

const submitPlan = async (): Promise<void> => {
  const trimmedMessage = message.value.trim();
  if (!trimmedMessage) return;

  planning.value = true;
  result.value = null;
  planResult.value = null;
  replanMessage.value = '';
  try {
    const response = await copilotService.createAgentPlan({
      message: trimmedMessage,
      context: autoContext.value,
    });
    planResult.value = response.data;
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Agent 規劃失敗'));
  } finally {
    planning.value = false;
  }
};

const confirmPlanExecution = async (): Promise<void> => {
  if (!planResult.value) return;
  loading.value = true;
  try {
    const response = await copilotService.executeAgentPlan({
      plan_id: planResult.value.plan_id,
      confirm: true,
      max_loops: 6,
    });
    result.value = response.data.agent_result;
    planResult.value = null;
    replanMessage.value = '';
  } catch (error) {
    toast.error(getApiErrorMessage(error, 'Agent 執行失敗'));
  } finally {
    loading.value = false;
  }
};

const replan = async (): Promise<void> => {
  if (!planResult.value) return;
  const revisedGoal = replanMessage.value.trim() || message.value.trim();
  if (!revisedGoal) {
    toast.warning('請輸入調整後需求');
    return;
  }

  loading.value = true;
  try {
    const response = await copilotService.replanAgent({
      plan_id: planResult.value.plan_id,
      message: revisedGoal,
      context: autoContext.value,
    });
    planResult.value = response.data;
    result.value = null;
    message.value = revisedGoal;
    replanMessage.value = '';
    toast.success('已完成重提案，請再次確認後執行');
  } catch (error) {
    toast.error(getApiErrorMessage(error, '重提案失敗'));
  } finally {
    loading.value = false;
  }
};

const rejectPlan = async (): Promise<void> => {
  if (!planResult.value) return;
  loading.value = true;
  try {
    await copilotService.rejectAgentPlan({
      plan_id: planResult.value.plan_id,
      reason: '使用者取消',
    });
    planResult.value = null;
    replanMessage.value = '';
    toast.success('已取消本次計畫');
  } catch (error) {
    toast.error(getApiErrorMessage(error, '取消計畫失敗'));
  } finally {
    loading.value = false;
  }
};

const formatDate = (iso: string): string => {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '未知';
  return date.toLocaleString('zh-TW');
};
</script>

<style scoped>
.step-ok {
  margin-left: 0.3rem;
  color: #166534;
  font-weight: 700;
}

.step-fail {
  margin-left: 0.5rem;
  color: #b91c1c;
  font-weight: 700;
}

.copilot-panel-pop-enter-active,
.copilot-panel-pop-leave-active {
  transition: all 0.2s ease;
}

.copilot-panel-pop-enter-from,
.copilot-panel-pop-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
</style>
