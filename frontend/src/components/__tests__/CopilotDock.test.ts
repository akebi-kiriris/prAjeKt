import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';

const mocks = vi.hoisted(() => ({
  route: {
    params: {},
    query: {},
  } as { params: Record<string, unknown>; query: Record<string, unknown> },
  createAgentPlan: vi.fn(),
  executeAgentPlan: vi.fn(),
  replanAgent: vi.fn(),
  rejectAgentPlan: vi.fn(),
  toastSuccess: vi.fn(),
  toastError: vi.fn(),
  toastWarning: vi.fn(),
}));

vi.mock('vue-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('vue-router')>();
  return {
    ...actual,
    useRoute: () => mocks.route,
  };
});

vi.mock('../../services/copilotService', () => ({
  copilotService: {
    createAgentPlan: mocks.createAgentPlan,
    executeAgentPlan: mocks.executeAgentPlan,
    replanAgent: mocks.replanAgent,
    rejectAgentPlan: mocks.rejectAgentPlan,
  },
}));

vi.mock('vue-sonner', () => ({
  toast: {
    success: mocks.toastSuccess,
    error: mocks.toastError,
    warning: mocks.toastWarning,
  },
}));

import CopilotDock from '../CopilotDock.vue';
import { useAuthStore } from '../../stores/auth';

const basePlan = {
  ok: true,
  plan_id: 'plan_a',
  status: 'planned',
  summary: '先建立專案',
  steps_preview: ['step1'],
  risk_notes: [],
  expires_at: '2026-06-03T00:00:00Z',
  proposal_source: 'llm_proposal',
  proposal_reason: '因為有上下文',
};

const mountOpenedDock = async () => {
  const wrapper = mount(CopilotDock, {
    global: { stubs: { transition: false } },
  });
  await wrapper.find('button').trigger('click');
  return wrapper;
};

const createPlan = async (wrapper: ReturnType<typeof mount>, goal = '建立專案') => {
  await wrapper.find('textarea').setValue(goal);
  await wrapper.find('form').trigger('submit.prevent');
  await flushPromises();
};

