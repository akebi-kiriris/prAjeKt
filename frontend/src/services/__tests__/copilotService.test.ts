import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { copilotService } from '../copilotService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
};

describe('copilotService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map POST /copilot/mcp/execute correctly', () => {
    const payload = {
      message: '幫我產生這個專案的任務清單',
      context: { timeline_id: 10, timeline_name: '網站重構' },
      preferred_tool: 'timeline_generate_tasks',
      tool_arguments: { description: '先分析需求，再拆任務' },
      auto_create_generated_tasks: false,
    };

    copilotService.executeMcp(payload);

    expect(mockedApi.post).toHaveBeenCalledWith('/copilot/mcp/execute', payload);
  });

  it('should map POST /copilot/agent/plan correctly', () => {
    const payload = {
      message: '幫我建立專案並拆任務',
      context: { user_id: 1 },
    };
    copilotService.createAgentPlan(payload);
    expect(mockedApi.post).toHaveBeenCalledWith('/copilot/agent/plan', payload);
  });

  it('should map POST /copilot/agent/reject correctly', () => {
    const payload = {
      plan_id: 'plan_abc',
      reason: '先取消',
    };
    copilotService.rejectAgentPlan(payload);
    expect(mockedApi.post).toHaveBeenCalledWith('/copilot/agent/reject', payload);
  });

  it('should map POST /copilot/agent/execute by plan correctly', () => {
    const payload = {
      plan_id: 'plan_abc',
      confirm: true,
      max_loops: 6,
    };
    copilotService.executeAgentPlan(payload);
    expect(mockedApi.post).toHaveBeenCalledWith('/copilot/agent/execute', payload);
  });

  it('should map POST /copilot/agent/replan correctly', () => {
    const payload = {
      plan_id: 'plan_abc',
      message: '請改成只建立專案，不建立任務',
      context: { user_id: 1 },
    };
    copilotService.replanAgent(payload);
    expect(mockedApi.post).toHaveBeenCalledWith('/copilot/agent/replan', payload);
  });

  it('should map GET /copilot/agent/tools correctly', () => {
    copilotService.listAgentTools();
    expect(mockedApi.get).toHaveBeenCalledWith('/copilot/agent/tools');
  });
});
