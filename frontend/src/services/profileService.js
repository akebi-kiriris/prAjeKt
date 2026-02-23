import api from './api';

export const profileService = {
  getMe: () => api.get('/profile/me'),
  update: (data) => api.put('/profile/me', data),
};
