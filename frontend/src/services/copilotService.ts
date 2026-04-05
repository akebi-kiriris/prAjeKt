import api from './api';
import type { AxiosResponse } from 'axios';
import type { CopilotMcpExecutePayload, CopilotMcpExecuteResponse } from '../types';

export const copilotService = {
  executeMcp: (
    payload: CopilotMcpExecutePayload,
  ): Promise<AxiosResponse<CopilotMcpExecuteResponse>> => api.post('/copilot/mcp/execute', payload),
};
