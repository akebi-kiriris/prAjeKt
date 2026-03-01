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
  // 成員管理
  getMembers:    (id)                  => api.get(`/tasks/${id}/members`),
  addMember:     (id, userId)          => api.post(`/tasks/${id}/members`, { user_id: userId }),
  removeMember:  (taskId, userId)      => api.delete(`/tasks/${taskId}/members/${userId}`),
  searchUser:    (email)               => api.post('/timelines/search_user', { email }),
  // 留言
  getComments:   (id)                  => api.get(`/tasks/${id}/comments`),
  addComment:    (id, msg)             => api.post(`/tasks/${id}/comments`, { task_message: msg }),
  deleteComment: (taskId, cid)         => api.delete(`/tasks/${taskId}/comments/${cid}`),
  // 附件
  getFiles:      (id)                  => api.get(`/tasks/${id}/files`),
  uploadFile:    (id, formData)        => api.post(`/tasks/${id}/upload`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  deleteFile:    (taskId, fileId)      => api.delete(`/tasks/${taskId}/files/${fileId}`),
};
