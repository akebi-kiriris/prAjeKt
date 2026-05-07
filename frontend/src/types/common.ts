export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
}

export interface ApiErrorPayload {
  error?: string;
  error_code?: string;
  error_details?: Record<string, unknown>;
}

export interface ApiMutationResponse {
  message: string;
  id?: number;
  task_id?: number;
}

export interface ApiCompletionResponse extends ApiMutationResponse {
  completed: boolean;
}

import type { TaskStatus } from './task';

export interface ApiTaskStatusResponse extends ApiCompletionResponse {
  status: TaskStatus;
}

export interface DaysRemainingResult {
  days: number | null;
  text: string;
  display: string;
  colorClass: string;
}