describe('CopilotDock', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setActivePinia(createPinia());
    const authStore = useAuthStore();
    authStore.user = { id: 12, name: 'User', email: 'u@a.com', username: null } as never;
    authStore.accessToken = 'token';
    authStore.refreshToken = 'refresh';
    mocks.route.params = {};
    mocks.route.query = {};
  });

  it('hides dock when unauthenticated', () => {
    const authStore = useAuthStore();
    authStore.accessToken = null;
    const wrapper = mount(CopilotDock);
    expect(wrapper.find('#copilot-panel').exists()).toBe(false);
    expect(wrapper.text()).toBe('');
  });

  it('submits plan with auto context and renders plan summary', async () => {
    mocks.route.query = { timeline_id: '99', task_id: '3', group_id: '7', timeline_name: 'Alpha' };
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });

    const wrapper = mount(CopilotDock, {
      global: { stubs: { transition: false } },
    });

    await wrapper.find('button').trigger('click');
    await wrapper.find('textarea').setValue('  建立專案  ');
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    expect(mocks.createAgentPlan).toHaveBeenCalledWith({
      message: '建立專案',
      context: {
        user_id: 12,
        timeline_id: 99,
        task_id: 3,
        group_id: 7,
        timeline_name: 'Alpha',
      },
      tool_payloads: {},
    });
    expect(wrapper.text()).toContain('Plan ID：plan_a');
    expect(wrapper.text()).toContain('模型提案');
    expect(wrapper.text()).toContain('提案說明：因為有上下文');
  });

  it('replans and requires confirm again', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.replanAgent.mockResolvedValueOnce({ data: { ...basePlan, plan_id: 'plan_b', summary: '改成只建專案' } });

    const wrapper = mount(CopilotDock, {
      global: { stubs: { transition: false } },
    });
    await wrapper.find('button').trigger('click');
    await wrapper.find('textarea').setValue('建立專案與任務');
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    const areas = wrapper.findAll('textarea');
    await areas[1].setValue('只建立專案');
    await wrapper.findAll('button').find((btn) => btn.text().includes('調整後重提案'))?.trigger('click');
    await flushPromises();

    expect(mocks.replanAgent).toHaveBeenCalledWith({
      plan_id: 'plan_a',
      message: '只建立專案',
      context: {
        user_id: 12,
        timeline_id: undefined,
        task_id: undefined,
        group_id: undefined,
        timeline_name: undefined,
      },
      tool_payloads: {},
    });
    expect(wrapper.text()).toContain('Plan ID：plan_b');
    expect(mocks.executeAgentPlan).not.toHaveBeenCalled();
  });

  it('confirms execution with latest plan id', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.executeAgentPlan.mockResolvedValueOnce({
      data: {
        agent_result: {
          final_answer: '完成',
          steps: [],
          executed_tools: [],
        },
      },
    });

    const wrapper = mount(CopilotDock, {
      global: { stubs: { transition: false } },
    });
    await wrapper.find('button').trigger('click');
    await wrapper.find('textarea').setValue('建立專案');
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    await wrapper.findAll('button').find((btn) => btn.text().includes('確認執行'))?.trigger('click');
    await flushPromises();

    expect(mocks.executeAgentPlan).toHaveBeenCalledWith({
      plan_id: 'plan_a',
      confirm: true,
      max_loops: 6,
    });
    expect(wrapper.text()).toContain('執行結果');
  });

  it('renders generated task suggestions from execution step output', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.executeAgentPlan.mockResolvedValueOnce({
      data: {
        agent_result: {
          final_answer: '任務已完成，已依序執行工具流程。',
          executed_tools: ['generate_timeline_tasks_with_ai'],
          steps: [
            {
              tool_name: 'generate_timeline_tasks_with_ai',
              input: {
                description: '請規劃 LangGraph 學習路徑',
              },
              output: {
                ok: true,
                data: {
                  existingCount: 0,
                  generatedCount: 2,
                  message: '現有 0 個任務，AI 生成 2 個新任務',
                  tasks: [
                    { name: 'LangGraph 基礎概念', estimated_days: 2, isExisting: false },
                    { name: 'State 與 Node 練習', estimated_days: 3, isExisting: false },
                  ],
                },
              },
            },
          ],
          route: 'finalize',
        },
      },
    });

    const wrapper = mount(CopilotDock, {
      global: { stubs: { transition: false } },
    });
    await wrapper.find('button').trigger('click');
    await wrapper.find('textarea').setValue('建立專案');
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    await wrapper.findAll('button').find((btn) => btn.text().includes('確認執行'))?.trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('AI 已產生 2 個新任務建議')
    expect(wrapper.text()).toContain('LangGraph 基礎概念（預估 2 天）')
    expect(wrapper.text()).toContain('State 與 Node 練習（預估 3 天）')
  });

  it('rejects plan', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.rejectAgentPlan.mockResolvedValueOnce({ data: { ok: true } });

    const wrapper = mount(CopilotDock, {
      global: { stubs: { transition: false } },
    });
    await wrapper.find('button').trigger('click');
    await wrapper.find('textarea').setValue('建立專案');
    await wrapper.find('form').trigger('submit.prevent');
    await flushPromises();

    await wrapper.findAll('button').find((btn) => btn.text().includes('放棄計畫'))?.trigger('click');
    await flushPromises();

    expect(mocks.rejectAgentPlan).toHaveBeenCalledWith({
      plan_id: 'plan_a',
      reason: '使用者取消',
    });
    expect(wrapper.text()).not.toContain('Plan ID：plan_a');
  });

  it('keeps the goal editable and clears planning state when plan creation fails', async () => {
    mocks.createAgentPlan.mockRejectedValueOnce(new Error('plan failed'));
    const wrapper = await mountOpenedDock();

    await createPlan(wrapper, '建立失敗後可重試');

    expect(mocks.toastError).toHaveBeenCalledWith('Agent 規劃失敗');
    expect(wrapper.text()).not.toContain('執行計畫預覽');
    expect((wrapper.find('textarea').element as HTMLTextAreaElement).value).toBe('建立失敗後可重試');
    expect(wrapper.find('button[type="submit"]').text()).toBe('產生執行計畫');
    expect(wrapper.find('button[type="submit"]').attributes('disabled')).toBeUndefined();
  });

  it('keeps the original plan when replan fails', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.replanAgent.mockRejectedValueOnce(new Error('replan failed'));
    const wrapper = await mountOpenedDock();
    await createPlan(wrapper);

    const areas = wrapper.findAll('textarea');
    await areas[1].setValue('改成另一個方案');
    await wrapper.findAll('button').find((btn) => btn.text().includes('調整後重提案'))?.trigger('click');
    await flushPromises();

    expect(mocks.toastError).toHaveBeenCalledWith('重提案失敗');
    expect(wrapper.text()).toContain('Plan ID：plan_a');
    expect(wrapper.text()).toContain('先建立專案');
    expect(wrapper.text()).not.toContain('執行結果');
    expect(wrapper.findAll('button').find((btn) => btn.text().includes('確認執行'))?.attributes('disabled'))
      .toBeUndefined();
  });

  it('keeps the plan available when execution fails', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.executeAgentPlan.mockRejectedValueOnce(new Error('execute failed'));
    const wrapper = await mountOpenedDock();
    await createPlan(wrapper);

    await wrapper.findAll('button').find((btn) => btn.text().includes('確認執行'))?.trigger('click');
    await flushPromises();

    expect(mocks.toastError).toHaveBeenCalledWith('Agent 執行失敗');
    expect(wrapper.text()).toContain('Plan ID：plan_a');
    expect(wrapper.text()).not.toContain('執行結果');
    expect(wrapper.findAll('button').find((btn) => btn.text().includes('確認執行'))?.attributes('disabled'))
      .toBeUndefined();
  });

  it('keeps the plan available when rejection fails', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.rejectAgentPlan.mockRejectedValueOnce(new Error('reject failed'));
    const wrapper = await mountOpenedDock();
    await createPlan(wrapper);

    await wrapper.findAll('button').find((btn) => btn.text().includes('放棄計畫'))?.trigger('click');
    await flushPromises();

    expect(mocks.toastError).toHaveBeenCalledWith('取消計畫失敗');
    expect(wrapper.text()).toContain('Plan ID：plan_a');
    expect(wrapper.findAll('button').find((btn) => btn.text().includes('放棄計畫'))?.attributes('disabled'))
      .toBeUndefined();
  });

  it('renders malformed step output safely without undefined text', async () => {
    mocks.createAgentPlan.mockResolvedValueOnce({ data: basePlan });
    mocks.executeAgentPlan.mockResolvedValueOnce({
      data: {
        agent_result: {
          final_answer: '部分步驟回傳非預期格式',
          executed_tools: ['unknown_tool', 'generate_timeline_tasks_with_ai'],
          steps: [
            {
              tool_name: 'unknown_tool',
              input: null,
              output: {
                ok: false,
                data: ['unexpected'],
                error: { message: '工具回傳格式錯誤' },
              },
            },
            {
              tool_name: 'generate_timeline_tasks_with_ai',
              input: {},
              output: {
                ok: true,
                data: {
                  tasks: [
                    null,
                    'invalid',
                    {},
                    { name: '  ', estimated_days: 'unknown', isExisting: false },
                    { name: '有效任務', isExisting: false },
                    { name: '既有任務', isExisting: true },
                  ],
                },
              },
            },
          ],
        },
      },
    });
    const wrapper = await mountOpenedDock();
    await createPlan(wrapper);

    await wrapper.findAll('button').find((btn) => btn.text().includes('確認執行'))?.trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('工具回傳格式錯誤');
    expect(wrapper.text()).toContain('未命名任務');
    expect(wrapper.text()).toContain('有效任務');
    expect(wrapper.text()).not.toContain('既有任務');
    expect(wrapper.text()).not.toContain('undefined');
  });
});
