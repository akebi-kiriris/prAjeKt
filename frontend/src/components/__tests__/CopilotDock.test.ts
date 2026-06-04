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
});
