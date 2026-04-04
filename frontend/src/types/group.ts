import type { ApiErrorPayload } from './common';

export interface Group {
  group_id: number;
  group_name: string;
  invite_code?: string;
  group_inviteCode?: string;
  created_at?: string;
  created_by?: number;
  description?: string | null;
  is_active?: boolean;
}

export interface Message {
  id?: number;
  message_id?: number;
  group_id?: number;
  user_id?: number;
  user_name?: string;
  sender_name?: string;
  content: string;
  created_at: string;
}

export interface SocketReadyPayload {
  user_id: number;
  name: string;
}

export interface SocketGroupErrorPayload {
  code: 'AUTH_FAILED' | 'NOT_MEMBER' | 'INVALID_PAYLOAD' | 'SERVER_ERROR' | string;
  message: string;
}

export interface SocketGroupMessagePayload {
  message_id: number;
  group_id: number;
  sender_id: number;
  sender_name: string;
  content: string;
  created_at: string;
}

export interface GroupCreateResponse {
  invite_code?: string;
}

export interface GroupErrorPayload extends ApiErrorPayload {}

export interface GroupSnapshotTopic {
  title: string;
  message_ids: number[];
}

export interface GroupSnapshotDecision {
  text: string;
  message_ids: number[];
}

export interface GroupSnapshotActionItem {
  text: string;
  assignee: string | null;
  message_ids: number[];
}

export interface GroupSnapshotBlocker {
  text: string;
  message_ids: number[];
}

export interface GroupSnapshotQuote {
  text: string;
  message_id: number | null;
}

export interface GroupSnapshotSummary {
  topics: GroupSnapshotTopic[];
  decisions: GroupSnapshotDecision[];
  action_items: GroupSnapshotActionItem[];
  blockers?: GroupSnapshotBlocker[];
  notable_quotes: GroupSnapshotQuote[];
  digest?: {
    overview: string;
    todo_for_user: GroupSnapshotActionItem[];
    watch_out: GroupSnapshotBlocker[];
    decisions_brief: GroupSnapshotDecision[];
  };
}

export interface GroupSnapshotResponse {
  snapshot_id: number;
  group_id: number;
  summary: GroupSnapshotSummary;
  created_by: number | null;
  created_at: string;
  source_count: number;
  model: string | null;
  provider: string | null;
  metadata: Record<string, unknown>;
}

export interface GroupSnapshotJobStatus {
  job_id: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | string;
  group_id?: number;
  requested_by?: number;
  window_days?: number;
  snapshot_id?: number | null;
  snapshot?: GroupSnapshotResponse | null;
  error?: string | null;
}

export interface GroupSnapshotRequest {
  window_days?: number;
  async?: boolean;
}
