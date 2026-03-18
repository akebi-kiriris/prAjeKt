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
