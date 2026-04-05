import type { AiGeneratedTask } from './task';

export interface CopilotMcpContext {
  timeline_id?: number;
  timeline_name?: string;
  task_id?: number;
  group_id?: number;
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

export interface CopilotMcpExecuteResponse {
  message: string;
  selected_tool: string;
  selection_source: string;
  arguments: Record<string, unknown>;
  result: unknown;
  generated_tasks?: AiGeneratedTask[];
  auto_create_result?: CopilotAutoCreateResult;
}
