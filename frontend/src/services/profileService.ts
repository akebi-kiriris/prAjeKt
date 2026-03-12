import api from './api';
import type { AxiosResponse } from 'axios';
import type { Profile, ChartStats } from '../types';

export const profileService = {
  getMe:         (): Promise<AxiosResponse<Profile>>          => api.get('/profile/me'),
  update:        (data: Partial<Profile>): Promise<AxiosResponse<Profile>> => api.put('/profile/me', data),
  getChartStats: (): Promise<AxiosResponse<ChartStats>>       => api.get('/profile/chart-stats'),
};
