import api from './api';

export const timelineService = {
  getAll:           ()              => api.get('/timelines'),
  create:           (data)          => api.post('/timelines', data),
  update:           (id, data)      => api.put(`/timelines/${id}`, data),
  remove:           (id)            => api.delete(`/timelines/${id}`),
  getTasks:         (id)            => api.get(`/timelines/${id}/tasks`),
  updateRemark:     (id, remark)    => api.put(`/timelines/${id}/remark`, { remark }),
  searchUser:       (email)         => api.post('/timelines/search_user', { email }),
  addMember:        (id, userId)    => api.post(`/timelines/${id}/members`, { user_id: userId, role: 1 }),
  generateTasks:    (id)            => api.post(`/timelines/${id}/generate-tasks`, {}),
  batchCreateTasks: (id, tasks)     => api.post(`/timelines/${id}/batch-create-tasks`, { tasks }),
  getComments:      (taskId)        => api.get(`/timelines/tasks/${taskId}/comments`),
  getFiles:         (taskId)        => api.get(`/timelines/tasks/${taskId}/files`),
  addComment:       (taskId, content) => api.post(`/timelines/tasks/${taskId}/comments`, { task_message: content }),
  getMembers:       (id)               => api.get(`/timelines/${id}/members`),
  removeMember:     (id, userId)       => api.delete(`/timelines/${id}/members/${userId}`),
};
