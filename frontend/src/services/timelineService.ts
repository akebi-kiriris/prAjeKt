import api from './api';
import type { AxiosResponse } from 'axios';
import type {
  ApiMutationResponse,
  Timeline,
  CreateTimelinePayload,
  UpdateTimelinePayload,
  CreateTaskPayload,
  Task,
  TaskMember,
  ProjectStats,
  SearchUserResult,
  GenerateTasksRequest,
  GenerateTasksResponse,
} from '../types';

export const timelineService = {
  getAll:           (): Promise<AxiosResponse<Timeline[]>>                                       => api.get('/timelines'),
  create:           (data: CreateTimelinePayload): Promise<AxiosResponse<ApiMutationResponse>>   => api.post('/timelines', data),
  update:           (id: number, data: UpdateTimelinePayload): Promise<AxiosResponse<ApiMutationResponse>> => api.put(`/timelines/${id}`, data),
  remove:           (id: number): Promise<AxiosResponse<void>>                                   => api.delete(`/timelines/${id}`),
  getTasks:         (id: number): Promise<AxiosResponse<Task[]>>                                 => api.get(`/timelines/${id}/tasks`),
  updateRemark:     (id: number, remark: string): Promise<AxiosResponse<ApiMutationResponse>>    => api.put(`/timelines/${id}/remark`, { remark }),
  searchUser:       (email: string): Promise<AxiosResponse<SearchUserResult>> => api.post('/timelines/search_user', { email }),
  addMember:        (id: number, userId: number): Promise<AxiosResponse<TaskMember>>             => api.post(`/timelines/${id}/members`, { user_id: userId, role: 1 }),
  generateTasks:    (id: number, payload: GenerateTasksRequest = {}): Promise<AxiosResponse<GenerateTasksResponse>> => api.post(`/timelines/${id}/generate-tasks`, payload),
  batchCreateTasks: (id: number, tasks: CreateTaskPayload[]): Promise<AxiosResponse<Task[]>>      => api.post(`/timelines/${id}/batch-create-tasks`, { tasks }),
  getMembers:       (id: number): Promise<AxiosResponse<TaskMember[]>>                           => api.get(`/timelines/${id}/members`),
  removeMember:     (id: number, userId: number): Promise<AxiosResponse<void>>                   => api.delete(`/timelines/${id}/members/${userId}`),
  upcoming:         (): Promise<AxiosResponse<Timeline[]>>                                       => api.get('/timelines/upcoming'),
  getMemberStats:   (id: number): Promise<AxiosResponse<ProjectStats>>                          => api.get(`/timelines/${id}/member-stats`),
};
