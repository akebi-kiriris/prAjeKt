import api from './api';
import type { AxiosResponse } from 'axios';
import type { ApiMutationResponse, TrashTask, TrashTimeline } from '../types';

interface TrashItem {
  tasks: TrashTask[];
  timelines: TrashTimeline[];
}

export const trashService = {
  getAll:                  (): Promise<AxiosResponse<TrashItem>>       => api.get('/trash'),
  restoreTask:             (id: number): Promise<AxiosResponse<ApiMutationResponse>>  => api.patch(`/trash/tasks/${id}/restore`),
  permanentDeleteTask:     (id: number): Promise<AxiosResponse<void>>  => api.delete(`/trash/tasks/${id}`),
  restoreTimeline:         (id: number): Promise<AxiosResponse<ApiMutationResponse>> => api.patch(`/trash/timelines/${id}/restore`),
  permanentDeleteTimeline: (id: number): Promise<AxiosResponse<void>>  => api.delete(`/trash/timelines/${id}`),
};
