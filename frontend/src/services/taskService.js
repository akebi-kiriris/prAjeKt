import api from './api';

export const taskService = {
  getAll:        ()                    => api.get('/tasks'),
  create:        (data)                => api.post('/tasks', data),
  update:        (id, data)            => api.put(`/tasks/${id}`, data),
  remove:        (id)                  => api.delete(`/tasks/${id}`),
  toggle:        (id)                  => api.patch(`/tasks/${id}/toggle`),
  updateStatus:  (id, status)          => api.patch(`/tasks/${id}/status`, { status }),
  getSubtasks:   (id)                  => api.get(`/tasks/${id}/subtasks`),
  createSubtask: (id, data)            => api.post(`/tasks/${id}/subtasks`, data),
  toggleSubtask: (taskId, subtaskId)   => api.patch(`/tasks/${taskId}/subtasks/${subtaskId}/toggle`),
  deleteSubtask: (taskId, subtaskId)   => api.delete(`/tasks/${taskId}/subtasks/${subtaskId}`),
};
