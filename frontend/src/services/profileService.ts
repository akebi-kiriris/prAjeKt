import api from './api';
import type { AxiosResponse } from 'axios';
import type { ApiMutationResponse, Profile, ProfileUpdatePayload, ChartStats } from '../types';

export const profileService = {
  getMe:         (): Promise<AxiosResponse<Profile>>          => api.get('/profile/me'),
  update:        (data: ProfileUpdatePayload): Promise<AxiosResponse<ApiMutationResponse>> => api.put('/profile/me', data),
  getChartStats: (): Promise<AxiosResponse<ChartStats>>       => api.get('/profile/chart-stats'),
};
