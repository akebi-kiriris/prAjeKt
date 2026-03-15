import type { ApiErrorPayload } from './common';
import type { Task } from './task';

export interface TrashErrorPayload extends ApiErrorPayload {}

export interface TrashTask extends Task {
  deleted_at: string | null;
}

export interface TrashTimeline {
  id: number;
  name: string;
  deleted_at: string | null;
  start_date: string | null;
  end_date: string | null;
  is_owner: boolean;
}
