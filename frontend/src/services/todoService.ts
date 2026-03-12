import api from './api';
import type { AxiosResponse } from 'axios';
import type { Todo, CreateTodoPayload } from '../types';

export const todoService = {
  getAll:         (): Promise<AxiosResponse<Todo[]>>                  => api.get('/todos'),
  create:         (data: CreateTodoPayload): Promise<AxiosResponse<Todo>> => api.post('/todos', data),
  update:         (id: number, data: Partial<Todo>): Promise<AxiosResponse<Todo>> => api.put(`/todos/${id}`, data),
  remove:         (id: number): Promise<AxiosResponse<void>>          => api.delete(`/todos/${id}`),
  toggleComplete: (id: number): Promise<AxiosResponse<Todo>>          => api.patch(`/todos/${id}/toggle`),
};
