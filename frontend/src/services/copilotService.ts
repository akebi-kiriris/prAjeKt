import api from './api';
import type { AxiosResponse } from 'axios';
import type {
  CopilotAgentExecuteByPlanPayload,
  CopilotAgentExecuteByPlanResponse,
  CopilotAgentPlanPayload,
  CopilotAgentPlanResponse,
  CopilotAgentRejectPayload,
  CopilotAgentRejectResponse,
  CopilotAgentReplanPayload,
  CopilotMcpExecutePayload,
  CopilotMcpExecuteResponse,
} from '../types';

export const copilotService = {
  executeMcp: (
    payload: CopilotMcpExecutePayload,
  ): Promise<AxiosResponse<CopilotMcpExecuteResponse>> => api.post('/copilot/mcp/execute', payload),
  createAgentPlan: (
    payload: CopilotAgentPlanPayload,
  ): Promise<AxiosResponse<CopilotAgentPlanResponse>> => api.post('/copilot/agent/plan', payload),
  executeAgentPlan: (
    payload: CopilotAgentExecuteByPlanPayload,
  ): Promise<AxiosResponse<CopilotAgentExecuteByPlanResponse>> => api.post('/copilot/agent/execute', payload),
  rejectAgentPlan: (
    payload: CopilotAgentRejectPayload,
  ): Promise<AxiosResponse<CopilotAgentRejectResponse>> => api.post('/copilot/agent/reject', payload),
  replanAgent: (
    payload: CopilotAgentReplanPayload,
  ): Promise<AxiosResponse<CopilotAgentPlanResponse>> => api.post('/copilot/agent/replan', payload),
  listAgentTools: (): Promise<AxiosResponse<{ tools: Array<Record<string, unknown>> }>> => api.get('/copilot/agent/tools'),
};
