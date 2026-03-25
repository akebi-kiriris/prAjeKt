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
import { trashService } from '../trashService';

const mockedApi = api as unknown as {
  get: ReturnType<typeof vi.fn>;
  post: ReturnType<typeof vi.fn>;
  put: ReturnType<typeof vi.fn>;
  patch: ReturnType<typeof vi.fn>;
  delete: ReturnType<typeof vi.fn>;
};

describe('trashService', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should map trash endpoints correctly', () => {
    trashService.getAll();
    trashService.restoreTask(1);
    trashService.permanentDeleteTask(1);
    trashService.restoreTimeline(2);
    trashService.permanentDeleteTimeline(2);

    expect(mockedApi.get).toHaveBeenCalledWith('/trash');
    expect(mockedApi.patch).toHaveBeenCalledWith('/trash/tasks/1/restore');
    expect(mockedApi.delete).toHaveBeenCalledWith('/trash/tasks/1');
    expect(mockedApi.patch).toHaveBeenCalledWith('/trash/timelines/2/restore');
    expect(mockedApi.delete).toHaveBeenCalledWith('/trash/timelines/2');
  });
});
