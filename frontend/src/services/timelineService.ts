import api from './api';
import type { AxiosResponse } from 'axios';
import type {
  ApiMutationResponse,
  Timeline,
  CreateTimelinePayload,
  UpdateTimelinePayload,
  TimelineBatchTaskPayload,
  TimelineBatchCreateTasksResponse,
  Task,
  TaskMember,
  ProjectStats,
  SearchUserResult,
  GenerateTasksRequest,
  GenerateTasksResponse,
  WeeklyReportResponse,
  CriticalPathAnalysisResponse,
  ConflictCheckPayload,
  ResourceConflictResponse,
  AIPlanSuggestionRequest,
  AIPlanSuggestionResponse,
  KnowledgeDocumentsResponse,
  KnowledgeDocumentEventsResponse,
} from '../types';

const knowledgeProjectParams = (projectId?: number) => (projectId ? { project_id: projectId } : undefined);

export const timelineService = {
  getAll:           (): Promise<AxiosResponse<Timeline[]>>                                       => api.get('/timelines'),
  create:           (data: CreateTimelinePayload): Promise<AxiosResponse<ApiMutationResponse>>   => api.post('/timelines', data),
  update:           (id: number, data: UpdateTimelinePayload): Promise<AxiosResponse<ApiMutationResponse>> => api.put(`/timelines/${id}`, data),
  remove:           (id: number): Promise<AxiosResponse<ApiMutationResponse>>                    => api.delete(`/timelines/${id}`),
  getTasks:         (id: number): Promise<AxiosResponse<Task[]>>                                 => api.get(`/timelines/${id}/tasks`),
  updateRemark:     (id: number, remark: string): Promise<AxiosResponse<ApiMutationResponse>>    => api.put(`/timelines/${id}/remark`, { remark }),
  searchUser:       (timelineId: number, email: string): Promise<AxiosResponse<SearchUserResult>> => api.post('/timelines/search_user', { timeline_id: timelineId, email }),
  addMember:        (id: number, userId: number): Promise<AxiosResponse<TaskMember>>             => api.post(`/timelines/${id}/members`, { user_id: userId, role: 1 }),
  generateTasks:    (id: number, payload: GenerateTasksRequest = {}): Promise<AxiosResponse<GenerateTasksResponse>> => api.post(`/timelines/${id}/generate-tasks`, payload),
  batchCreateTasks: (id: number, tasks: TimelineBatchTaskPayload[]): Promise<AxiosResponse<TimelineBatchCreateTasksResponse>> =>
    api.post(`/timelines/${id}/batch-create-tasks`, { tasks }),
  getMembers:       (id: number): Promise<AxiosResponse<TaskMember[]>>                           => api.get(`/timelines/${id}/members`),
  removeMember:     (id: number, userId: number): Promise<AxiosResponse<ApiMutationResponse>>    => api.delete(`/timelines/${id}/members/${userId}`),
  upcoming:         (): Promise<AxiosResponse<Timeline[]>>                                       => api.get('/timelines/upcoming'),
  getMemberStats:   (id: number): Promise<AxiosResponse<ProjectStats>>                          => api.get(`/timelines/${id}/member-stats`),
  getWeeklyReport:  (
    id: number,
    params?: { start_date?: string; end_date?: string }
  ): Promise<AxiosResponse<WeeklyReportResponse>> => api.get(`/timelines/${id}/weekly-report`, {
    params,
    timeout: 45000,
  }),
  getRiskAnalysis:  (id: number): Promise<AxiosResponse<CriticalPathAnalysisResponse>> =>
    api.get(`/timelines/${id}/risk-analysis`),
  conflictCheck:    (id: number, payload: ConflictCheckPayload): Promise<AxiosResponse<ResourceConflictResponse>> =>
    api.post(`/timelines/${id}/conflict-check`, payload),
  suggestPlan:      (payload: AIPlanSuggestionRequest): Promise<AxiosResponse<AIPlanSuggestionResponse>> =>
    api.post('/timelines/ai-suggest-plan', payload, { timeout: 90000 }),
  listKnowledgeDocuments: (
    params?: {
      limit?: number;
      offset?: number;
      project_id?: number;
      q?: string;
      sort?: 'created_desc' | 'created_asc' | 'name_asc' | 'name_desc' | 'status_asc';
      status?: string;
    }
  ): Promise<AxiosResponse<KnowledgeDocumentsResponse>> =>
    api.get('/knowledge/documents', { params }),
  uploadKnowledgeDocument: (file: File, projectId?: number): Promise<AxiosResponse<{ message: string }>> => {
    const form = new FormData();
    form.append('file', file);
    const config: { headers: { 'Content-Type': string }; params?: { project_id: number } } = {
      headers: { 'Content-Type': 'multipart/form-data' },
    };
    const params = knowledgeProjectParams(projectId);
    if (params) config.params = params;
    return api.post('/knowledge/documents', form, config);
  },
  deleteKnowledgeDocument: (documentId: number, projectId?: number): Promise<AxiosResponse<{ message: string }>> =>
    api.delete(`/knowledge/documents/${documentId}`, { params: knowledgeProjectParams(projectId) }),
  reindexKnowledgeDocument: (documentId: number, projectId?: number): Promise<AxiosResponse<{ message: string }>> =>
    api.post(`/knowledge/documents/${documentId}/reindex`, null, { params: knowledgeProjectParams(projectId) }),
  batchDeleteKnowledgeDocuments: (projectId: number, documentIds: number[]) =>
    api.post('/knowledge/documents/batch-delete', { document_ids: documentIds }, { params: { project_id: projectId } }),
  batchReindexKnowledgeDocuments: (projectId: number, documentIds: number[]) =>
    api.post('/knowledge/documents/batch-reindex', { document_ids: documentIds }, { params: { project_id: projectId } }),
  downloadKnowledgeDocumentFile: (documentId: number, projectId: number): Promise<AxiosResponse<Blob>> =>
    api.get(`/knowledge/documents/${documentId}/download`, {
      params: { project_id: projectId },
      responseType: 'blob',
    }),
  previewKnowledgeDocumentFile: (documentId: number, projectId: number): Promise<AxiosResponse<Blob>> =>
    api.get(`/knowledge/documents/${documentId}/preview`, {
      params: { project_id: projectId },
      responseType: 'blob',
    }),
  listKnowledgeDocumentEvents: (
    params: { project_id: number; limit?: number; offset?: number }
  ): Promise<AxiosResponse<KnowledgeDocumentEventsResponse>> =>
    api.get('/knowledge/documents/events', { params }),
};
