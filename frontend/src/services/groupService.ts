import api from './api';
import type { AxiosResponse } from 'axios';
import type {
  Group,
  Message,
  GroupCreateResponse,
  GroupJoinResponse,
  GroupLeaveResponse,
  GroupSendMessageResponse,
  GroupSnapshotRequest,
  GroupSnapshotResponse,
  GroupSnapshotJobStatus,
  GroupSnapshotGenerationResponse,
} from '../types';

export const groupService = {
  getAll:      (): Promise<AxiosResponse<Group[]>>                                        => api.get('/groups'),
  create:      (name: string): Promise<AxiosResponse<GroupCreateResponse>>                => api.post('/groups', { group_name: name }),
  join:        (inviteCode: string): Promise<AxiosResponse<GroupJoinResponse>>            => api.post('/groups/join', { invite_code: inviteCode }),
  leave:       (groupId: number): Promise<AxiosResponse<GroupLeaveResponse>>              => api.post(`/groups/${groupId}/leave`),
  getMessages: (groupId: number): Promise<AxiosResponse<Message[]>>                       => api.get(`/groups/${groupId}/messages`),
  sendMessage: (groupId: number, content: string): Promise<AxiosResponse<GroupSendMessageResponse>> =>
    api.post(`/groups/${groupId}/messages`, { content }),
  generateSnapshot: (groupId: number, payload: GroupSnapshotRequest = {}): Promise<AxiosResponse<GroupSnapshotGenerationResponse>> =>
    api.post(`/groups/${groupId}/ai-snapshot`, payload),
  getLatestSnapshot: (groupId: number): Promise<AxiosResponse<GroupSnapshotResponse>>      => api.get(`/groups/${groupId}/ai-snapshot/latest`),
  getSnapshotJobStatus: (jobId: string): Promise<AxiosResponse<GroupSnapshotJobStatus>>    => api.get(`/groups/snapshot-jobs/${jobId}`),
};
