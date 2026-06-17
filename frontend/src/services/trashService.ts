import api from './api';
import type { AxiosResponse } from 'axios';
import type { ApiMutationResponse, TrashPayloadResponse } from '../types';

export const trashService = {
  getAll:                  (): Promise<AxiosResponse<TrashPayloadResponse>>       => api.get('/trash'),
  restoreTask:             (id: number): Promise<AxiosResponse<ApiMutationResponse>>  => api.patch(`/trash/tasks/${id}/restore`),
  permanentDeleteTask:     (id: number): Promise<AxiosResponse<ApiMutationResponse>>  => api.delete(`/trash/tasks/${id}`),
  restoreTimeline:         (id: number): Promise<AxiosResponse<ApiMutationResponse>> => api.patch(`/trash/timelines/${id}/restore`),
  permanentDeleteTimeline: (id: number): Promise<AxiosResponse<ApiMutationResponse>>  => api.delete(`/trash/timelines/${id}`),
};
