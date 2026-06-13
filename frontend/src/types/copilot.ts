import type { AiGeneratedTask } from './task';

export interface CopilotMcpContext {
  timeline_id?: number;
  timeline_name?: string;
  task_id?: number;
  group_id?: number;
}

export interface CopilotAgentContext extends CopilotMcpContext {
  user_id?: number;
}

export interface CopilotMcpExecutePayload {
  message: string;
  context?: CopilotMcpContext;
  preferred_tool?: string;
  tool_arguments?: Record<string, unknown>;
  auto_create_generated_tasks?: boolean;
}

export interface CopilotAutoCreateResult {
  message?: string;
  kept?: number;
  deleted?: number;
  created?: number;
}

export interface CopilotAgentTraceEvent {
  event_type: string;
  step_name: string;
  status?: string | null;
  duration_ms?: number | null;
  error_code?: string | null;
  detail: Record<string, unknown>;
  timestamp: string;
}

export interface CopilotAgentTrace {
  request_id: string;
  user_id?: number | null;
  plan_id?: string | null;
  routes: string[];
  status: string;
  started_at: string;
  updated_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  error_code?: string;
  metadata: Record<string, unknown>;
  events: CopilotAgentTraceEvent[];
}

export interface CopilotMcpExecuteResponse {
  message: string;
  selected_tool: string;
  selection_source: string;
  arguments: Record<string, unknown>;
  result: unknown;
  generated_tasks?: AiGeneratedTask[];
  auto_create_result?: CopilotAutoCreateResult;
  request_id?: string;
  trace?: CopilotAgentTrace;
}

export interface CopilotAgentPlanPayload {
  message: string;
  context?: CopilotAgentContext;
  tool_payloads?: Record<string, Record<string, unknown>>;
}

export interface CopilotAgentPlanResponse {
  ok: boolean;
  plan_id: string;
  status: 'planned' | 'executing' | 'succeeded' | 'failed' | 'rejected' | 'expired' | string;
  pending_tools?: string[];
  summary: string;
  steps_preview: string[];
  risk_notes: string[];
  expires_at: string;
  proposal_source?: 'llm_proposal' | 'rule_fallback' | string;
  proposal_reason?: string | null;
  request_id?: string;
  trace?: CopilotAgentTrace;
}

export interface CopilotAgentRejectPayload {
  plan_id: string;
  reason?: string;
}

export interface CopilotAgentRejectResponse {
  ok: boolean;
  plan_id: string;
  status: 'rejected' | string;
  request_id?: string;
  trace?: CopilotAgentTrace;
}

export interface CopilotAgentExecuteByPlanPayload {
  plan_id: string;
  confirm: boolean;
  max_loops?: number;
}

export interface CopilotAgentReplanPayload {
  plan_id?: string;
  message: string;
  context?: CopilotAgentContext;
  tool_payloads?: Record<string, Record<string, unknown>>;
}

export interface CopilotAgentStep {
  tool_name: string;
  input: Record<string, unknown>;
  output: {
    ok: boolean;
    data?: Record<string, unknown>;
    error?: {
      error_code: string;
      message: string;
      retryable: boolean;
      hint: string;
    };
  };
}

export interface CopilotAgentExecuteResponse {
  message: string;
  final_answer: string;
  steps: CopilotAgentStep[];
  executed_tools: string[];
  route: 'continue' | 'retry' | 'ask_user' | 'stop' | 'finalize' | string;
}

export interface CopilotAgentExecuteByPlanResponse {
  ok: boolean;
  plan_id: string;
  execution_id?: string;
  status: 'succeeded' | 'failed' | string;
  approved_pending_tools?: string[];
  executed_tools?: string[];
  summary: string;
  diff_from_plan: string[];
  steps_result: CopilotAgentStep[];
  agent_result: CopilotAgentExecuteResponse;
  request_id?: string;
  trace?: CopilotAgentTrace;
}
