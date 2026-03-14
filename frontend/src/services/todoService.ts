import api from './api';
import type { AxiosResponse } from 'axios';
import type { ApiCompletionResponse, ApiMutationResponse, Todo, CreateTodoPayload, UpdateTodoPayload } from '../types';

export const todoService = {
  getAll:         (): Promise<AxiosResponse<Todo[]>>                  => api.get('/todos'),
  create:         (data: CreateTodoPayload): Promise<AxiosResponse<ApiMutationResponse>> => api.post('/todos', data),
  update:         (id: number, data: UpdateTodoPayload): Promise<AxiosResponse<ApiMutationResponse>> => api.put(`/todos/${id}`, data),
  remove:         (id: number): Promise<AxiosResponse<void>>          => api.delete(`/todos/${id}`),
  toggleComplete: (id: number): Promise<AxiosResponse<ApiCompletionResponse>> => api.patch(`/todos/${id}/toggle`),
};
