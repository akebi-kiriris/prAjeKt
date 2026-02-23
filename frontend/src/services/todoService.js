import api from './api';

export const todoService = {
  getAll:         ()         => api.get('/todos'),
  create:         (data)     => api.post('/todos', data),
  update:         (id, data) => api.put(`/todos/${id}`, data),
  remove:         (id)       => api.delete(`/todos/${id}`),
  toggleComplete: (id)       => api.patch(`/todos/${id}/toggle`),
};
