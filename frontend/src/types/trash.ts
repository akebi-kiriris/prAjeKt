import type { ApiErrorPayload } from './common';

export interface TrashErrorPayload extends ApiErrorPayload {}

export interface TrashTask {
  task_id: number;
  name: string;
  deleted_at: string | null;
  end_date: string | null;
  priority: number;
  is_owner: boolean;
}

export interface TrashTimeline {
  id: number;
  name: string;
  deleted_at: string | null;
  start_date: string | null;
  end_date: string | null;
  is_owner: boolean;
}

export interface TrashPayloadResponse {
  tasks: TrashTask[];
  timelines: TrashTimeline[];
}
