import api from './api';
import type { AxiosResponse } from 'axios';
import type { ApiCompletionResponse, ApiMutationResponse, ApiTaskStatusResponse, Task, CreateTaskPayload, TaskUpdatePayload, Subtask, TaskComment, TaskCommentSummaryResponse, TaskFile, TaskMember, SearchUserResult } from '../types';

export const taskService = {
  getAll:        (): Promise<AxiosResponse<Task[]>>                                    => api.get('/tasks'),
  create:        (data: CreateTaskPayload): Promise<AxiosResponse<ApiMutationResponse>> => api.post('/tasks', data),
  update:        (id: number, data: TaskUpdatePayload): Promise<AxiosResponse<ApiMutationResponse>> => api.put(`/tasks/${id}`, data),
  remove:        (id: number): Promise<AxiosResponse<void>>                            => api.delete(`/tasks/${id}`),
  toggle:        (id: number): Promise<AxiosResponse<ApiCompletionResponse>>           => api.patch(`/tasks/${id}/toggle`),
  updateStatus:  (id: number, status: Task['status']): Promise<AxiosResponse<ApiTaskStatusResponse>> => api.patch(`/tasks/${id}/status`, { status }),

  // 子任務
  getSubtasks:   (id: number): Promise<AxiosResponse<Subtask[]>>                      => api.get(`/tasks/${id}/subtasks`),
  createSubtask: (id: number, data: Pick<Subtask, 'name'>): Promise<AxiosResponse<Subtask>> => api.post(`/tasks/${id}/subtasks`, data),
  toggleSubtask: (taskId: number, subtaskId: number): Promise<AxiosResponse<Subtask>> => api.patch(`/tasks/${taskId}/subtasks/${subtaskId}/toggle`),
  deleteSubtask: (taskId: number, subtaskId: number): Promise<AxiosResponse<void>>    => api.delete(`/tasks/${taskId}/subtasks/${subtaskId}`),

  // 成員管理
  getMembers:    (id: number): Promise<AxiosResponse<TaskMember[]>>                   => api.get(`/tasks/${id}/members`),
  addMember:     (id: number, userId: number): Promise<AxiosResponse<TaskMember>>     => api.post(`/tasks/${id}/members`, { user_id: userId }),
  updateMemberRole: (taskId: number, userId: number, role: 0 | 1): Promise<AxiosResponse<ApiMutationResponse>> => api.patch(`/tasks/${taskId}/members/${userId}`, { role }),
  removeMember:  (taskId: number, userId: number): Promise<AxiosResponse<void>>       => api.delete(`/tasks/${taskId}/members/${userId}`),
  searchUser:    (email: string): Promise<AxiosResponse<SearchUserResult>> => api.post('/timelines/search_user', { email }),

  // 留言
  getComments:   (id: number): Promise<AxiosResponse<TaskComment[]>>                  => api.get(`/tasks/${id}/comments`),
  addComment:    (id: number, msg: string): Promise<AxiosResponse<TaskComment>>       => api.post(`/tasks/${id}/comments`, { task_message: msg }),
  deleteComment: (taskId: number, cid: number): Promise<AxiosResponse<void>>          => api.delete(`/tasks/${taskId}/comments/${cid}`),
  summarizeComments: (id: number): Promise<AxiosResponse<TaskCommentSummaryResponse>> => api.post(`/tasks/${id}/ai-comment-summary`, {}),

  // 附件
  getFiles:      (id: number): Promise<AxiosResponse<TaskFile[]>>                     => api.get(`/tasks/${id}/files`),
  uploadFile:    (id: number, formData: FormData): Promise<AxiosResponse<TaskFile>>   => api.post(`/tasks/${id}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  deleteFile:    (taskId: number, fileId: number): Promise<AxiosResponse<void>>       => api.delete(`/tasks/${taskId}/files/${fileId}`),

  upcoming:      (): Promise<AxiosResponse<Task[]>>                                   => api.get('/tasks/upcoming'),
};
