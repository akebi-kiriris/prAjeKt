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
});
