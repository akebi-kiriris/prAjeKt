import api from './api';

export const trashService = {
  getAll:                  ()   => api.get('/trash'),
  restoreTask:             (id) => api.patch(`/trash/tasks/${id}/restore`),
  permanentDeleteTask:     (id) => api.delete(`/trash/tasks/${id}`),
  restoreTimeline:         (id) => api.patch(`/trash/timelines/${id}/restore`),
  permanentDeleteTimeline: (id) => api.delete(`/trash/timelines/${id}`),
};
