import api from './api';
import type { AxiosResponse } from 'axios';
import type {
  Group,
  Message,
  GroupSnapshotRequest,
  GroupSnapshotResponse,
  GroupSnapshotJobStatus,
} from '../types';

export const groupService = {
  getAll:      (): Promise<AxiosResponse<Group[]>>                                        => api.get('/groups'),
  create:      (name: string): Promise<AxiosResponse<Group>>                              => api.post('/groups', { group_name: name }),
  join:        (inviteCode: string): Promise<AxiosResponse<Group>>                        => api.post('/groups/join', { invite_code: inviteCode }),
  leave:       (groupId: number): Promise<AxiosResponse<void>>                            => api.post(`/groups/${groupId}/leave`),
  getMessages: (groupId: number): Promise<AxiosResponse<Message[]>>                       => api.get(`/groups/${groupId}/messages`),
  sendMessage: (groupId: number, content: string): Promise<AxiosResponse<Message>>        => api.post(`/groups/${groupId}/messages`, { content }),
  generateSnapshot: (groupId: number, payload: GroupSnapshotRequest = {}): Promise<AxiosResponse<GroupSnapshotResponse | GroupSnapshotJobStatus>> =>
    api.post(`/groups/${groupId}/ai-snapshot`, payload),
  getLatestSnapshot: (groupId: number): Promise<AxiosResponse<GroupSnapshotResponse>>      => api.get(`/groups/${groupId}/ai-snapshot/latest`),
  getSnapshotJobStatus: (jobId: string): Promise<AxiosResponse<GroupSnapshotJobStatus>>    => api.get(`/groups/snapshot-jobs/${jobId}`),
};
