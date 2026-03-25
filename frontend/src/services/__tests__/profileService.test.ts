import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../api', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}));

import api from '../api';
import { profileService } from '../profileService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('profileService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map profile endpoints correctly', () => {
    profileService.getMe();
    profileService.update({ name: 'N' } as never);
    profileService.getChartStats();

    expect(mockedApi.get).toHaveBeenCalledWith('/profile/me');
    expect(mockedApi.put).toHaveBeenCalledWith('/profile/me', { name: 'N' });
    expect(mockedApi.get).toHaveBeenCalledWith('/profile/chart-stats');
  });
});
