import api from './api';

export const groupService = {
  getAll: () => api.get('/groups'),
  create: (name) => api.post('/groups', { group_name: name }),
  join: (inviteCode) => api.post('/groups/join', { invite_code: inviteCode }),
  leave: (groupId) => api.post(`/groups/${groupId}/leave`),
  getMessages: (groupId) => api.get(`/groups/${groupId}/messages`),
  sendMessage: (groupId, content) => api.post(`/groups/${groupId}/messages`, { content }),
};
